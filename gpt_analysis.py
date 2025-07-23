import os
import requests
import re
import json
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
    if custom_prompt:
        prompt = custom_prompt + "\n\nPayload à analyser :\n" + str(payload)
    else:
        prompt = (
            "Tu es un analyste SOC expert. Je vais te fournir un payload brut (journal d'événement). "
            "Ta mission est de produire une synthèse professionnelle et structurée, sans emoji, dans ce format précis :\n\n"
            "Pattern du payload : [un nom très court, max 5 mots, ex : Échec RADIUS NPS]\n"
            "Résumé court : [1 phrase synthétique, max 120 caractères]\n"
            "1. Description des faits\n"
            "2. Analyse technique\n"
            "3. Résultat (Faux positif ou Positif confirmé, justifie-toi)\n\n"
            "Réponds uniquement dans ce format, sans rien ajouter d’autre.\n\n"
            f"Payload à analyser :\n{payload}\n"
        )

    payload_str = str(payload)
    if len(payload_str) > 3000:
        payload_str = payload_str[:3000] + "... (payload tronqué)"
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
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return content.strip()
    except Exception as e:
        return f"[ERREUR] {str(e)}"

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
