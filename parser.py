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

    tokens = re.findall(r'\S+=\S+|\S+=|\S+', payload)
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if '=' in token:
            key, sep, value = token.partition('=')
            if value == '' and i + 1 < len(tokens) and '=' not in tokens[i + 1]:
                value = tokens[i + 1]
                i += 1
            while i + 1 < len(tokens) and '=' not in tokens[i + 1]:
                value += ' ' + tokens[i + 1]
                i += 1
            value = value.strip() if value else None
            parsed[key.strip()].append(value)
        else:
            unparsed.append(token)
        i += 1

    final_result = {}
    for k, v in parsed.items():
        if len(v) == 1:
            final_result[k] = v[0]
        else:
            final_result[k] = v
    if unparsed:
        final_result['_unparsed'] = unparsed
    return final_result


def extract_critical_fields(parsed_payload: dict) -> dict:
    """
    Retourne un dict avec tous les champs métiers connus (Exchange, firewall, générique),
    mais seules les valeurs présentes dans le payload sont non None.
    """
    def normalize_key(key):
        return re.sub(r'[^a-z0-9]', '', key.lower())
    norm_payload = {normalize_key(k): v for k, v in parsed_payload.items()}
    # Mapping métier (clé affichée -> variantes acceptées)
    mapping = {
        # Exchange/M365
        "Date": ["date", "creationtime"],
        "Heure": ["time", "creationtime"],
        "Utilisateur": ["userid", "user", "username", "account", "user_name", "user_id"],
        "IP Source": ["clientip", "clientipaddress", "sourceip", "srcip", "ip"],
        "Opération": ["operation", "eventid", "eventtype", "action"],
        "Workload": ["workload", "service", "system"],
        "Statut": ["resultstatus", "status"],
        "Client": ["clientprocessname", "clientinfostring"],
        "Boîte cible": ["mailboxownerupn", "mailboxowner", "mailbox"],
        "Dossier": ["folder", "parentfolder", "path"],
        "Sujet": ["subject"],
        # Firewall
        "Appareil": ["devname", "device", "computer", "hostname"],
        "ID Appareil": ["devid", "deviceid"],
        "Port Source": ["srcport", "sourceport"],
        "Interface Source": ["srcintf", "sourceinterface"],
        "IP Destination": ["dstip", "destinationip", "destip"],
        "Port Destination": ["dstport", "destinationport", "destport"],
        "Interface Destination": ["dstintf", "destinationinterface"],
        "Action": ["action"],
        "ID Politique": ["policyid"],
        "Type de Politique": ["policytype"],
        "Protocole": ["proto", "protocol"],
        "Niveau": ["level"],
        "Type": ["type"],
        "Sous-type": ["subtype"],
        "ID Session": ["sessionid"],
        "Durée": ["duration"],
        "Octets envoyés": ["sentbyte", "bytesent"],
        "Octets reçus": ["rcvdbyte", "byterecv"],
        "Paquets envoyés": ["sentpkt"],
        "Paquets reçus": ["rcvdpkt"],
        "Pays Source": ["srccountry"],
        "Pays Destination": ["dstcountry"],
        "VD": ["vd"],
        "Fuseau horaire": ["tz"],
        "ID Log": ["logid"],
        "Service": ["service"],
        "Disposition": ["trandisp"],
        "Type VPN": ["vpntype"],
        "Catégorie Application": ["appcat"],
        "Score CR": ["crscore"],
        "Action CR": ["craction"],
        "Niveau CR": ["crlevel"],
    }
    filtered = {}
    for label, variants in mapping.items():
        value = None
        for variant in variants:
            if variant in norm_payload and norm_payload[variant]:
                value = norm_payload[variant]
                break
        filtered[label] = value
    return filtered


def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f'{parent_key}{sep}{k}' if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f'{new_key}[{i}]', sep=sep).items())
                else:
                    items.append((f'{new_key}[{i}]', item))
        else:
            items.append((new_key, v))
    return dict(items)

# --- Test rapide du parseur ---
if __name__ == "__main__":
    example = """
<189>date=2025-07-21 time=08:33:44 devname="FGT3KDT418800255" devid="FGT3KDT418800255" eventtime=1753079624443273707 tz="+0200" logid="0000000013" type="traffic" subtype="forward" level="notice" vd="DFI_INTERNE" srcip=10.10.61.15 srcport=54706 srcintf="VPN-COR_RUNGIS" srcintfrole="undefined" dstip=192.168.30.206 dstport=443 dstintf="Corelia-Serveur" dstintfrole="lan" srccountry="Reserved" dstcountry="Reserved" sessionid=2608048636 proto=6 action="deny" policyid=0 policytype="policy" service="HTTPS" trandisp="noop" duration=0 sentbyte=0 rcvdbyte=0 sentpkt=0 rcvdpkt=0 vpntype="ipsecvpn" appcat="unscanned" crscore=30 craction=131072 crlevel="high"
"""
    parsed = parse_payload(example)
    print("--- PARSED ---")
    for k, v in parsed.items():
        print(f"{k}: {v}")
    print("\n--- SYNTHÈSE ---")
    synth = extract_critical_fields(parsed)
    for k, v in synth.items():
        print(f"{k}: {v}")
