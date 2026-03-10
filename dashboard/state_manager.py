import json
from pathlib import Path

GUI_STATE_FILE = Path("data/gui_state.json")

def load_gui_state() -> dict:
    if not GUI_STATE_FILE.exists():
        return {}
    try:
        with open(GUI_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_gui_state(state: dict):
    try:
        GUI_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(GUI_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
    except IOError:
        pass
