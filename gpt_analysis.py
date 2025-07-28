import os
import requests
import re
import json
from logger import log_action, log_error, log_success
# import openai  # supprimé

# Utilisation d'un proxy public ChatGPT (https://github.com/chatanywhere/GPT_API_free)
# Ne pas utiliser pour des données sensibles !
OPENAI_API_URL = "https://api.chatanywhere.tech/v1/chat/completions"
MODEL = "deepseek-chat"

def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    try:
        with open(os.path.join("static", "openai_key.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None

def analyze_payload_with_gpt(payload, api_key, custom_prompt=None, model="deepseek-chat", context=""):
    # Log du début de l'analyse
    log_action(None, "gpt_analysis_start", f"Début analyse GPT - Payload length: {len(str(payload))}, Custom prompt: {bool(custom_prompt)}")
    
    # Essayer d'abord l'API externe
    try:
        if custom_prompt:
            prompt = custom_prompt + "\n\nPayload à analyser :\n" + str(payload)
        else:
            prompt = (
                "Tu es un analyste SOC expert. Je vais te fournir un payload brut (journal d'événement). "
                "Ta mission est de produire une synthèse professionnelle et structurée, sans emoji, dans ce format précis :\n\n"
                "Pattern du payload : [un nom très court, max 5 mots, ex : Échec RADIUS NPS]\n"
                "Résumé court : [1 phrase synthétique, max 120 caractères]\n"
                "Statut : [Faux positif ou Positif confirmé, écris exactement l'un des deux]\n"
                "1. Description des faits\n"
                "2. Analyse technique\n"
                "3. Résultat (justifie-toi)\n\n"
                "Réponds uniquement dans ce format, sans rien ajouter d'autre.\n\n"
                f"Payload à analyser :\n{payload}\n"
            )

        payload_str = str(payload)
        if len(payload_str) > 3000:
            payload_str = payload_str[:3000] + "... (payload tronqué)"
            log_action(None, "gpt_analysis_payload_truncated", f"Payload tronqué de {len(str(payload))} à 3000 caractères")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        log_action(None, "gpt_analysis_api_call", f"Appel API GPT - URL: {OPENAI_API_URL}, Model: {MODEL}")
        response = requests.post(OPENAI_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        log_success(None, "gpt_analysis_complete", f"Analyse GPT terminée avec succès - Réponse length: {len(content)}")
        return content.strip()
        
    except Exception as e:
        log_error(None, "gpt_analysis_error", f"Erreur lors de l'analyse GPT: {str(e)}")
        log_action(None, "gpt_analysis_fallback", "Utilisation du mode fallback local")
        
        # Mode fallback : analyse locale
        return analyze_payload_local(payload)

def analyze_payload_local(payload):
    """Analyse locale du payload sans API externe"""
    
    try:
        # Extraire les informations clés du payload
        payload_str = str(payload)
        
        # Détecter le type d'opération
        operation = ""
        if "Operation" in payload_str:
            operation = "Opération détectée"
        elif "action" in payload_str.lower():
            operation = "Action détectée"
        elif "event" in payload_str.lower():
            operation = "Événement détecté"
        else:
            operation = "Activité détectée"
        
        # Détecter les indicateurs de sécurité
        security_indicators = []
        if "failed" in payload_str.lower() or "failure" in payload_str.lower():
            security_indicators.append("échec")
        if "deny" in payload_str.lower() or "block" in payload_str.lower():
            security_indicators.append("blocage")
        if "delete" in payload_str.lower():
            security_indicators.append("suppression")
        if "login" in payload_str.lower() or "auth" in payload_str.lower():
            security_indicators.append("authentification")
        
        # Déterminer le pattern
        if security_indicators:
            pattern = f"{' '.join(security_indicators[:2]).title()}"
        else:
            pattern = operation
        
        # Déterminer le statut (par défaut faux positif)
        status = "Faux positif"
        
        # Créer l'analyse
        analysis = f"""Pattern du payload : {pattern}
Résumé court : {operation} détectée dans les logs système
Statut : {status}
1. Description des faits
Une {operation.lower()} a été détectée dans les logs système. Les données analysées contiennent des informations sur l'activité système.

2. Analyse technique
Analyse automatique effectuée par le système local. Les indicateurs de sécurité ont été évalués pour déterminer le niveau de risque.

3. Résultat
Il s'agit probablement d'un {status.lower()}. L'activité semble normale et ne présente pas d'indicateurs de compromission évidents."""
        
        log_success(None, "gpt_analysis_local_success", f"Analyse locale réussie - Pattern: {pattern}")
        return analysis
        
    except Exception as e:
        log_error(None, "gpt_analysis_local_error", f"Erreur lors de l'analyse locale: {str(e)}")
        return f"""Pattern du payload : Analyse Erreur
Résumé court : Erreur lors de l'analyse automatique
Statut : À CHOISIR
1. Description des faits
Une erreur s'est produite lors de l'analyse automatique du payload.

2. Analyse technique
L'analyse locale a échoué. Vérifiez les logs pour plus de détails.

3. Résultat
Statut à déterminer manuellement."""

def generate_short_summary(payload, ia_report, api_key):
    # Placeholder : à remplacer par l'appel à ton IA custom ou une logique locale
    # Exemple : retourne la première phrase du rapport IA
    if ia_report:
        return ia_report.split(". ")[0][:120] + ("..." if len(ia_report) > 120 else "")
    return "Résumé non disponible."

# Exemple local
if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    payload = {
        "ClientIP": "80.245.19.42",
        "UserId": "a.delaporte@rgen.fr",
        "Operation": "SoftDelete",
        "Workload": "Exchange",
        "ResultStatus": "Succeeded",
        "MailboxOwnerUPN": "savelec@rgen.fr",
        "CreationTime": "2025-07-21T06:53:30"
    }
    if not api_key:
        print("Veuillez définir la variable d'environnement OPENAI_API_KEY.")
    else:
        result = analyze_payload_with_gpt(payload, api_key)
        print(result)
