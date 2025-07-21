import re
from collections import defaultdict


def parse_payload(payload: str) -> dict:
    """
    Prend un payload QRadar brut (texte), et le transforme en dictionnaire structuré.
    - Gère les clés multiples (stocke en liste si dupliquées)
    - Gère les champs sans valeur (valeur None)
    - Gère les champs sans égal (stocke dans '_unparsed')
    - Gère les valeurs multi-mots
    - Gère les champs en début de ligne (avant le premier espace)
    """
    parsed = defaultdict(list)
    unparsed = []

    # Découpage en tokens par espace, mais en respectant les valeurs multi-mots après =
    # Ex: key1=val1 key2=val2 multi mots key3=val3
    # => key2: 'val2 multi mots'
    tokens = re.findall(r'\S+=\S+|\S+=|\S+', payload)
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if '=' in token:
            key, sep, value = token.partition('=')
            # Si la valeur est vide, on regarde si le token suivant n'est pas une clé
            if value == '' and i + 1 < len(tokens) and '=' not in tokens[i + 1]:
                value = tokens[i + 1]
                i += 1
            # Si la valeur semble s'étendre sur plusieurs tokens (pas de clé suivante)
            while i + 1 < len(tokens) and '=' not in tokens[i + 1]:
                value += ' ' + tokens[i + 1]
                i += 1
            value = value.strip() if value else None
            parsed[key.strip()].append(value)
        else:
            # Token sans égal, on le stocke à part
            unparsed.append(token)
        i += 1

    # Convertir en dictionnaire simple : si une clé a une seule valeur, on la déplie
    final_result = {}
    for k, v in parsed.items():
        if len(v) == 1:
            final_result[k] = v[0]
        else:
            final_result[k] = v  # on garde toutes les valeurs si plusieurs
    if unparsed:
        final_result['_unparsed'] = unparsed
    return final_result


def extract_critical_fields(parsed_payload: dict) -> dict:
    """
    Filtre et extrait les champs critiques pour l’analyse humaine rapide.
    Par exemple : EventID, SourceIP, DestinationIP, User, DeviceTime, etc.
    """
    keys_to_extract = [
        "EventID", "EventIDCode", "SourceIP", "DestinationIP", "Username",
        "User", "Domain", "DeviceTime", "LogSource", "Computer", "OriginatingComputer", "Message"
    ]
    filtered = {}
    for key in keys_to_extract:
        if key in parsed_payload:
            filtered[key] = parsed_payload[key]
        else:
            filtered[key] = None
    return filtered


# --- Test rapide du parseur ---
if __name__ == "__main__":
    example = """
<13>Jul 18 15:04:23 CORELIA-INT_SPSFRT AgentDevice=WindowsLog AgentLogFile=Security PluginVersion=7.3.1.22 Source=Microsoft-Windows-Security-Auditing Computer=SPSFRT.GROUPEDFI.FR OriginatingComputer=10.10.10.189 User= Domain= EventID=4672 EventIDCode=4672 EventType=8 EventCategory=12548 RecordNumber=3235305379 TimeGenerated=1752843861 TimeWritten=1752843861 Level=Log Always Keywords=Audit Success Task=SE_ADT_LOGON_SPECIALLOGON Opcode=Info Message=Privilèges spéciaux attribués à la nouvelle ouverture de session. Sujet : ID de sécurité : GROUPEDFI\\sp_portalapppool Nom du compte : sp_portalapppool Domaine du compte : GROUPEDFI ID d’ouverture de session : 0x3696b986 Privilèges : SeAssignPrimaryTokenPrivilege SeImpersonatePrivilege
"""
    parsed = parse_payload(example)
    print("--- PARSED ---")
    for k, v in parsed.items():
        print(f"{k}: {v}")
    print("\n--- SYNTHÈSE ---")
    synth = extract_critical_fields(parsed)
    for k, v in synth.items():
        print(f"{k}: {v}")
