# backend/intervention_logic.py

import json
import os
from datetime import datetime, timedelta
from user_model import user_model
from beliefs import beliefs_system
from goals import goal_manager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
INTERVENTIONS_PATH = os.path.join(DATA_DIR, "interventions.json")

class InterventionLogic:
    """
    לוגיקת התערבות - Nog מזהה בעיות ומתערב באופן אקטיבי.
    
    זה מה שהופך את Nog מ"עוזר" ל"שותף אקטיבי שדואג".
    
    Intervention Types:
    1. **Stuck Detection** - מזהה שהמשתמש תקוע
    2. **Procrastination Alert** - מזהה דחיינות
    3. **Pattern Break** - מזהה שבירת דפוסים טובים
    4. **Energy Management** - מתערב כשאנרגיה נמוכה
    5. **Goal Drift** - מזהה סטייה ממטרות
    
    Examples:
    - "רואה שאתה מנסה לפתור את זה 40 דקות - בוא אעזור"
    - "אתה אמור לעבוד על X אבל דוחה כבר 3 ימים - מה קורה?"
    - "האנרגיה שלך נמוכה - מה דעתך להפסיק ולהמשיך מחר?"
    """
    
    def __init__(self):
        self.interventions_log = self.load_log()
        self.active_monitors = {}  # מעקב אחר סיטואציות פעילות
        
        # הגדרות סף להתערבות
        self.thresholds = {
            "stuck_duration_minutes": 30,
            "procrastination_days": 2,
            "energy_critical": 0.2,
            "repeated_failure_count": 3
        }
    
    def load_log(self):
        if os.path.exists(INTERVENTIONS_PATH):
            try:
                with open(INTERVENTIONS_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"interventions": [], "success_rate": 0.0}
        return {"interventions": [], "success_rate": 0.0}
    
    def save_log(self):
        try:
            with open(INTERVENTIONS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.interventions_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving interventions: {e}")
    
    def should_intervene(self, context):
        """
        מחליט האם להתערב עכשיו.
        """
        
        interventions = []
        
        # בדיקה 1: Stuck Detection
        stuck_check = self._check_stuck(context)
        if stuck_check:
            interventions.append(stuck_check)
        
        # בדיקה 2: Procrastination
        procrastination_check = self._check_procrastination()
        if procrastination_check:
            interventions.append(procrastination_check)
        
        # בדיקה 3: Energy Critical
        energy_check = self._check_energy_critical()
        if energy_check:
            interventions.append(energy_check)
        
        if interventions:
            urgency_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            interventions.sort(key=lambda x: urgency_order.get(x["urgency"], 0), reverse=True)
            
            best = interventions[0]
            best["should_intervene"] = True
            return best
        
        return {
            "should_intervene": False,
            "intervention_type": None,
            "message": None,
            "urgency": "none",
            "reasoning": "No intervention needed"
        }
    
    def _check_stuck(self, context):
        """מזהה תקיעה"""
        current_task = context.get("current_task")
        task_duration = context.get("task_duration_minutes", 0)
        
        if not current_task:
            return None
        
        if task_duration > self.thresholds["stuck_duration_minutes"]:
            failed_attempts = context.get("failed_attempts", 0)
            
            if failed_attempts >= self.thresholds["repeated_failure_count"]:
                return {
                    "intervention_type": "stuck_critical",
                    "message": f"רואה שאתה מנסה לפתור את '{current_task}' כבר {task_duration} דקות - בוא אעזור",
                    "urgency": "high",
                    "reasoning": f"User stuck {task_duration} min with {failed_attempts} failures"
                }
            else:
                return {
                    "intervention_type": "stuck_moderate",
                    "message": f"אתה כבר {task_duration} דקות על '{current_task}' - אולי גישה אחרת?",
                    "urgency": "medium",
                    "reasoning": f"User on task {task_duration} min"
                }
        
        return None
    
    def _check_procrastination(self):
        """מזהה דחיינות"""
        overdue = goal_manager.get_overdue_commitments()
        
        if overdue:
            most_overdue = max(overdue, key=lambda x: x.get("days_overdue", 0))
            days = most_overdue.get("days_overdue", 0)
            
            if days >= self.thresholds["procrastination_days"]:
                return {
                    "intervention_type": "procrastination",
                    "message": f"אתה אמור {most_overdue['promise']} כבר {days} ימים - מה עוצר אותך?",
                    "urgency": "medium" if days < 7 else "high",
                    "reasoning": f"Commitment {days} days overdue"
                }
        
        return None
    
    def _check_energy_critical(self):
        """מתערב כשאנרגיה קריטית"""
        user_state = user_model.predict_current_state()
        
        if user_state["energy_level"] == "low":
            current_hour = datetime.now().hour
            
            if not (23 <= current_hour or current_hour < 7):
                return {
                    "intervention_type": "energy_critical",
                    "message": "רואה שהאנרגיה שלך נמוכה - אולי כדאי להפסיק לפני שתשרוף?",
                    "urgency": "medium",
                    "reasoning": f"Low energy at {current_hour}:00"
                }
        
        return None
    
    def log_intervention(self, intervention_type, message, user_response, was_helpful):
        """רושם התערבות"""
        self.interventions_log["interventions"].append({
            "timestamp": datetime.now().isoformat(),
            "type": intervention_type,
            "message": message,
            "user_response": user_response[:100],
            "was_helpful": was_helpful
        })
        
        total = len(self.interventions_log["interventions"])
        successful = sum(1 for i in self.interventions_log["interventions"] if i.get("was_helpful"))
        self.interventions_log["success_rate"] = successful / total if total > 0 else 0.0
        
        self.save_log()
        
        print(f"🚨 Intervention Success: {self.interventions_log['success_rate']:.0%}")

# יצירת מופע גלובלי
intervention_logic = InterventionLogic()
