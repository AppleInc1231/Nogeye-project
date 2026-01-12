# backend/metacognition.py

import json
import os
from datetime import datetime
from beliefs import beliefs_system

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
METACOG_PATH = os.path.join(DATA_DIR, "metacognition.json")

class Metacognition:
    """
    Metacognition - "מודעות עצמית" של Nog.
    
    זה המודול שגורם ל-Nog לדעת מה הוא יודע ומה הוא לא יודע.
    
    Features:
    - Confidence Tracking: עוקב אחר רמת הביטחון בכל תחום
    - Know/Don't-Know Detection: יודע מתי להגיד "אני לא יודע"
    - Ask-Back Mechanism: יודע מתי לשאול במקום להניח
    - Uncertainty Expression: מבטא אי-ודאות בצורה טבעית
    
    זה מה שהופך את Nog מ"תמיד בטוח" ל"כנה וסקפטי".
    """
    
    def __init__(self):
        self.state = self.load_or_create()
    
    def load_or_create(self):
        if os.path.exists(METACOG_PATH):
            try:
                with open(METACOG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_initial_state()
        else:
            return self.create_initial_state()
    
    def create_initial_state(self):
        """יצירת מצב ראשוני"""
        return {
            "confidence_by_domain": {
                # רמת ביטחון בכל תחום
                "user_patterns": 0.5,       # כמה אני מכיר את המשתמש
                "user_preferences": 0.3,     # מה הוא אוהב/לא אוהב
                "user_goals": 0.4,           # מה המטרות שלו
                "world_knowledge": 0.7,      # ידע כללי על העולם
                "self_capabilities": 0.8     # מה אני יכול לעשות
            },
            
            "uncertainty_threshold": 0.5,    # מתחת לזה = "אני לא בטוח"
            
            "ask_back_triggers": {
                # מתי לשאול במקום להניח
                "ambiguous_reference": True,   # "הפרויקט" - איזה?
                "missing_critical_info": True,  # חסר מידע חיוני
                "conflicting_beliefs": True,    # אמונות סותרות
                "low_confidence": True          # ביטחון נמוך
            },
            
            "calibration": {
                # כיול - האם הביטחון שלי תואם למציאות?
                "predictions_made": 0,
                "predictions_correct": 0,
                "accuracy": 0.0,
                "overconfident": False,
                "underconfident": False
            },
            
            "meta": {
                "last_updated": datetime.now().isoformat(),
                "total_ask_backs": 0,
                "total_uncertainties_expressed": 0
            }
        }
    
    def save(self):
        """שמירה לדיסק"""
        try:
            self.state["meta"]["last_updated"] = datetime.now().isoformat()
            with open(METACOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving metacognition: {e}")
    
    def assess_confidence(self, domain, context=""):
        """
        מעריך את רמת הביטחון בתחום מסוים.
        
        Args:
            domain (str): התחום ("user_patterns", "user_preferences", etc.)
            context (str): הקשר ספציפי
        
        Returns:
            dict: {
                "confidence": float,
                "should_ask": bool,
                "reasoning": str
            }
        """
        
        base_confidence = self.state["confidence_by_domain"].get(domain, 0.5)
        
        # התאמת ביטחון לפי הקשר ספציפי
        adjusted_confidence = base_confidence
        
        # בדיקת אמונות רלוונטיות
        if domain == "user_patterns":
            # בדוק כמה אמונות יש על המשתמש
            user_beliefs = beliefs_system.beliefs.get("about_user", {})
            high_conf_count = sum(1 for b in user_beliefs.values() if b.get("confidence", 0) > 0.7)
            
            if high_conf_count > 5:
                adjusted_confidence = min(1.0, adjusted_confidence + 0.2)
            elif high_conf_count < 2:
                adjusted_confidence = max(0.0, adjusted_confidence - 0.2)
        
        # בדיקת קונפליקטים
        conflicts = beliefs_system.detect_conflicts()
        if conflicts and domain in ["user_patterns", "user_preferences"]:
            adjusted_confidence = max(0.0, adjusted_confidence - 0.3)
        
        # החלטה אם לשאול
        threshold = self.state["uncertainty_threshold"]
        should_ask = adjusted_confidence < threshold
        
        result = {
            "confidence": adjusted_confidence,
            "should_ask": should_ask,
            "reasoning": self._explain_confidence(adjusted_confidence, should_ask)
        }
        
        return result
    
    def should_ask_back(self, user_input, context):
        """
        מחליט האם לשאול שאלת הבהרה במקום להניח.
        
        Args:
            user_input (str): מה המשתמש אמר
            context (dict): הקשר נוכחי
        
        Returns:
            dict: {
                "should_ask": bool,
                "question": str or None,
                "reason": str
            }
        """
        
        triggers = self.state["ask_back_triggers"]
        user_lower = user_input.lower()
        
        # 1. זיהוי התייחסות מעורפלת
        if triggers["ambiguous_reference"]:
            ambiguous_words = ["זה", "הפרויקט", "הדבר", "השיחה", "it", "that", "the thing"]
            if any(word in user_lower for word in ambiguous_words):
                # בדוק אם יש context ברור
                if not context.get("last_topic"):
                    return {
                        "should_ask": True,
                        "question": self._generate_clarification_question(user_input),
                        "reason": "Ambiguous reference without clear context"
                    }
        
        # 2. מידע קריטי חסר
        if triggers["missing_critical_info"]:
            # זיהוי פקודות שחסר להן מידע
            if any(word in user_lower for word in ["תשלח", "תעביר", "send", "forward"]):
                if "ל" not in user_lower and "to" not in user_lower:
                    return {
                        "should_ask": True,
                        "question": "למי אני צריך לשלוח את זה?",
                        "reason": "Missing recipient information"
                    }
        
        # 3. אמונות סותרות
        if triggers["conflicting_beliefs"]:
            conflicts = beliefs_system.detect_conflicts()
            if conflicts:
                return {
                    "should_ask": True,
                    "question": "רגע, אני לא בטוח - אתה מעדיף X או Y?",
                    "reason": f"Conflicting beliefs: {conflicts[0]['type']}"
                }
        
        # 4. ביטחון נמוך
        if triggers["low_confidence"]:
            # בדוק ביטחון בהבנת הכוונה
            intent_confidence = self._assess_intent_confidence(user_input)
            if intent_confidence < 0.4:
                return {
                    "should_ask": True,
                    "question": "לא בטוח שהבנתי - אתה רוצה ש...?",
                    "reason": f"Low intent understanding confidence: {intent_confidence:.0%}"
                }
        
        # אין צורך לשאול
        return {
            "should_ask": False,
            "question": None,
            "reason": "Sufficient confidence to proceed"
        }
    
    def express_uncertainty(self, confidence, statement):
        """
        מחזיר גרסה של statement עם ביטוי אי-ודאות מתאים.
        
        Args:
            confidence (float): רמת ביטחון (0.0-1.0)
            statement (str): המשפט המקורי
        
        Returns:
            str: משפט עם ביטוי אי-ודאות
        
        Examples:
            confidence=0.9 → "אני די בטוח ש..."
            confidence=0.5 → "נראה לי ש..."
            confidence=0.2 → "אני לא בטוח, אבל אולי..."
        """
        
        if confidence > 0.85:
            prefixes = ["אני די בטוח ש", "זה ברור ש", ""]
        elif confidence > 0.7:
            prefixes = ["נראה ש", "כנראה ש", ""]
        elif confidence > 0.5:
            prefixes = ["נראה לי ש", "אני חושב ש", ""]
        elif confidence > 0.3:
            prefixes = ["אני לא ממש בטוח, אבל ", "זה לא ברור לי אבל אולי ", ""]
        else:
            prefixes = ["אני לא בטוח בכלל, אבל אולי ", "זה נראה לי מאוד לא ברור - ", ""]
        
        # בחר prefix אקראי
        import random
        prefix = random.choice(prefixes)
        
        if prefix:
            self.state["meta"]["total_uncertainties_expressed"] += 1
            self.save()
        
        return f"{prefix}{statement}"
    
    def calibrate(self, prediction_was_correct):
        """
        מכייל את מערכת הביטחון לפי תוצאות בפועל.
        
        Args:
            prediction_was_correct (bool): האם התחזית הייתה נכונה
        
        זה עוזר ל-Nog להבין אם הוא יותר מדי בטוח או יותר מדי זהיר.
        """
        
        self.state["calibration"]["predictions_made"] += 1
        
        if prediction_was_correct:
            self.state["calibration"]["predictions_correct"] += 1
        
        # חישוב accuracy
        total = self.state["calibration"]["predictions_made"]
        correct = self.state["calibration"]["predictions_correct"]
        
        if total > 0:
            accuracy = correct / total
            self.state["calibration"]["accuracy"] = accuracy
            
            # זיהוי overconfidence / underconfidence
            if accuracy < 0.6 and total > 10:
                self.state["calibration"]["overconfident"] = True
                # הפחת ביטחון בכל התחומים
                for domain in self.state["confidence_by_domain"]:
                    current = self.state["confidence_by_domain"][domain]
                    self.state["confidence_by_domain"][domain] = max(0.1, current - 0.1)
                print("⚠️  Overconfidence detected - lowering all domain confidences")
            
            elif accuracy > 0.85 and total > 10:
                self.state["calibration"]["underconfident"] = True
                # העלה ביטחון קצת
                for domain in self.state["confidence_by_domain"]:
                    current = self.state["confidence_by_domain"][domain]
                    self.state["confidence_by_domain"][domain] = min(1.0, current + 0.05)
                print("✅ High accuracy - slightly increasing confidence")
        
        self.save()
    
    def get_context_for_gpt(self):
        """
        מחזיר סיכום metacognition לשימוש ב-GPT context.
        
        Returns:
            str: טקסט מעוצב
        """
        
        context = "METACOGNITION (Self-Awareness):\n"
        context += "═" * 60 + "\n"
        
        # רמות ביטחון
        context += "\nCONFIDENCE BY DOMAIN:\n"
        for domain, conf in self.state["confidence_by_domain"].items():
            context += f"  • {domain}: {conf:.0%}\n"
        
        # כיול
        calib = self.state["calibration"]
        if calib["predictions_made"] > 0:
            context += f"\nCALIBRATION: {calib['accuracy']:.0%} accuracy ({calib['predictions_correct']}/{calib['predictions_made']})\n"
            if calib["overconfident"]:
                context += "  ⚠️ System is overconfident - be more careful\n"
            if calib["underconfident"]:
                context += "  ✓ System is well-calibrated\n"
        
        context += "\n" + "═" * 60
        
        return context
    
    def _explain_confidence(self, confidence, should_ask):
        """מסביר למה הביטחון ברמה מסוימת"""
        if confidence > 0.8:
            return "High confidence based on strong evidence"
        elif confidence > 0.6:
            return "Moderate confidence - some evidence"
        elif confidence > 0.4:
            return "Low confidence - limited evidence"
        else:
            return "Very low confidence - should ask for clarification"
    
    def _generate_clarification_question(self, user_input):
        """מייצר שאלת הבהרה"""
        # בינתיים פשוט
        return "על מה בדיוק אתה מדבר?"
    
    def _assess_intent_confidence(self, user_input):
        """מעריך כמה אני בטוח שהבנתי את הכוונה"""
        # לוגיקה פשוטה - ככל שהטקסט יותר ארוך ומפורט, יותר בטוח
        word_count = len(user_input.split())
        
        if word_count > 8:
            return 0.8
        elif word_count > 4:
            return 0.6
        else:
            return 0.4

# יצירת מופע גלובלי
metacognition = Metacognition()
