import os
import requests
import re
import json

# Utilisation d'un proxy public ChatGPT (https://github.com/chatanywhere/GPT_API_free)
# Ne pas utiliser pour des données sensibles !
OPENAI_API_URL = "https://api.chatanywhere.tech/v1/chat/completions"
MODEL = "gpt-3.5-turbo"

def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    try:
        with open(os.path.join("static", "openai_key.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None

def analyze_payload_with_gpt(payload: dict, api_key: str = None) -> str:
    if api_key is None:
        api_key = get_openai_api_key()
    payload_str = str(payload)
    if len(payload_str) > 3000:
        payload_str = payload_str[:3000] + "... (payload tronqué)"
    prompt = f"""
Tu es un analyste SOC expert. Voici un log (payload) à analyser :

{payload_str}

Rédige une analyse SOC complète, exclusivement sous ce format clair :

1. Description des faits
(une description factuelle claire de l’événement)

2. Analyse technique
(une analyse technique compréhensible de l’impact et du contexte)

3. Résultat
(Faux positif ou Positif confirmé avec justification claire)

Ne donne aucun JSON ni balise, uniquement ce texte structuré.
"""
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
