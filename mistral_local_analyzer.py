import requests

MISTRAL_API_URL = "http://localhost:5005/generate"  # À adapter selon ton VPS

def analyze_payload_with_mistral(payload: dict) -> str:
    """
    Envoie le payload à un serveur Mistral auto-hébergé pour une analyse SOC structurée.
    Retourne une réponse au format :
    1. Description des faits
    2. Analyse technique
    3. Résultat
    """
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

Ne donne aucun JSON, aucune balise, uniquement ce texte structuré.
    """.strip()

    data = {"prompt": prompt, "max_tokens": 800, "temperature": 0.2}
    try:
        response = requests.post(MISTRAL_API_URL, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        # Adapter selon la structure de réponse de ton serveur Mistral
        if isinstance(result, dict) and "text" in result:
            return result["text"].strip()
        elif isinstance(result, str):
            return result.strip()
        else:
            return str(result)
    except Exception as e:
        return f"[ERREUR MISTRAL] {str(e)}" 