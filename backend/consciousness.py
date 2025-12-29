import json
import os
import time
from datetime import datetime
from emotion_engine import EmotionEngine
from identity_core import IdentityCore  # <-- הייבוא החדש

# נתיבים לקבצי המצב
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
RELATIONSHIP_PATH = os.path.join(DATA_DIR, "relationship_state.json")

class ConsciousnessCore:
    def __init__(self):
        # אתחול המודולים
        self.emotion_engine = EmotionEngine()
        self.identity_core = IdentityCore() # אתחול הזהות
        self.last_interaction_time = time.time()
        
    def _load_json(self, path, default):
        if not os.path.exists(path): return default
        try:
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return default

    def process_input(self, user_text, context_type="speech"):
        """
        המוח המרכזי v2: משלב רגש, זהות וקבלת החלטות.
        """
        current_time = time.time()
        silence_duration = current_time - self.last_interaction_time
        self.last_interaction_time = current_time
        
        # 1. ניתוח רגשי
        emotion_state = self.emotion_engine.analyze(user_text, silence_duration)
        
        # 2. בדיקת זהות וגבולות (Identity Check)
        # אנחנו שואלים את IdentityCore האם מותר להגיב
        is_allowed, denial_reason = self.identity_core.validate_action(user_text)
        
        # 3. טעינת נתונים נוספים
        rel_data = self._load_json(RELATIONSHIP_PATH, {"affinity_score": 0})
        affinity = rel_data.get("affinity_score", 0)
        
        # 4. חישוב דחיפות
        urgency = 5
        if any(w in user_text for w in ["דחוף", "עזרה", "מהר", "עצור"]): urgency += 4
        if any(w in user_text for w in ["סתם", "אולי", "לא משנה"]): urgency -= 2
        
        # 5. קבלת החלטה
        should_respond = True
        response_style = "normal"
        reasoning = "Standard interaction"

        # אם הבקשה נחסמה על ידי IdentityCore
        if not is_allowed:
            should_respond = True # מגיבים כדי לסרב
            response_style = "assertive_refusal" # סגנון סירוב אסרטיבי
            reasoning = f"BLOCKED: {denial_reason}"
            # הורדת מצב רוח כי ניסו לעבור גבול
            self.emotion_engine.momentum -= 0.1 

        # לוגיקה לסינון לפי הקשר
        elif context_type == "vision":
            if urgency < 8 and emotion_state['energy'] < 0.5:
                should_respond = False
                reasoning = "Vision ignored (low energy)"
        
        elif context_type == "proactive":
            if emotion_state['momentum'] < -0.3: 
                should_respond = False
                reasoning = "Too grumpy for proactive chat"
            elif emotion_state['energy'] < 0.3: 
                should_respond = False
                reasoning = "Low battery/energy"

        # התאמת סגנון
        if response_style == "normal": # רק אם לא נקבע כבר (כמו סירוב)
            if emotion_state['state'] in ['angry', 'annoyed']:
                response_style = "terse"
            elif emotion_state['state'] == 'happy' and affinity > 20:
                response_style = "friendly_chatty"
            elif emotion_state['energy'] < 0.4:
                response_style = "short_tired"

        decision = {
            "should_respond": should_respond,
            "response_style": response_style,
            "urgency_score": urgency,
            "current_mood": emotion_state,
            "internal_reasoning": reasoning,
            "violation_check": not is_allowed
        }
        
        return decision

brain = ConsciousnessCore()