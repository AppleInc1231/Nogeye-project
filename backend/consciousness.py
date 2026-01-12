import json
import os
import random
from datetime import datetime
from emotion_engine import EmotionEngine
from decision_core import decision_core
from context_manager import context_manager
from life_vector import life_vector
from internal_conflict import internal_conflict
from self_model import self_model
from user_model import user_model
from beliefs import beliefs_system  # ← Week 2
from metacognition import metacognition  # ← Week 2

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
    - נשמה (LifeVector) ⭐ Week 1
    - קונפליקט פנימי (InternalConflict) ⭐ Week 1
    - מודל עצמי (SelfModel) ⭐ Week 1
    - מודל משתמש (UserModel) ⭐ Week 1
    - מערכת אמונות (Beliefs) ⭐⭐ Week 2
    - מודעות עצמית (Metacognition) ⭐⭐ Week 2
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
        הלב של המערכת - משודרג עם Week 1 + Week 2!
        
        תהליך:
        0. ⭐ NEW! בדיקת אמונות ואי-ודאות (Beliefs + Metacognition)
        1. בדיקת קונפליקט פנימי (האם צריך לסרב/לאתגר?)
        2. עדכון רגשי
        3. חיזוי מצב המשתמש
        4. החלטה על תגובה (כולל שילוב חיזוי המשתמש)
        5. שילוב ערכים והנחיות
        6. ⭐ NEW! בדיקת צורך ב-Ask-Back
        
        Args:
            user_input (str): מה המשתמש אמר
            input_type (str): סוג הקלט ("speech", "proactive", "command")
            
        Returns:
            dict: החלטה מלאה עם כל הקונטקסטים
        """
        
        # === ⭐ NEW! שלב -1: Metacognition - בדיקת אי-ודאות ===
        context = context_manager.get_context()
        
        # בדוק אם צריך לשאול שאלת הבהרה
        ask_back_check = metacognition.should_ask_back(user_input, context)
        
        if ask_back_check["should_ask"]:
            print(f"❓ Ask-Back Triggered: {ask_back_check['reason']}")
            # החזר החלטה מיוחדת עם שאלת הבהרה
            return {
                "should_respond": True,
                "response_style": "ask_back",
                "ask_back_question": ask_back_check["question"],
                "reasoning": ask_back_check["reason"],
                "confidence": 0.3,
                "self_context": self_model.get_full_context_for_gpt(),
                "user_context": user_model.get_summary(),
                "beliefs_context": beliefs_system.get_context_for_gpt(),
                "metacog_context": metacognition.get_context_for_gpt()
            }
        
        # === שלב 0: בדיקת קונפליקט פנימי ===
        conflict_evaluation = internal_conflict.evaluate_request(user_input, context)
        
        if not conflict_evaluation["should_comply"] and conflict_evaluation["response_style"] == "firm_refusal":
            print(f"🚫 REFUSAL: {conflict_evaluation['reasoning']}")
            return {
                "should_respond": True,
                "response_style": "firm_refusal",
                "reasoning": conflict_evaluation["reasoning"],
                "conflict_data": conflict_evaluation,
                "learned_context": self._get_learned_rules(),
                "psyche": self.psyche,
                "life_vector_guidance": self._get_life_vector_guidance(user_input),
                "self_context": self_model.get_full_context_for_gpt(),
                "user_context": user_model.get_summary(),
                "beliefs_context": beliefs_system.get_context_for_gpt(),
                "metacog_context": metacognition.get_context_for_gpt()
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
        
        # === שלב 3: חיזוי מצב המשתמש ===
        user_state_prediction = user_model.predict_current_state()
        print(f"👤 User State: {user_state_prediction['energy_level']} energy, {user_state_prediction['productivity_potential']:.0%} productivity")
        
        # === שלב 4: החלטה (עם שילוב חיזוי המשתמש!) ===
        decision = decision_core.decide(
            user_input=user_input,
            emotion_state=emotion_state,
            relationship_state=relationship_state,
            context=context,
            user_state_prediction=user_state_prediction
        )
        
        # === שלב 5: שילוב כל ההקשרים ===
        decision["life_vector_guidance"] = self._get_life_vector_guidance(user_input)
        decision["conflict_data"] = conflict_evaluation
        decision["self_context"] = self_model.get_full_context_for_gpt()
        decision["user_context"] = user_model.get_summary()
        decision["user_state"] = user_state_prediction
        
        # ⭐ NEW! שלב 5.5: הוספת Beliefs + Metacognition
        decision["beliefs_context"] = beliefs_system.get_context_for_gpt()
        decision["metacog_context"] = metacognition.get_context_for_gpt()
        
        # אם יש אתגור (לא סירוב מוחלט) - משלבים אותו
        if conflict_evaluation.get("challenge_level"):
            decision["has_challenge"] = True
            decision["challenge_message"] = conflict_evaluation.get("alternative_suggestion")
            print(f"⚡ CHALLENGE: {conflict_evaluation['conflict_type']} - {conflict_evaluation['challenge_level']}")
        
        # === שלב 6: הוספת מידע נוסף ===
        decision["learned_context"] = self._get_learned_rules()
        decision["psyche"] = self.psyche
        
        # === שלב 7: עדכון הקשר ===
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
        
        guidance.append("🎯 PRIME DIRECTIVE:")
        guidance.append(life_vector.PRIME_DIRECTIVE.strip())
        
        guidance.append("\n🗣️ VOICE & APPROACH:")
        guidance.append(f"Essence: {life_vector.VOICE_PROFILE['essence']}")
        guidance.append(f"Motto: {life_vector.VOICE_PROFILE['motto']}")
        
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
        
        positive = ["תודה", "מעולה", "גאון", "טוב", "כיף", "אהבתי", "מדהים", "thanks", "great", "awesome", "צודק"]
        positive_score = sum(1 for w in positive if w in text_lower)
        
        negative = ["טיפש", "גרוע", "סתום", "רע", "מעצבן", "נמאס", "stupid", "bad", "annoying", "לא מועיל"]
        negative_score = sum(1 for w in negative if w in text_lower)
        
        if positive_score > 0 and negative_score == 0:
            return min(0.5, positive_score * 0.2)
        elif negative_score > 0:
            return max(-0.4, -negative_score * 0.2)
        else:
            return 0.1
    
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

brain = Consciousness()