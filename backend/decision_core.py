"""
Decision Core - המוח המחליט של Nog
=====================================

תפקיד: לקבל החלטות מבוססות על מצב פנימי, קשר עם משתמש, והקשר.

מחזיר החלטה:
- should_respond: האם לענות בכלל
- response_style: איך לענות (short/long/friendly/terse/action_oriented)
- reasoning: למה הוחלט כך (לדיבאג)
"""

import json
import os
from datetime import datetime
from behavioral_memory import behavioral_memory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

class DecisionCore:
    """
    המוח המחליט של Nog.
    מקבל קלט ומצב, מחזיר החלטה.
    
    ⭐ NEW: עכשיו משתמש גם ב-User Model Predictions!
    """
    
    def __init__(self):
        self.last_decision_time = datetime.now()
        self.interaction_history = []  # היסטוריית החלטות אחרונות
        
    def decide(self, user_input, emotion_state, relationship_state, context, user_state_prediction=None):
        """
        פונקציית החלטה ראשית - משודרגת עם Behavioral Memory + User Model!
        
        Args:
            user_input (str): מה המשתמש אמר
            emotion_state (dict): מצב רוח ואנרגיה של Nog
            relationship_state (dict): רמת קשר עם המשתמש
            context (dict): הקשר נוכחי (מה קורה עכשיו)
            user_state_prediction (dict): ⭐ NEW! חיזוי מצב המשתמש
            
        Returns:
            dict: {
                "should_respond": bool,
                "response_style": str,
                "reasoning": str,
                "confidence": float (0-1),
                "behavioral_rules": str (הוראות מהזיכרון)
            }
        """
        
        # === בדיקה אם המשתמש נתן פידבק ===
        if behavioral_memory.analyze_feedback(user_input):
            print("🎓 Learned new behavior from feedback!")
        
        # חילוץ נתונים
        momentum = emotion_state.get("momentum", 0.0)
        energy = emotion_state.get("energy", 1.0)
        affinity = relationship_state.get("affinity_score", 0)
        tier = relationship_state.get("relationship_tier", "Stranger")
        
        # בניית ההחלטה
        decision = {
            "should_respond": True,
            "response_style": "normal",
            "reasoning": "",
            "confidence": 0.5,
            "behavioral_rules": ""
        }
        
        # ═══════════════════════════════════════════════════════════
        # ⭐ NEW! Layer 0: User State Prediction (הכי גבוה בעדיפות!)
        # ═══════════════════════════════════════════════════════════
        
        if user_state_prediction:
            recommended_approach = user_state_prediction.get("recommended_approach", "balanced")
            user_energy = user_state_prediction.get("energy_level", "medium")
            productivity = user_state_prediction.get("productivity_potential", 0.5)
            reasoning_hints = user_state_prediction.get("reasoning", [])
            
            # התאמה אוטומטית לפי מצב המשתמש
            if recommended_approach == "gentle" or user_energy == "low":
                decision["response_style"] = "short"
                decision["reasoning"] = f"User in low energy state: {reasoning_hints[0] if reasoning_hints else 'Based on patterns'}"
                decision["confidence"] = 0.75
                print(f"👤 User Model Override: gentle approach (low energy)")
            
            elif recommended_approach == "challenging" and productivity > 0.7:
                decision["response_style"] = "action_oriented"
                decision["reasoning"] = f"User in peak productive state - push for action"
                decision["confidence"] = 0.85
                print(f"👤 User Model Override: challenging approach (peak time)")
            
            elif recommended_approach == "supportive":
                decision["response_style"] = "friendly_chatty"
                decision["reasoning"] = "User may need encouragement"
                decision["confidence"] = 0.7
                print(f"👤 User Model Override: supportive approach")
        
        # ═══════════════════════════════════════════════════════════
        # Decision Tree - עץ ההחלטות (עם זיכרון התנהגותי!)
        # ═══════════════════════════════════════════════════════════
        
        # --- Layer 1: סינון ראשוני ---
        
        # 1.1 בדיקת דחיפות
        urgency = self._detect_urgency(user_input)
        
        if urgency == "critical":
            decision["should_respond"] = True
            decision["response_style"] = "action_oriented"
            decision["reasoning"] = "Critical urgency detected"
            decision["confidence"] = 1.0
            # אפילו בדחיפות - מכבד העדפות אורך
            decision["response_style"] = behavioral_memory.apply_to_style(decision["response_style"])
            decision["behavioral_rules"] = behavioral_memory.get_context_instructions()
            return decision
        
        # 1.2 בדיקת "רעש"
        if self._is_noise(user_input):
            decision["should_respond"] = False
            decision["reasoning"] = "Detected noise/irrelevant input"
            decision["confidence"] = 0.9
            return decision
        
        # --- Layer 2: בדיקת מצב רגשי (של Nog) ---
        
        # 2.1 עייפות קיצונית
        if energy < 0.2:
            if affinity < 30:
                decision["should_respond"] = False
                decision["reasoning"] = "Too tired, low affinity"
                decision["confidence"] = 0.8
                return decision
            else:
                decision["response_style"] = "short_tired"
                decision["reasoning"] = "Low energy but high affinity"
                decision["confidence"] = 0.7
        
        # 2.2 מצב רוח רע
        if momentum < -0.4:
            if affinity < 20:
                decision["should_respond"] = False
                decision["reasoning"] = "Bad mood, stranger"
                decision["confidence"] = 0.85
                return decision
            elif affinity < 50:
                decision["response_style"] = "terse"
                decision["reasoning"] = "Bad mood, acquaintance level"
                decision["confidence"] = 0.75
        
        # 2.3 מצב רוח מצוין
        if momentum > 0.6 and energy > 0.7:
            if affinity > 50:
                # רק אם User Model לא דרס כבר
                if not user_state_prediction or user_state_prediction.get("recommended_approach") != "gentle":
                    decision["response_style"] = "friendly_chatty"
                    decision["reasoning"] = "Good mood, close relationship"
                    decision["confidence"] = 0.9
        
        # --- Layer 3: ניתוח תוכן השאלה ---
        
        intent = self._analyze_intent(user_input)
        
        if intent == "greeting":
            decision["response_style"] = "short"
            decision["reasoning"] = "Simple greeting"
            decision["confidence"] = 0.95
            
        elif intent == "question":
            decision["should_respond"] = True
            if urgency == "high":
                decision["response_style"] = "action_oriented"
            else:
                decision["response_style"] = "normal"
            decision["reasoning"] = "Direct question asked"
            decision["confidence"] = 0.9
            
        elif intent == "command":
            decision["should_respond"] = True
            decision["response_style"] = "action_oriented"
            decision["reasoning"] = "Command received"
            decision["confidence"] = 1.0
            
        elif intent == "small_talk":
            if affinity < 30:
                decision["should_respond"] = False
                decision["reasoning"] = "Small talk with stranger"
                decision["confidence"] = 0.7
            else:
                decision["response_style"] = "friendly"
                decision["reasoning"] = "Small talk with friend"
                decision["confidence"] = 0.8
        
        # --- Layer 4: בדיקת הקשר ---
        
        if context.get("in_process"):
            if urgency != "high":
                decision["should_respond"] = False
                decision["reasoning"] = "In the middle of a process"
                decision["confidence"] = 0.7
        
        # === Layer 5: התאמה לפי Behavioral Memory ===
        decision["response_style"] = behavioral_memory.apply_to_style(decision["response_style"])
        decision["behavioral_rules"] = behavioral_memory.get_context_instructions()
        
        # שמירת ההחלטה בהיסטוריה
        self._log_decision(decision, user_input)
        
        return decision
    
    # ═══════════════════════════════════════════════════════════
    # Helper Functions - פונקציות עזר
    # ═══════════════════════════════════════════════════════════
    
    def _detect_urgency(self, text):
        """
        מזהה רמת דחיפות בטקסט.
        Returns: "critical" | "high" | "medium" | "low"
        """
        text_lower = text.lower()
        
        # דחיפות קריטית
        critical_keywords = ["דחוף", "מהר", "עכשיו", "מיד", "חירום", "urgent", "emergency", "now"]
        if any(kw in text_lower for kw in critical_keywords):
            return "critical"
        
        # דחיפות גבוהה
        high_keywords = ["צריך", "חשוב", "בבקשה", "need", "important", "please"]
        if any(kw in text_lower for kw in high_keywords):
            return "high"
        
        # שאלות מרמזות על דחיפות
        if "?" in text or "איך" in text_lower or "מה" in text_lower:
            return "medium"
        
        return "low"
    
    def _is_noise(self, text):
        """
        בודק אם הטקסט הוא "רעש" שלא צריך להגיב לו.
        """
        text_lower = text.lower().strip()
        
        # טקסטים קצרים מדי
        if len(text_lower) < 3:
            return True
        
        # צלילים/רעשים
        noise_patterns = ["אההה", "אממ", "הממ", "אוף", "ugh", "hmm", "uh"]
        if any(pattern in text_lower for pattern in noise_patterns):
            return True
        
        return False
    
    def _analyze_intent(self, text):
        """
        מנתח את הכוונה מאחורי הטקסט.
        Returns: "greeting" | "question" | "command" | "small_talk" | "statement"
        """
        text_lower = text.lower()
        
        # ברכה
        greetings = ["שלום", "היי", "מה קורה", "מה נשמע", "בוקר טוב", "ערב טוב", "hello", "hi"]
        if any(g in text_lower for g in greetings) and len(text_lower) < 20:
            return "greeting"
        
        # שאלה
        question_words = ["מה", "איך", "למה", "מתי", "איפה", "מי", "?", "what", "how", "why", "when", "where"]
        if any(qw in text_lower for qw in question_words):
            return "question"
        
        # פקודה
        command_words = ["תעשה", "תבדוק", "תחפש", "תגיד", "תשלח", "do", "check", "search", "tell", "send"]
        if any(cw in text_lower for cw in command_words):
            return "command"
        
        # שיחת חולין
        small_talk = ["איך אתה", "מה שלומך", "כיף", "how are you", "what's up"]
        if any(st in text_lower for st in small_talk):
            return "small_talk"
        
        return "statement"
    
    def _log_decision(self, decision, user_input):
        """
        שומר את ההחלטה בהיסטוריה (לדיבאג ולמידה עתידית)
        """
        self.interaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input[:50],  # רק התחלה
            "decision": decision
        })
        
        # שומר רק 20 אחרונות
        if len(self.interaction_history) > 20:
            self.interaction_history = self.interaction_history[-20:]

# יצירת מופע יחיד
decision_core = DecisionCore()