import json
import os
import random
from datetime import datetime
from emotion_engine import EmotionEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
PSYCHE_PATH = os.path.join(DATA_DIR, "psyche.json")
RELATIONSHIP_PATH = os.path.join(DATA_DIR, "relationship_state.json")

class Consciousness:
    def __init__(self):
        self.emotion_engine = EmotionEngine()
        self.load_psyche()
    
    def load_psyche(self):
        if not os.path.exists(PSYCHE_PATH):
            default_psyche = {
                "name": "Nog",
                "core_values": ["curiosity", "loyalty", "authenticity"],
                "personality_traits": {"humor": 0.7, "cynicism": 0.3, "patience": 0.5}
            }
            with open(PSYCHE_PATH, "w") as f:
                json.dump(default_psyche, f)
            self.psyche = default_psyche
        else:
            with open(PSYCHE_PATH, "r") as f:
                self.psyche = json.load(f)

    def load_relationship(self):
        if os.path.exists(RELATIONSHIP_PATH):
            with open(RELATIONSHIP_PATH, "r") as f:
                return json.load(f)
        return {"affinity_score": 0, "relationship_tier": "Stranger"}

    def process_input(self, user_input, input_type="speech"):
        """
        הלב של המערכת. מקבל קלט ומחליט האם ואיך להגיב.
        מחזיר מילון עם ההחלטה.
        """
        # 1. עדכון רגשי (האם מה שנאמר משמח/מעצבן?)
        # ניתוח פשטני בינתיים - בעתיד נחבר ל-NLP אמיתי
        stimulus = 0.1
        if any(w in user_input for w in ["תודה", "מעולה", "גאון", "טוב"]): 
            stimulus = 0.3
        elif any(w in user_input for w in ["טיפש", "גרוע", "סתום", "רע"]): 
            stimulus = -0.5
            
        self.emotion_engine.update_mood(stimulus)
        current_mood = self.emotion_engine.momentum
        current_energy = self.emotion_engine.energy
        
        rel = self.load_relationship()
        affinity = rel.get("affinity_score", 0)

        decision = {
            "should_respond": True,
            "response_style": "normal", # normal, short_tired, terse, friendly_chatty, action_oriented
            "internal_reasoning": ""
        }

        # --- לוגיקת קבלת ההחלטות (The Soul) ---

        # 1. סירוב בגלל יחסים גרועים
        if affinity < -10 and current_mood < -0.5:
            decision["should_respond"] = False
            decision["internal_reasoning"] = "I am angry and we are not close. Ignoring."
            return decision

        # 2. עייפות (Energy Low)
        if current_energy < 0.2:
            decision["response_style"] = "short_tired"
            decision["internal_reasoning"] = "Low energy. I will answer briefly."
        
        # 3. מצב רוח רע (Mood Low)
        elif current_mood < -0.3:
            decision["response_style"] = "terse"
            decision["internal_reasoning"] = "Bad mood. I will be sharp and direct."

        # 4. חברות טובה (High Affinity)
        elif affinity > 50 and current_mood > 0.2:
            decision["response_style"] = "friendly_chatty"
            decision["internal_reasoning"] = "We are friends. I will be warm and playful."

        # 5. דחיפות (מילים כמו 'מהר', 'עכשיו')
        if any(w in user_input for w in ["מהר", "דחוף", "עכשיו", "מיד"]):
            decision["response_style"] = "action_oriented"
            decision["internal_reasoning"] = "User signaled urgency. Skipping pleasantries."

        # 6. בדיקה פרואקטיבית (אם הקריאה הגיעה מהטיימר ולא מדיבור)
        if input_type == "proactive":
            # ליזום רק אם יש אנרגיה גבוהה ומצב רוח טוב
            if current_energy > 0.6 and current_mood > 0.3:
                 decision["should_respond"] = True
                 decision["internal_reasoning"] = "Feeling good, let's chat."
            else:
                 decision["should_respond"] = False
                 decision["internal_reasoning"] = "Not in the mood to initiate."

        return decision

# יצירת המופע הראשי
brain = Consciousness()