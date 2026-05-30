import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'memory_bank.json')

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"used_concepts": []}
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading memory bank: {e}")
        return {"used_concepts": []}

def save_memory(memory_data):
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory_data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving memory bank: {e}")

def is_concept_used(video_id):
    memory = load_memory()
    for concept in memory.get('used_concepts', []):
        if concept.get('video_id') == video_id:
            return True
    return False

def log_concept(video_id, title, url):
    memory = load_memory()
    # Avoid duplicate logging just in case
    if not is_concept_used(video_id):
        memory.setdefault('used_concepts', []).append({
            'video_id': video_id,
            'title': title,
            'url': url,
            'date_used': datetime.now().isoformat()
        })
        save_memory(memory)
