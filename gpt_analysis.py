import os
import requests
import json
import logging
from typing import Dict, Any, Optional

# Configuration du logging
logger = logging.getLogger(__name__)

def analyze_payload_with_gpt(payload_dict: Dict[str, Any], api_key: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyse un payload avec GPT via l'API OpenAI ou un service local
    
    Args:
        payload_dict: Dictionnaire contenant les données du payload
        api_key: Clé API pour le service GPT
        custom_prompt: Prompt personnalisé optionnel
    
    Returns:
        Dict contenant l'analyse et les métadonnées
    """
    try:
        print(f"🤖 [GPT_ANALYSIS] Début de l'analyse GPT")
        print(f"📊 [GPT_ANALYSIS] Type de payload: {type(payload_dict)}")
        print(f"🔑 [GPT_ANALYSIS] Clé API fournie: {'Oui' if api_key else 'Non'}")
        print(f"🎯 [GPT_ANALYSIS] Prompt personnalisé: {'Oui' if custom_prompt else 'Non'}")
        logger.info("🔍 Début de l'analyse GPT du payload")
        
        # Préparer le payload pour l'analyse
        payload_text = str(payload_dict)
        
        # Prompt par défaut pour l'analyse de sécurité
        default_prompt = """
Tu es un expert en cybersécurité spécialisé dans l'analyse de logs QRadar.

IMPORTANT: Réponds UNIQUEMENT en français. Ne jamais utiliser l'espagnol ou l'anglais.

Payload à analyser:
{payload}

Fournis une analyse structurée et détaillée en français incluant:
1. Type de menace détectée
2. Niveau de risque (Faible/Moyen/Élevé/Critique)
3. Recommandations de réponse immédiate
4. Indicateurs techniques (IOC)
5. Actions de remédiation

Analyse complète (en français uniquement):
"""
        
        # Utiliser le prompt personnalisé ou le prompt par défaut
        prompt = custom_prompt if custom_prompt else default_prompt.format(payload=payload_text)
        
        # Configuration de la requête
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un expert en cybersécurité spécialisé dans l'analyse de logs QRadar. Réponds toujours en français."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        # Appel à l'API OpenAI
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result["choices"][0]["message"]["content"]
            
            print(f"✅ [GPT_ANALYSIS] Analyse GPT réussie")
            print(f"📝 [GPT_ANALYSIS] Longueur de l'analyse: {len(analysis)} caractères")
            print(f"🎯 [GPT_ANALYSIS] Modèle utilisé: gpt-3.5-turbo")
            print(f"🔢 [GPT_ANALYSIS] Tokens utilisés: {result.get('usage', {}).get('total_tokens', 0)}")
            
            logger.info("✅ Analyse GPT réussie")
            
            return {
                "success": True,
                "analysis": analysis,
                "model": "gpt-3.5-turbo",
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "timestamp": result.get("created", "")
            }
        else:
            print(f"❌ [GPT_ANALYSIS] Erreur API GPT: {response.status_code}")
            print(f"📄 [GPT_ANALYSIS] Réponse: {response.text[:200]}...")
            logger.error(f"❌ Erreur API GPT: {response.status_code}")
            return {
                "success": False,
                "error": f"Erreur API: {response.status_code}",
                "analysis": "Erreur lors de l'analyse GPT"
            }
            
    except requests.exceptions.Timeout:
        print(f"⏰ [GPT_ANALYSIS] Timeout lors de l'appel GPT")
        logger.error("⏰ Timeout lors de l'appel GPT")
        return {
            "success": False,
            "error": "Timeout",
            "analysis": "Timeout lors de l'analyse GPT"
        }
    except requests.exceptions.ConnectionError as e:
        print(f"❌ [GPT_ANALYSIS] Erreur de connexion GPT: {e}")
        logger.error(f"❌ Erreur de connexion GPT: {e}")
        return {
            "success": False,
            "error": f"Erreur de connexion: {str(e)}",
            "analysis": "Erreur de connexion lors de l'analyse GPT"
        }
    except Exception as e:
        print(f"❌ [GPT_ANALYSIS] Erreur inattendue GPT: {e}")
        logger.error(f"❌ Erreur inattendue GPT: {e}")
        return {
            "success": False,
            "error": f"Erreur inattendue: {str(e)}",
            "analysis": "Erreur inattendue lors de l'analyse GPT"
        }

def generate_short_summary(text: str, api_key: str, max_length: int = 200) -> str:
    """
    Génère un résumé court d'un texte avec GPT
    
    Args:
        text: Texte à résumer
        api_key: Clé API pour le service GPT
        max_length: Longueur maximale du résumé
    
    Returns:
        Résumé du texte
    """
    try:
        logger.info("📝 Génération du résumé GPT")
        
        prompt = f"""
Résume ce texte en français en maximum {max_length} caractères:

{text}

Résumé:
"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un expert en résumé. Réponds toujours en français de manière concise."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result["choices"][0]["message"]["content"].strip()
            
            logger.info("✅ Résumé GPT généré")
            return summary
        else:
            logger.error(f"❌ Erreur génération résumé: {response.status_code}")
            return text[:max_length] + "..." if len(text) > max_length else text
            
    except Exception as e:
        logger.error(f"❌ Erreur résumé GPT: {e}")
        return text[:max_length] + "..." if len(text) > max_length else text

def test_gpt_connection(api_key: str) -> bool:
    """
    Teste la connexion à l'API GPT
    
    Args:
        api_key: Clé API pour le service GPT
    
    Returns:
        True si la connexion fonctionne, False sinon
    """
    try:
        logger.info("🧪 Test de connexion GPT")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": "Test de connexion - réponds 'OK'"
                }
            ],
            "max_tokens": 10
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Connexion GPT OK")
            return True
        else:
            logger.error(f"❌ Erreur connexion GPT: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test connexion GPT: {e}")
        return False 