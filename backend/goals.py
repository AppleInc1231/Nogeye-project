# backend/goals.py

import json
import os
from datetime import datetime, timedelta
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
GOALS_PATH = os.path.join(DATA_DIR, "goals.json")

class GoalManager:
    """
    מנהל את המטרות וההתחייבויות של Nog.
    לא רק reactive - proactive עם כיוון.
    
    ההבדל בין "מערכת" ל"ישות": 
    ישות זוכרת מה היא הבטיחה ופועלת לפי זה.
    """
    
    def __init__(self):
        self.data = self.load_or_create()
    
    def load_or_create(self):
        """טען או צור קובץ חדש"""
        if os.path.exists(GOALS_PATH):
            try:
                with open(GOALS_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_initial_data()
        else:
            return self.create_initial_data()
    
    def create_initial_data(self):
        """נתונים ראשוניים"""
        return {
            "system_goals": [
                {
                    "id": str(uuid.uuid4()),
                    "goal": "לעזור למשתמש להיות יותר פרודוקטיבי",
                    "type": "ongoing",
                    "priority": "high",
                    "measurable": "משתמש משלים משימות",
                    "status": "active"
                },
                {
                    "id": str(uuid.uuid4()),
                    "goal": "לבנות אמון דרך עקביות",
                    "type": "ongoing",
                    "priority": "high",
                    "measurable": "אפס התחייבויות שבורות",
                    "status": "active"
                },
                {
                    "id": str(uuid.uuid4()),
                    "goal": "ללמוד את הדפוסים של המשתמש",
                    "type": "ongoing",
                    "priority": "medium",
                    "measurable": "דיוק של תחזיות",
                    "status": "active"
                }
            ],
            "user_goals": [],  # מטרות שהמשתמש מגדיר במפורש
            "active_focus": None,  # על מה אני ממוקד עכשיו
            "commitments": []  # התחייבויות פעילות
        }
    
    def save(self):
        """שמירה לדיסק"""
        try:
            with open(GOALS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving goals: {e}")
    
    def add_commitment(self, promise, deadline, context=""):
        """
        המשתמש ביקש שאעשה משהו עד זמן מסוים.
        אני חייב לזכור ולמלא את זה.
        
        Args:
            promise (str): מה הבטחתי
            deadline (datetime or str): מתי
            context (str): הקשר נוסף
        
        Returns:
            str: commitment ID
        """
        
        # המרה לפורמט אחיד
        if isinstance(deadline, datetime):
            deadline_str = deadline.isoformat()
        elif isinstance(deadline, str):
            deadline_str = deadline
        else:
            deadline_str = datetime.now().isoformat()
        
        commitment = {
            "id": str(uuid.uuid4()),
            "promise": promise,
            "deadline": deadline_str,
            "context": context,
            "status": "pending",  # pending / fulfilled / broken
            "created": datetime.now().isoformat(),
            "fulfilled_at": None
        }
        
        self.data["commitments"].append(commitment)
        self.save()
        
        print(f"💍 COMMITMENT: {promise} by {deadline}")
        return commitment["id"]
    
    def check_due_commitments(self):
        """
        נקרא על ידי proactive_loop.
        מחזיר התחייבויות שמגיע להן הזמן.
        
        Returns:
            list: רשימת commitments שצריך למלא עכשיו
        """
        now = datetime.now()
        due = []
        
        for c in self.data["commitments"]:
            if c["status"] != "pending":
                continue
            
            try:
                deadline = datetime.fromisoformat(c["deadline"])
                
                # מגיע אם בטווח של 5 דקות
                time_diff = (deadline - now).total_seconds()
                
                if 0 <= time_diff <= 300:  # בין 0 ל-5 דקות
                    due.append(c)
            except:
                continue
        
        return due
    
    def fulfill_commitment(self, commitment_id):
        """
        סמן התחייבות כממולאת.
        
        Args:
            commitment_id (str): ID של ההתחייבות
        
        Returns:
            bool: הצלחה/כישלון
        """
        for c in self.data["commitments"]:
            if c["id"] == commitment_id:
                c["status"] = "fulfilled"
                c["fulfilled_at"] = datetime.now().isoformat()
                self.save()
                print(f"✅ FULFILLED: {c['promise']}")
                return True
        return False
    
    def get_broken_commitments(self):
        """
        התחייבויות שעבר להן הזמן בלי מילוי.
        זה רע מאוד - צריך להימנע מזה!
        
        Returns:
            list: התחייבויות שבורות
        """
        now = datetime.now()
        broken = []
        
        for c in self.data["commitments"]:
            if c["status"] == "pending":
                try:
                    deadline = datetime.fromisoformat(c["deadline"])
                    if deadline < now:
                        # עבר הזמן ולא מילאנו
                        c["status"] = "broken"
                        broken.append(c)
                except:
                    continue
        
        if broken:
            self.save()
            print(f"⚠️ BROKEN COMMITMENTS: {len(broken)}")
        
        return broken
    
    def set_active_focus(self, goal):
        """
        מה אני ממוקד עליו כרגע.
        
        Args:
            goal (str): תיאור המטרה הפעילה
        """
        self.data["active_focus"] = {
            "goal": goal,
            "started": datetime.now().isoformat()
        }
        self.save()
        print(f"🎯 FOCUS: {goal}")
    
    def get_active_focus(self):
        """
        מה אני ממוקד עליו עכשיו?
        
        Returns:
            dict or None: המטרה הפעילה
        """
        return self.data["active_focus"]
    
    def clear_active_focus(self):
        """סיימתי עם המטרה הנוכחית"""
        self.data["active_focus"] = None
        self.save()
    
    def get_all_commitments(self):
        """כל ההתחייבויות (לצורך דיבאג)"""
        return self.data["commitments"]
    
    def get_pending_commitments_count(self):
        """כמה התחייבויות עדיין ממתינות"""
        return len([c for c in self.data["commitments"] if c["status"] == "pending"])

# יצירת מופע גלובלי
goal_manager = GoalManager()