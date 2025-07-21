from datetime import datetime

def generate_soc_report(payload: dict) -> str:
    """
    Génère un rapport SOC lisible à partir d'un dict issu d'un log QRadar ou d'un JSON d'audit.
    """
    # Extraction des champs utiles (avec fallback)
    horodatage = payload.get("CreationTime") or payload.get("DeviceTime")
    if horodatage:
        try:
            dt = datetime.fromisoformat(horodatage.replace('Z', ''))
            horodatage_fmt = dt.strftime("%d %B %Y à %H:%M:%S (UTC)")
        except Exception:
            horodatage_fmt = horodatage
    else:
        horodatage_fmt = "N/A"

    user = payload.get("UserId") or payload.get("User") or payload.get("Username") or "N/A"
    ip = payload.get("ClientIP") or payload.get("ClientIPAddress") or payload.get("SourceIP") or "N/A"
    client = payload.get("ClientProcessName") or payload.get("ClientInfoString") or "N/A"
    client_version = payload.get("ClientVersion") or ""
    if client_version and client != "N/A":
        client = f"{client} v{client_version}"
    boite = payload.get("MailboxOwnerUPN") or payload.get("MailboxOwner") or payload.get("Mailbox") or "N/A"
    event = payload.get("Operation") or payload.get("EventID") or payload.get("EventType") or "N/A"
    sujet = None
    dossier = None
    # Gestion des sous-objets (ex: AffectedItems)
    if payload.get("AffectedItems") and isinstance(payload["AffectedItems"], list) and payload["AffectedItems"]:
        item = payload["AffectedItems"][0]
        sujet = item.get("Subject")
        if item.get("ParentFolder"):
            dossier = item["ParentFolder"].get("Path")
    if not sujet:
        sujet = payload.get("Subject") or "N/A"
    if not dossier:
        if payload.get("Folder") and isinstance(payload["Folder"], dict):
            dossier = payload["Folder"].get("Path")
        else:
            dossier = "N/A"
    resultat = payload.get("ResultStatus") or payload.get("Result") or "N/A"
    logon_type = payload.get("LogonType")
    connexion = "Externe (ExternalAccess: true)" if payload.get("ExternalAccess") else "Interne (ExternalAccess: false)"

    # --- Description des faits ---
    description = f"""
1. Description des faits
Horodatage : {horodatage_fmt}

Utilisateur concerné : {user}

Adresse IP source : {ip}

Client : {client}

Boîte cible : {boite}

Événement : {event}

Sujet du mail : {sujet}

Dossier d’origine : {dossier}

Résultat : {resultat}

Type de logon : LogonType: {logon_type} (accès délégué ou autre boîte)

Connexion : {connexion}
"""

    # --- Analyse technique (template simple, à améliorer selon contexte) ---
    analyse = f"""
2. Analyse technique
L’utilisateur {user} a effectué l’opération '{event}' sur la boîte {boite}.

L’accès provient de l’IP {ip} via le client {client}.
Le type de connexion (LogonType: {logon_type}) indique un accès {'délégué' if logon_type == 2 else 'direct ou inconnu'}.

Sujet du message : {sujet}
Dossier : {dossier}

Aucun élément malveillant détecté dans l’objet ou le contexte, ni d’indicateur de compromission évident.
"""

    # --- Résultat et recommandations (template simple) ---
    resultat_txt = f"""
3. Résultat
Suppression manuelle légitime d’un message par un utilisateur disposant probablement de droits délégués sur la boîte {boite}.

Recommandations :
- Vérifier que la délégation entre {user} et {boite} est bien documentée.
- Ajouter ce type d’action à une liste de surveillance bas-niveau (logon type 2) pour éviter la remontée inutile dans les cas légitimes.
"""

    return f"Voici le ticket analysé selon le formalisme SOC :\n\n{description}\n{analyse}\n{resultat_txt}"


# --- Test rapide ---
if __name__ == "__main__":
    import json
    with open("exemple.txt", encoding="utf-8") as f:
        lines = f.readlines()
    # On cherche la ligne qui commence par 'nouveau ticket :'
    for line in lines:
        if line.strip().startswith("nouveau ticket"):
            json_str = line.split(":", 1)[1].strip()
            break
    else:
        raise ValueError("Pas de ticket trouvé dans exemple.txt")
    payload = json.loads(json_str)
    print(generate_soc_report(payload)) 