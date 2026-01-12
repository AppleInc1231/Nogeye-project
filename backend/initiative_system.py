# backend/initiative_system.py

import json
import os
from datetime import datetime, timedelta
from user_model import user_model
from beliefs import beliefs_system
from goals import goal_manager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
INITIATIVE_LOG_PATH = os.path.join(DATA_DIR, "initiative_log.json")

class InitiativeSystem:
    """
    מערכת יוזמה - Nog מתחיל שיחות מעצמו.
    
    זה מה שהופך את Nog מ"מגיב" ל"אקטיבי".
    
    Features:
    - Timing: יודע מתי להתחיל שיחה (לא להפריע)
    - Topic Selection: בוחר נושא רלוונטי
    - Value Assessment: מעריך האם השיחה באמת תעזור
    - Frequency Control: לא מציק יותר מדי
    
    Examples:
    - "ראיתי שיש לך פגישה בעוד שעה - צריך עזרה בהכנה?"
    - "אתה לא עבדת על הפרויקט 3 ימים - מה קורה?"
    - "זו השעה הטובה שלך - בוא נעשה משהו פרודוקטיבי"
    """
    
    def __init__(self):
        self.log = self.load_log()
        self.last_initiative = None
        self.cooldown_minutes = 60  # מינימום 60 דקות בין יוזמות
    
    def load_log(self):
        if os.path.exists(INITIATIVE_LOG_PATH):
            try:
                with open(INITIATIVE_LOG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"initiatives": [], "success_rate": 0.0}
        return {"initiatives": [], "success_rate": 0.0}
    
    def save_log(self):
        try:
            with open(INITIATIVE_LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving initiative log: {e}")
    
    def should_initiate(self):
        """
        מחליט האם להתחיל שיחה עכשיו.
        
        Returns:
            dict: {
                "should_initiate": bool,
                "reason": str,
                "topic": str or None,
                "confidence": float
            }
        """
        
        # בדיקה 1: Cooldown - האם עבר מספיק זמן מהיוזמה האחרונה?
        if self.last_initiative:
            time_since = (datetime.now() - datetime.fromisoformat(self.last_initiative)).total_seconds() / 60
            if time_since < self.cooldown_minutes:
                return {
                    "should_initiate": False,
                    "reason": f"Cooldown active ({time_since:.0f}/{self.cooldown_minutes} min)",
                    "topic": None,
                    "confidence": 0.0
                }
        
        # בדיקה 2: User State - האם המשתמש במצב מתאים?
        user_state = user_model.predict_current_state()
        
        if user_state["productivity_potential"] < 0.3:
            return {
                "should_initiate": False,
                "reason": f"User in low productivity state ({user_state['energy_level']})",
                "topic": None,
                "confidence": 0.0
            }
        
        # בדיקה 3: זיהוי סיטואציות שדורשות יוזמה
        initiatives = []
        
        # 3.1: התחייבות קרובה
        upcoming_commitments = self._check_upcoming_commitments()
        if upcoming_commitments:
            initiatives.append({
                "type": "commitment_reminder",
                "topic": upcoming_commitments,
                "confidence": 0.9,
                "value": "high"
            })
        
        # 3.2: Peak time ללא פעילות
        if user_state["productivity_potential"] > 0.7:
            initiatives.append({
                "type": "peak_time_nudge",
                "topic": "זו השעה הטובה שלך - בוא נעשה משהו פרודוקטיבי",
                "confidence": 0.7,
                "value": "medium"
            })
        
        # 3.3: מטרה נזנחת
        abandoned_goals = self._check_abandoned_goals()
        if abandoned_goals:
            initiatives.append({
                "type": "goal_check_in",
                "topic": abandoned_goals,
                "confidence": 0.6,
                "value": "medium"
            })
        
        # 3.4: דפוס שבור (למשל: לא עבד 3 ימים רצוף)
        broken_patterns = self._check_broken_patterns()
        if broken_patterns:
            initiatives.append({
                "type": "pattern_concern",
                "topic": broken_patterns,
                "confidence": 0.5,
                "value": "low"
            })
        
        # בחירת היוזמה הטובה ביותר
        if initiatives:
            # ממיין לפי ערך וביטחון
            initiatives.sort(key=lambda x: (self._value_to_score(x["value"]), x["confidence"]), reverse=True)
            best = initiatives[0]
            
            return {
                "should_initiate": True,
                "reason": f"Initiative: {best['type']}",
                "topic": best["topic"],
                "confidence": best["confidence"]
            }
        
        return {
            "should_initiate": False,
            "reason": "No valuable initiative identified",
            "topic": None,
            "confidence": 0.0
        }
    
    def generate_opening(self, topic, initiative_type):
        """
        מייצר פתיחת שיחה טבעית לפי הנושא.
        
        Args:
            topic (str): הנושא
            initiative_type (str): סוג היוזמה
        
        Returns:
            str: פתיחה טבעית
        """
        
        openings = {
            "commitment_reminder": [
                f"היי, שמתי לב ש{topic} - צריך עזרה?",
                f"רגע, {topic} - הכול בשליטה?",
                f"{topic} - אני כאן אם צריך משהו"
            ],
            "peak_time_nudge": [
                "זו השעה הטובה שלך - מה דעתך לנצל?",
                "אתה במצב מנטלי מעולה עכשיו - יש משהו שכדאי לתקוף?",
                "רואה שאתה ב-peak time - בוא נעשה משהו משמעותי"
            ],
            "goal_check_in": [
                f"אז מה קורה עם {topic}? לא שמעתי עליו כבר זמן",
                f"שמתי לב שלא עבדת על {topic} מזה זמן - הכול בסדר?",
                f"היי, {topic} - עדיין רלוונטי או משהו השתנה?"
            ],
            "pattern_concern": [
                f"רואה ש{topic} - מה קורה?",
                f"שמתי לב ש{topic} - צריך לדבר על זה?",
                f"{topic} - אולי אני יכול לעזור?"
            ]
        }
        
        import random
        return random.choice(openings.get(initiative_type, [f"מה קורה? שמתי לב ש{topic}"]))
    
    def log_initiative(self, topic, user_response, was_helpful):
        """
        רושם יוזמה ומעדכן שיעור הצלחה.
        
        Args:
            topic (str): הנושא
            user_response (str): מה המשתמש ענה
            was_helpful (bool): האם זה עזר
        """
        
        self.log["initiatives"].append({
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "user_response": user_response[:100],
            "was_helpful": was_helpful
        })
        
        # עדכון שיעור הצלחה
        total = len(self.log["initiatives"])
        successful = sum(1 for i in self.log["initiatives"] if i.get("was_helpful"))
        self.log["success_rate"] = successful / total if total > 0 else 0.0
        
        # עדכון cooldown לפי הצלחה
        if not was_helpful:
            # אם לא עזר - הגדל cooldown
            self.cooldown_minutes = min(180, self.cooldown_minutes + 15)
        else:
            # אם עזר - הקטן cooldown
            self.cooldown_minutes = max(30, self.cooldown_minutes - 10)
        
        self.last_initiative = datetime.now().isoformat()
        self.save_log()
        
        print(f"📊 Initiative Success Rate: {self.log['success_rate']:.0%} | Cooldown: {self.cooldown_minutes}min")
    
    def _check_upcoming_commitments(self):
        """בודק אם יש התחייבויות קרובות"""
        pending = goal_manager.get_pending_commitments()
        
        for commitment in pending:
            deadline = datetime.fromisoformat(commitment["deadline"])
            time_until = (deadline - datetime.now()).total_seconds() / 60
            
            # התחייבות בעוד 30-60 דקות
            if 30 <= time_until <= 60:
                return f"יש לך התחייבות בעוד {int(time_until)} דקות: {commitment['promise']}"
        
        return None
    
    def _check_abandoned_goals(self):
        """בודק אם יש מטרות נזנחות"""
        # בינתיים מחזיר None - צריך ממשק למטרות
        return None
    
    def _check_broken_patterns(self):
        """בודק אם דפוסים נשברו"""
        user_data = user_model.data
        
        # בדיקה פשוטה: האם המשתמש לא עבד בשעות הפרודוקטיביות שלו
        # זה דורש מעקב אחר פעילות - בינתיים מחזיר None
        return None
    
    def _value_to_score(self, value):
        """ממיר ערך למספר"""
        mapping = {"high": 3, "medium": 2, "low": 1}
        return mapping.get(value, 0)

# יצירת מופע גלובלי
initiative_system = InitiativeSystem()
