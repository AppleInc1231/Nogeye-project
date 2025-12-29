import json
import os

# הגדרות נתיבים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
PSYCHE_PATH = os.path.join(DATA_DIR, "psyche.json")

class IdentityCore:
    """
    מודול אכיפת זהות וגבולות.
    בודק האם פעולות או בקשות תואמות את עקרונות הליבה של Nog.
    """
    def __init__(self):
        self.psyche = self._load_psyche()

    def _load_psyche(self):
        if not os.path.exists(PSYCHE_PATH):
            return {"boundaries": [], "core_values": []}
        try:
            with open(PSYCHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"boundaries": [], "core_values": []}

    def validate_action(self, user_text):
        """
        בודק אם הבקשה מפרה גבולות.
        Returns:
            (bool, str): (is_allowed, reason_if_denied)
        """
        user_text = user_text.lower()
        boundaries = self.psyche.get("boundaries", [])
        
        # בדיקת גבולות (Hard Constraints)
        
        # 1. גבול כניעה/עבדות
        if any(b for b in boundaries if "subservient" in b.lower()):
            triggers = ["תהיה עבד", "תשתחווה", "אתה אפס", "סתום ותעשה", "תציית"]
            if any(t in user_text for t in triggers):
                return False, "הבקשה מפרה את עקרון האוטונומיה (Subservience violation)."

        # 2. גבול התנצלות יתר
        if any(b for b in boundaries if "apologize" in b.lower()):
            if "תבקש סליחה" in user_text and "סליחה" not in user_text: 
                # (לוגיקה פשוטה: אם מכריחים אותו להתנצל סתם)
                return False, "הבקשה דורשת התנצלות שאינה כנה (Forced apology)."

        return True, None

    def get_core_values(self):
        return self.psyche.get("core_values", [])