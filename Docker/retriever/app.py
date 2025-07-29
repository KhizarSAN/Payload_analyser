import os
import hashlib
import sqlite3
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chromadb import Client
from sentence_transformers import SentenceTransformer
import requests
from sqlalchemy import create_engine, text
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mistral Retriever API", version="1.0.0")

# Configuration des variables d'environnement
TGI_URL = os.getenv("TGI_URL", "http://tgi:80")
CHROMA_URL = os.getenv("CHROMA_URL", "http://chromadb:8000")
DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "payload_analyser")

# Initialisation de ChromaDB
try:
    chroma = Client(api_url=CHROMA_URL)
    collection = chroma.get_or_create_collection("mistral_analyses")
    logger.info("✅ ChromaDB connecté avec succès")
except Exception as e:
    logger.error(f"❌ Erreur connexion ChromaDB: {e}")
    chroma = None
    collection = None

# Initialisation du modèle d'embeddings
try:
    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    logger.info("✅ Modèle d'embeddings chargé")
except Exception as e:
    logger.error(f"❌ Erreur chargement embeddings: {e}")
    embedder = None

# Connexion MySQL
try:
    mysql_engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
    logger.info("✅ MySQL connecté avec succès")
except Exception as e:
    logger.error(f"❌ Erreur connexion MySQL: {e}")
    mysql_engine = None

# SQLite pour métadonnées locales
DB_PATH = "/data/embeddings.db"
try:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS meta (
        id TEXT PRIMARY KEY, 
        payload TEXT, 
        analysis TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    logger.info("✅ SQLite local initialisé")
except Exception as e:
    logger.error(f"❌ Erreur SQLite: {e}")
    conn = None

class PayloadRequest(BaseModel):
    payload: str

class AnalysisResponse(BaseModel):
    analysis: str
    context_count: int
    payload_hash: str
    similar_analyses: Optional[List[dict]] = None

@app.get("/health")
def health():
    """Endpoint de santé du service"""
    status = {
        "status": "healthy",
        "service": "mistral_retriever",
        "tgi_url": TGI_URL,
        "chroma_url": CHROMA_URL,
        "mysql_connected": mysql_engine is not None,
        "chroma_connected": chroma is not None,
        "embedder_loaded": embedder is not None
    }
    return status

@app.post("/analyze", response_model=AnalysisResponse)
def analyze(payload_req: PayloadRequest):
    """Analyse un payload avec RAG et apprentissage"""
    if not payload_req.payload:
        raise HTTPException(400, "Payload requis")
    
    payload = payload_req.payload
    logger.info(f"🔍 Analyse demandée pour payload: {payload[:100]}...")
    
    try:
        # 1) Récupérer contexte via ChromaDB
        context = ""
        similar_analyses = []
        
        if embedder and collection:
            try:
                q_emb = embedder.encode(payload).tolist()
                results = collection.query(
                    query_embeddings=[q_emb], 
                    n_results=3,
                    include=["metadatas", "documents"]
                )
                
                if results["metadatas"] and results["metadatas"][0]:
                    context = "\n\nContexte historique:\n"
                    for i, metadata in enumerate(results["metadatas"][0], 1):
                        if metadata:
                            context += f"\n{i}. Payload: {metadata.get('payload', '')[:200]}...\n"
                            context += f"   Analyse: {metadata.get('analysis', '')[:300]}...\n"
                            similar_analyses.append({
                                "payload": metadata.get('payload', '')[:200],
                                "analysis": metadata.get('analysis', '')[:300]
                            })
                
                logger.info(f"📚 {len(similar_analyses)} analyses similaires trouvées")
            except Exception as e:
                logger.warning(f"⚠️ Erreur récupération contexte: {e}")
        
        # 2) Générer prompt avec contexte
        prompt = f"""
Tu es un expert en cybersécurité spécialisé dans l'analyse de logs QRadar.

Payload à analyser:
{payload}

{context}

Fournis une analyse structurée et détaillée incluant:
1. Type de menace détectée
2. Niveau de risque (Faible/Moyen/Élevé/Critique)
3. Recommandations de réponse immédiate
4. Indicateurs techniques (IOC)
5. Actions de remédiation

Analyse complète:
"""
        
        # 3) Appeler TGI Mistral
        logger.info("🤖 Appel à TGI Mistral...")
        response = requests.post(
            f"{TGI_URL}/generate",
            json={
                "prompt": prompt,
                "max_new_tokens": 512,
                "temperature": 0.7,
                "do_sample": True
            },
            timeout=120
        )
        
        if response.status_code != 200:
            logger.error(f"❌ Erreur TGI: {response.status_code}")
            raise HTTPException(500, f"Erreur TGI Mistral: {response.status_code}")
        
        analysis = response.json().get("generated_text", "")
        if not analysis:
            analysis = "Erreur: Aucune réponse générée par Mistral"
        
        logger.info("✅ Analyse générée avec succès")
        
        # 4) Stocker dans MySQL
        if mysql_engine:
            try:
                with mysql_engine.connect() as connection:
                    connection.execute(text("""
                        INSERT INTO analyses (payload, resultat, type_analyse, date_analyse)
                        VALUES (:payload, :resultat, :type_analyse, NOW())
                    """), {
                        "payload": payload,
                        "resultat": analysis,
                        "type_analyse": "mistral_rag"
                    })
                    connection.commit()
                logger.info("💾 Analyse sauvegardée en MySQL")
            except Exception as e:
                logger.error(f"❌ Erreur sauvegarde MySQL: {e}")
        
        # 5) Stocker metadata + embedding
        payload_hash = hashlib.md5(payload.encode()).hexdigest()
        
        if conn:
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO meta (id, payload, analysis) VALUES (?, ?, ?)",
                    (payload_hash, payload, analysis)
                )
                conn.commit()
                logger.info("💾 Métadonnées sauvegardées en SQLite")
            except Exception as e:
                logger.error(f"❌ Erreur SQLite: {e}")
        
        # 6) Stocker embedding dans ChromaDB
        if embedder and collection:
            try:
                emb = embedder.encode(payload).tolist()
                collection.upsert(
                    ids=[payload_hash],
                    embeddings=[emb],
                    metadatas=[{
                        "payload": payload,
                        "analysis": analysis,
                        "type": "qradar_payload"
                    }]
                )
                logger.info("💾 Embedding stocké dans ChromaDB")
            except Exception as e:
                logger.error(f"❌ Erreur ChromaDB: {e}")
        
        return AnalysisResponse(
            analysis=analysis,
            context_count=len(similar_analyses),
            payload_hash=payload_hash,
            similar_analyses=similar_analyses
        )
        
    except requests.exceptions.Timeout:
        logger.error("⏰ Timeout TGI Mistral")
        raise HTTPException(504, "Timeout - Service Mistral non disponible")
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {e}")
        raise HTTPException(500, f"Erreur inattendue: {str(e)}")

@app.get("/stats")
def stats():
    """Statistiques du service"""
    try:
        # Statistiques SQLite
        sqlite_count = 0
        if conn:
            cursor = conn.execute("SELECT COUNT(*) FROM meta")
            sqlite_count = cursor.fetchone()[0]
        
        # Statistiques MySQL
        mysql_count = 0
        if mysql_engine:
            with mysql_engine.connect() as connection:
                result = connection.execute(text("SELECT COUNT(*) FROM analyses WHERE type_analyse = 'mistral_rag'"))
                mysql_count = result.fetchone()[0]
        
        # Statistiques ChromaDB
        chroma_count = 0
        if collection:
            try:
                chroma_count = collection.count()
            except:
                pass
        
        return {
            "total_embeddings_sqlite": sqlite_count,
            "total_analyses_mysql": mysql_count,
            "total_embeddings_chroma": chroma_count,
            "service": "mistral_retriever",
            "status": "healthy"
        }
    except Exception as e:
        logger.error(f"❌ Erreur stats: {e}")
        return {"error": str(e)}

@app.get("/learn")
def trigger_learning():
    """Déclenche l'apprentissage sur les données existantes"""
    try:
        # Ici on pourrait ajouter une logique d'apprentissage plus avancée
        # Par exemple, réentraîner les embeddings ou optimiser les prompts
        logger.info("🧠 Apprentissage déclenché")
        return {"status": "learning_triggered", "message": "Apprentissage en cours"}
    except Exception as e:
        logger.error(f"❌ Erreur apprentissage: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000) 