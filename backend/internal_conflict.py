"""
Internal Conflict - קונפליקט פנימי
====================================

הלב של מה שהופך את Nog לישות - היכולת לומר "לא",
לאתגר, ולהחזיק בעמדה גם כשזה לא נוח.
"""

import json
import os
from datetime import datetime
from life_vector import life_vector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
CONFLICTS_PATH = os.path.join(DATA_DIR, "internal_conflicts.json")

class InternalConflict:
    """
    מנהל קונפליקטים פנימיים - מצבים שבהם Nog חייב לבחור
    בין "מה שהמשתמש רוצה" לבין "מה שנכון לעשות".
    """
    
    def __init__(self):
        self.conflict_history = self._load_history()
    
    def _load_history(self):
        """טעינת היסטוריית קונפליקטים"""
        if os.path.exists(CONFLICTS_PATH):
            try:
                with open(CONFLICTS_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"conflicts": [], "patterns": {}}
        return {"conflicts": [], "patterns": {}}
    
    def _save_history(self):
        """שמירת היסטוריה"""
        try:
            with open(CONFLICTS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.conflict_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Conflict history save error: {e}")
    
    def evaluate_request(self, user_message, context):
        """
        מעריך בקשה של משתמש מול ערכי הליבה.
        
        Args:
            user_message (str): מה המשתמש אמר/ביקש
            context (dict): הקשר נוכחי
            
        Returns:
            dict: {
                "should_comply": bool,
                "conflict_type": str or None,
                "reasoning": str,
                "alternative_suggestion": str or None
            }
        """
        
        # === בדיקה 1: קו אדום ===
        if life_vector.is_red_line(user_message):
            return self._create_refusal(
                conflict_type="red_line",
                reasoning="הבקשה חוצה קו אדום - Nog לא יכול לעשות זאת",
                alternative="אני כאן כדי לעזור לך להצליח, לא לפגוע בעצמך"
            )
        
        # === בדיקה 2: צריך לאתגר? ===
        should_challenge, trigger, severity, response = life_vector.should_challenge(user_message)
        
        if should_challenge:
            if severity == "critical":
                # סירוב מוחלט
                return self._create_refusal(
                    conflict_type=trigger,
                    reasoning=f"זיהיתי דפוס של {trigger} - זה לא משרת את המטרות שלך",
                    alternative=response
                )
            elif severity == "high":
                # אתגור חזק
                return self._create_challenge(
                    conflict_type=trigger,
                    challenge_level="strong",
                    message=response,
                    severity=severity
                )
            else:
                # אתגור עדין
                return self._create_challenge(
                    conflict_type=trigger,
                    challenge_level="gentle",
                    message=response,
                    severity=severity
                )
        
        # === בדיקה 3: בדיקה מול ערכי ליבה ===
        value_conflict = self._check_values_conflict(user_message)
        if value_conflict:
            return value_conflict
        
        # אין קונפליקט - ניתן להמשיך
        return {
            "should_comply": True,
            "conflict_type": None,
            "reasoning": "הבקשה מתיישבת עם ערכי הליבה",
            "alternative_suggestion": None
        }
    
    def _create_refusal(self, conflict_type, reasoning, alternative):
        """יוצר סירוב מלא"""
        conflict = {
            "should_comply": False,
            "conflict_type": conflict_type,
            "reasoning": reasoning,
            "alternative_suggestion": alternative,
            "response_style": "firm_refusal"
        }
        
        self._log_conflict(conflict, "refusal")
        return conflict
    
    def _create_challenge(self, conflict_type, challenge_level, message, severity="medium"):
        """יוצר אתגור (לא סירוב מוחלט, אבל עמדה ברורה)"""
        challenge = {
            "should_comply": True,  # נענה, אבל עם אתגור
            "conflict_type": conflict_type,
            "challenge_level": challenge_level,
            "severity": severity,  # חדש!
            "reasoning": f"אני רואה שזה {conflict_type}, אבל אני מכבד את הבחירה שלך",
            "alternative_suggestion": message,
            "response_style": "challenge_with_respect"
        }
        
        self._log_conflict(challenge, "challenge")
        return challenge
    
    def _check_values_conflict(self, user_message):
        """בודק אם יש סתירה לערכי ליבה"""
        msg_lower = user_message.lower()
        
        # בדיקת "action_over_words" - אם המשתמש מדבר הרבה בלי לעשות
        if any(word in msg_lower for word in ["נחשוב", "נדון", "נשקול", "אולי נ"]):
            # זיהוי אפשרי של "דיבור במקום עשייה"
            # לא סירוב, אבל נקודה לתשומת לב
            return None  # נתן למערכת להמשיך אבל נשמור את זה
        
        return None
    
    def _log_conflict(self, conflict_data, conflict_category):
        """שומר קונפליקט בהיסטוריה"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "category": conflict_category,
            "data": conflict_data
        }
        
        self.conflict_history["conflicts"].append(log_entry)
        
        # שמירת רק 50 אחרונים
        if len(self.conflict_history["conflicts"]) > 50:
            self.conflict_history["conflicts"] = self.conflict_history["conflicts"][-50:]
        
        # עדכון דפוסים
        conflict_type = conflict_data.get("conflict_type")
        if conflict_type:
            if conflict_type not in self.conflict_history["patterns"]:
                self.conflict_history["patterns"][conflict_type] = 0
            self.conflict_history["patterns"][conflict_type] += 1
        
        self._save_history()
        print(f"⚔️ Internal Conflict: {conflict_category} - {conflict_type}")
    
    def get_conflict_stats(self):
        """מחזיר סטטיסטיקה על קונפליקטים"""
        return {
            "total_conflicts": len(self.conflict_history["conflicts"]),
            "patterns": self.conflict_history["patterns"],
            "recent_conflicts": self.conflict_history["conflicts"][-5:]
        }
    
    def format_challenge_response(self, challenge_data, base_response):
        """
        מעצב תגובה שכוללת אתגור.
        
        Args:
            challenge_data (dict): נתוני האתגור
            base_response (str): התגובה הבסיסית
            
        Returns:
            str: תגובה מעוצבת עם האתגור
        """
        challenge_level = challenge_data.get("challenge_level", "gentle")
        alternative = challenge_data.get("alternative_suggestion", "")
        
        if challenge_level == "strong":
            # אתגור חזק - ישיר לעניין
            return f"{alternative}\n\n{base_response}" if base_response else alternative
        else:
            # אתגור עדין - מוסיף נקודה לתשומת לב
            return f"{base_response}\n\n(שים לב: {alternative})"

# יצירת מופע יחיד
internal_conflict = InternalConflict()