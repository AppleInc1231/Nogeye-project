# backend/verification.py

import json
import os
from datetime import datetime, timedelta
from beliefs import beliefs_system
from user_model import user_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
VERIFICATION_LOG_PATH = os.path.join(DATA_DIR, "verification_log.json")

class VerificationEngine:
    """
    מנוע אימות האמונות של Nog - "החוקר הפנימי".
    
    תפקיד: לבדוק האם האמונות שנוצרו אכן נכונות במציאות.
    
    Process:
    1. בוחר אמונה לאימות (בעדיפות: אמונות לא בטוחות)
    2. אוסף ראיות מהמציאות (user_model, התנהגות אמיתית)
    3. משווה בין תחזית למציאות
    4. מעדכן confidence בהתאם
    
    זה מה שהופך את Nog מ"מניח" ל"יודע".
    """
    
    def __init__(self):
        self.verification_log = self.load_log()
    
    def load_log(self):
        """טוען לוג אימותים"""
        if os.path.exists(VERIFICATION_LOG_PATH):
            try:
                with open(VERIFICATION_LOG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"verifications": [], "last_verification": None}
        return {"verifications": [], "last_verification": None}
    
    def save_log(self):
        """שומר לוג"""
        try:
            with open(VERIFICATION_LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.verification_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving verification log: {e}")
    
    def verify_belief(self, category, key):
        """
        מאמת אמונה ספציפית.
        
        Args:
            category (str): "about_user", "about_world", "causal_models"
            key (str): מזהה האמונה
        
        Returns:
            dict: {
                "verified": bool,
                "confidence_change": float,
                "evidence": str,
                "reasoning": str
            }
        """
        
        belief = beliefs_system.get_belief(category, key)
        if not belief:
            return {"verified": False, "error": "Belief not found"}
        
        print(f"🔍 Verifying: {belief['statement']}")
        
        result = {
            "belief_key": key,
            "belief_statement": belief["statement"],
            "verified": False,
            "confidence_before": belief["confidence"],
            "confidence_after": belief["confidence"],
            "confidence_change": 0.0,
            "evidence": "",
            "reasoning": "",
            "timestamp": datetime.now().isoformat()
        }
        
        # === לוגיקת אימות לפי סוג האמונה ===
        
        # אמונות על המשתמש
        if category == "about_user":
            result = self._verify_user_belief(key, belief, result)
        
        # אמונות על העולם
        elif category == "about_world":
            result = self._verify_world_belief(key, belief, result)
        
        # מודלים סיבתיים
        elif category == "causal_models":
            result = self._verify_causal_belief(key, belief, result)
        
        # עדכון האמונה במערכת
        if result["verified"]:
            beliefs_system.update_belief(
                category, 
                key, 
                evidence_type="for", 
                confidence_delta=result["confidence_change"]
            )
        else:
            beliefs_system.update_belief(
                category, 
                key, 
                evidence_type="against", 
                confidence_delta=result["confidence_change"]
            )
        
        # שמירה בלוג
        self.verification_log["verifications"].append(result)
        self.verification_log["last_verification"] = datetime.now().isoformat()
        self.save_log()
        
        print(f"{'✅' if result['verified'] else '❌'} Verification: {result['reasoning']}")
        
        return result
    
    def _verify_user_belief(self, key, belief, result):
        """
        אימות אמונה על המשתמש (בעזרת User Model).
        
        Examples:
            - "works_at_night" → בדיקה ב-user_model.patterns.productive_hours
            - "distracted_by_bitcoin" → בדיקה ב-user_model.distraction_triggers
        """
        
        statement = belief["statement"].lower()
        
        # אמונה: מאור עובד בלילה
        if "night" in statement or "לילה" in statement:
            user_data = user_model.data
            late_night_conf = user_data["patterns"]["productive_hours"].get("late_night", {}).get("confidence", 0)
            
            if late_night_conf > 0.7:
                result["verified"] = True
                result["confidence_change"] = 0.15
                result["evidence"] = f"User Model shows late_night confidence: {late_night_conf:.0%}"
                result["reasoning"] = "User consistently works late (evidence from pattern learning)"
            else:
                result["verified"] = False
                result["confidence_change"] = -0.1
                result["evidence"] = f"User Model shows late_night confidence: {late_night_conf:.0%}"
                result["reasoning"] = "No strong evidence for late night work"
        
        # אמונה: מאור מוסח על ידי ביטקוין
        elif "bitcoin" in statement or "distract" in statement:
            user_data = user_model.data
            btc_distraction = user_data["patterns"]["distraction_triggers"].get("bitcoin_price", {})
            count = btc_distraction.get("count", 0)
            severity = btc_distraction.get("severity", "unknown")
            
            if count > 5 and severity in ["medium", "high"]:
                result["verified"] = True
                result["confidence_change"] = 0.2
                result["evidence"] = f"Bitcoin distraction observed {count} times, severity: {severity}"
                result["reasoning"] = "Strong pattern of Bitcoin price checking"
            else:
                result["verified"] = False
                result["confidence_change"] = -0.05
                result["evidence"] = f"Bitcoin distraction only {count} times"
                result["reasoning"] = "Insufficient evidence for distraction pattern"
        
        # אמונה: מאור early riser
        elif "early" in statement or "morning" in statement:
            user_data = user_model.data
            morning_conf = user_data["patterns"]["productive_hours"].get("morning", {}).get("confidence", 0)
            early_count = user_data["behavioral_observations"].get("early_riser", 0)
            
            if morning_conf > 0.6 or early_count > 5:
                result["verified"] = True
                result["confidence_change"] = 0.1
                result["evidence"] = f"Morning confidence: {morning_conf:.0%}, early count: {early_count}"
                result["reasoning"] = "User shows morning productivity"
            else:
                result["verified"] = False
                result["confidence_change"] = -0.15
                result["evidence"] = f"Morning confidence: {morning_conf:.0%}"
                result["reasoning"] = "User not observed as early riser"
        
        # ברירת מחדל: לא יכול לאמת
        else:
            result["verified"] = None
            result["confidence_change"] = 0.0
            result["evidence"] = "No verification method available"
            result["reasoning"] = "Cannot verify this belief type yet"
        
        result["confidence_after"] = belief["confidence"] + result["confidence_change"]
        return result
    
    def _verify_world_belief(self, key, belief, result):
        """
        אימות אמונה כללית על העולם.
        
        זה יותר קשה כי צריך מקורות חיצוניים, אז בינתיים נשווה למה שנלמד על המשתמש.
        """
        
        statement = belief["statement"].lower()
        
        # אמונה: "אנשים פרודוקטיביים בבוקר"
        if "morning" in statement and "productive" in statement:
            # נבדוק האם המשתמש הספציפי שלנו מתאים לזה
            user_data = user_model.data
            morning_conf = user_data["patterns"]["productive_hours"].get("morning", {}).get("confidence", 0)
            late_night_conf = user_data["patterns"]["productive_hours"].get("late_night", {}).get("confidence", 0)
            
            if morning_conf > late_night_conf:
                result["verified"] = True
                result["confidence_change"] = 0.1
                result["evidence"] = f"User supports this: morning {morning_conf:.0%} > night {late_night_conf:.0%}"
                result["reasoning"] = "User data confirms general belief"
            else:
                result["verified"] = False
                result["confidence_change"] = -0.15
                result["evidence"] = f"User contradicts: night {late_night_conf:.0%} > morning {morning_conf:.0%}"
                result["reasoning"] = "User is counter-example to general belief"
        
        else:
            result["verified"] = None
            result["confidence_change"] = 0.0
            result["evidence"] = "World beliefs require external data sources"
            result["reasoning"] = "Cannot verify world belief without external info"
        
        result["confidence_after"] = belief["confidence"] + result["confidence_change"]
        return result
    
    def _verify_causal_belief(self, key, belief, result):
        """
        אימות מודל סיבתי: X גורם ל-Y.
        
        צריך לבדוק האם יש קורלציה בין X ל-Y בפועל.
        """
        
        # בינתיים לא מיושם - זה דורש ניתוח סטטיסטי של היסטוריה
        result["verified"] = None
        result["confidence_change"] = 0.0
        result["evidence"] = "Causal verification not yet implemented"
        result["reasoning"] = "Need more data and statistical analysis"
        result["confidence_after"] = belief["confidence"]
        
        return result
    
    def auto_verify_uncertain_beliefs(self, max_to_verify=3):
        """
        אוטומטית מאמת אמונות לא בטוחות.
        
        Args:
            max_to_verify (int): מספר מקסימלי של אמונות לאמת בריצה
        
        Returns:
            list של תוצאות
        """
        
        uncertain = beliefs_system.get_uncertain_beliefs(max_confidence=0.6)
        
        if not uncertain:
            print("✅ No uncertain beliefs to verify")
            return []
        
        # ממיין לפי עדכון אחרון (הכי ישנות קודם)
        uncertain.sort(key=lambda x: x["belief"].get("last_updated", ""))
        
        results = []
        
        for i, item in enumerate(uncertain[:max_to_verify]):
            category = item["category"]
            key = item["key"]
            
            print(f"\n🔍 Verification {i+1}/{min(max_to_verify, len(uncertain))}")
            result = self.verify_belief(category, key)
            results.append(result)
        
        return results
    
    def get_verification_summary(self):
        """
        מחזיר סיכום אימותים לשימוש ב-context.
        
        Returns:
            str: טקסט מעוצב
        """
        
        recent = self.verification_log["verifications"][-5:]  # 5 אחרונות
        
        if not recent:
            return "VERIFICATION STATUS: No verifications yet"
        
        summary = "RECENT VERIFICATIONS:\n"
        summary += "═" * 60 + "\n"
        
        for v in recent:
            status = "✓" if v["verified"] else "✗"
            conf_change = v["confidence_change"]
            summary += f"{status} {v['belief_statement']}\n"
            summary += f"   → {v['reasoning']} (Δ confidence: {conf_change:+.0%})\n"
        
        return summary

# יצירת מופע גלובלי
verification_engine = VerificationEngine()
