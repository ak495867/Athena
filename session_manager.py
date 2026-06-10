import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any

SESSIONS_DIR = "sessions"

class SessionManager:
    """Manages research session persistence and discovery."""
    def __init__(self):
        if not os.path.exists(SESSIONS_DIR):
            os.makedirs(SESSIONS_DIR)

    def save_session(self, session_id: str, topic: str, state: Dict[str, Any], messages: List[Dict[str, Any]]):
        filename = f"{session_id}.json"
        filepath = os.path.join(SESSIONS_DIR, filename)
        data = {
            "session_id": session_id,
            "topic": topic,
            "last_updated": datetime.now().isoformat(),
            "state": state,
            "messages": messages
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def list_recent_sessions(self) -> List[Dict[str, str]]:
        """Discover sessions and return human-readable topics and IDs."""
        sessions = []
        for f in os.listdir(SESSIONS_DIR):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(SESSIONS_DIR, f), 'r') as f_in:
                        data = json.load(f_in)
                        sessions.append({
                            "id": data["session_id"],
                            "topic": data["topic"],
                            "date": data["last_updated"]
                        })
                except: continue
        # Sort by most recent
        return sorted(sessions, key=lambda x: x["date"], reverse=True)

    def load_session(self, session_id: str) -> Dict[str, Any]:
        filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None

SESSION_MANAGER = SessionManager()
