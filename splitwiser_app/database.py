# database.py
import json
from pathlib import Path
from typing import Dict

DB_FILE = Path("app_database.json")

def load_db() -> Dict[str, Dict]:
    """Loads the database, initializing with 'users' and 'groups' keys if empty."""
    if not DB_FILE.exists():
        return {"users": {}, "groups": {}}
    with DB_FILE.open("r") as f:
        try:
            data = json.load(f)
            if "users" not in data: data["users"] = {}
            if "groups" not in data: data["groups"] = {}
            return data
        except json.JSONDecodeError:
            return {"users": {}, "groups": {}}

def save_db(data: Dict[str, Dict]):
    """Saves the provided dictionary to the JSON database file."""
    with DB_FILE.open("w") as f:
        json.dump(data, f, indent=4)