import json
import os
from datetime import datetime

DATA_DIR = 'patterns_data'
CENTRAL_FILE = os.path.join(DATA_DIR, 'patterns.json')

os.makedirs(DATA_DIR, exist_ok=True)

def load_data():
    if not os.path.exists(CENTRAL_FILE):
        return []
    with open(CENTRAL_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_data(data):
    with open(CENTRAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_analysis(entry):
    data = load_data()
    entry['date'] = datetime.now().isoformat()
    pattern = entry.get('pattern')
    feedback = entry.get('feedback')
    feedback_comment = entry.get('feedback_comment', '')
    feedback_type = entry.get('feedback_type', feedback or '')
    feedback_author = entry.get('feedback_author', '')
    feedback_obj = None
    if feedback_type or feedback_comment:
        feedback_obj = {
            'date': entry['date'],
            'type': feedback_type,
            'comment': feedback_comment,
            'author': feedback_author
        }
    found = False
    for i, e in enumerate(data):
        if e.get('pattern') == pattern:
            # Mettre à jour l'entrée existante
            # Mettre à jour les champs principaux
            for k in ['input', 'pattern', 'result', 'analyse_technique', 'tags', 'status']:
                if k in entry:
                    e[k] = entry[k]
            # Ajouter le feedback à l'historique
            if feedback_obj:
                if 'feedbacks' not in e:
                    e['feedbacks'] = []
                e['feedbacks'].append(feedback_obj)
            e['date'] = entry['date']
            data[i] = e
            found = True
            break
    if not found:
        # Nouvelle entrée
        new_entry = {k: entry.get(k, '') for k in ['input', 'pattern', 'result', 'analyse_technique', 'tags', 'status']}
        new_entry['date'] = entry['date']
        new_entry['feedbacks'] = [feedback_obj] if feedback_obj else []
        data.append(new_entry)
    save_data(data)

def find_existing_pattern(pattern):
    data = load_data()
    for entry in data:
        if entry.get('pattern') == pattern:
            return entry
    return None

def get_all_patterns():
    data = load_data()
    return [entry.get('pattern') for entry in data if 'pattern' in entry] 