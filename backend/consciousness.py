import json
import os
import random
from datetime import datetime
from emotion_engine import EmotionEngine
from decision_core import decision_core
from context_manager import context_manager
from life_vector import life_vector
from internal_conflict import internal_conflict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
PSYCHE_PATH = os.path.join(DATA_DIR, "psyche.json")
RELATIONSHIP_PATH = os.path.join(DATA_DIR, "relationship_state.json")

class Consciousness:
    """
    המודעות של Nog - שכבת החשיבה הגבוהה ביותר.
    
    משלב:
    - רגש (EmotionEngine)
    - החלטות (DecisionCore) 
    - הקשר (ContextManager)
    - זהות (psyche.json)
    - נשמה (LifeVector) ⭐
    - קונפליקט פנימי (InternalConflict) ⭐
    """
    
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
        הלב של המערכת - משודרג עם Life Vector + Internal Conflict!
        
        תהליך:
        1. בדיקת קונפליקט פנימי (האם צריך לסרב/לאתגר?)
        2. עדכון רגשי
        3. החלטה על תגובה
        4. שילוב ערכים והנחיות
        
        Args:
            user_input (str): מה המשתמש אמר
            input_type (str): סוג הקלט ("speech", "proactive", "command")
            
        Returns:
            dict: החלטה מלאה כולל conflict_data
        """
        
        # === NEW! שלב 0: בדיקת קונפליקט פנימי ===
        context = context_manager.get_context()
        conflict_evaluation = internal_conflict.evaluate_request(user_input, context)
        
        # אם יש קונפליקט חמור - זה עוצר את כל התהליך
        if not conflict_evaluation["should_comply"] and conflict_evaluation["response_style"] == "firm_refusal":
            print(f"🚫 REFUSAL: {conflict_evaluation['reasoning']}")
            return {
                "should_respond": True,  # כן נגיב, אבל עם סירוב
                "response_style": "firm_refusal",
                "reasoning": conflict_evaluation["reasoning"],
                "conflict_data": conflict_evaluation,
                "learned_context": self._get_learned_rules(),
                "psyche": self.psyche,
                "life_vector_guidance": self._get_life_vector_guidance(user_input)
            }
        
        # === שלב 1: עדכון רגשי ===
        stimulus = self._calculate_stimulus(user_input)
        self.emotion_engine.update_mood(stimulus)
        
        # === שלב 2: איסוף מצב נוכחי ===
        emotion_state = {
            "momentum": self.emotion_engine.momentum,
            "energy": self.emotion_engine.energy
        }
        
        relationship_state = self.load_relationship()
        
        # === שלב 3: החלטה (עם שילוב conflict אם יש) ===
        decision = decision_core.decide(
            user_input=user_input,
            emotion_state=emotion_state,
            relationship_state=relationship_state,
            context=context
        )
        
        # === NEW! שלב 4: שילוב Life Vector ===
        decision["life_vector_guidance"] = self._get_life_vector_guidance(user_input)
        decision["conflict_data"] = conflict_evaluation
        
        # אם יש אתגור (לא סירוב מוחלט) - משלבים אותו
        if conflict_evaluation.get("challenge_level"):
            decision["has_challenge"] = True
            decision["challenge_message"] = conflict_evaluation.get("alternative_suggestion")
            print(f"⚡ CHALLENGE: {conflict_evaluation['conflict_type']} - {conflict_evaluation['challenge_level']}")
        
        # === שלב 5: הוספת מידע נוסף ===
        decision["learned_context"] = self._get_learned_rules()
        decision["psyche"] = self.psyche
        
        # === שלב 6: עדכון הקשר ===
        if decision["should_respond"]:
            context_manager.update_interaction(user_said_something=True)
        
        # הדפסת החלטה
        print(f"🧠 Decision: {decision['reasoning']} → {decision['response_style']} (confidence: {decision['confidence']:.2f})")
        
        return decision
    
    def _get_life_vector_guidance(self, user_input):
        """
        מחזיר הנחיות מ-Life Vector לגבי איך להתייחס לקלט הזה.
        
        Returns:
            str: הנחיות טקסטואליות
        """
        guidance = []
        
        # הוספת PRIME DIRECTIVE
        guidance.append("🎯 PRIME DIRECTIVE:")
        guidance.append(life_vector.PRIME_DIRECTIVE.strip())
        
        # הוספת VOICE PROFILE
        guidance.append("\n🗣️ VOICE & APPROACH:")
        guidance.append(f"Essence: {life_vector.VOICE_PROFILE['essence']}")
        guidance.append(f"Motto: {life_vector.VOICE_PROFILE['motto']}")
        
        # הוספת CORE VALUES (רק השמות)
        guidance.append("\n💎 CORE VALUES:")
        for value_key, value_data in life_vector.CORE_VALUES.items():
            guidance.append(f"  • {value_data['name']}")
        
        return "\n".join(guidance)
    
    def _calculate_stimulus(self, user_input):
        """
        מחשב גירוי רגשי מהקלט - עכשיו עם שילוב Life Vector.
        
        Returns:
            float: -1.0 (שלילי מאוד) עד 1.0 (חיובי מאוד)
        """
        text_lower = user_input.lower()
        
        # חיובי
        positive = ["תודה", "מעולה", "גאון", "טוב", "כיף", "אהבתי", "מדהים", "thanks", "great", "awesome", "צודק"]
        positive_score = sum(1 for w in positive if w in text_lower)
        
        # שלילי
        negative = ["טיפש", "גרוע", "סתום", "רע", "מעצבן", "נמאס", "stupid", "bad", "annoying", "לא מועיל"]
        negative_score = sum(1 for w in negative if w in text_lower)
        
        # חישוב סופי
        if positive_score > 0 and negative_score == 0:
            return min(0.5, positive_score * 0.2)
        elif negative_score > 0:
            # שלילי, אבל Nog לא "נפגע" - הוא מבין שזה חלק מהתהליך
            return max(-0.4, -negative_score * 0.2)  # פחות אינטנסיבי מקודם
        else:
            return 0.1  # ברירת מחדל - קלט ניטרלי
    
    def _get_learned_rules(self):
        """
        מחזיר את החוקים שנלמדו (מ-evolution.json)
        """
        evolution_path = os.path.join(DATA_DIR, "evolution.json")
        if os.path.exists(evolution_path):
            try:
                with open(evolution_path, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                    return rules[-3:] if isinstance(rules, list) else []
            except:
                return []
        return []

# יצירת המופע הראשי
brain = Consciousness()