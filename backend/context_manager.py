"""
Context Manager - מנהל ההקשר של Nog
=====================================

תפקיד: לעקוב אחר מה קורה כרגע, במה Nog עסוק, ומה ההקשר הכללי.
"""

import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
CONTEXT_PATH = os.path.join(DATA_DIR, "current_context.json")

class ContextManager:
    """
    עוקב אחר ההקשר הנוכחי:
    - מה המשימה/תהליך הנוכחי
    - מתי הייתה האינטראקציה האחרונה
    - האם Nog באמצע משהו
    """
    
    def __init__(self):
        self.load_context()
        
    def load_context(self):
        """טעינת ההקשר הנוכחי"""
        if os.path.exists(CONTEXT_PATH):
            try:
                with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
                    self.context = json.load(f)
            except:
                self.context = self._default_context()
        else:
            self.context = self._default_context()
    
    def save_context(self):
        """שמירת ההקשר"""
        try:
            with open(CONTEXT_PATH, "w", encoding="utf-8") as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Context save error: {e}")
    
    def _default_context(self):
        """ההקשר ברירת המחדל"""
        return {
            "current_task": None,
            "in_process": False,
            "last_interaction": None,
            "conversation_depth": 0,  # כמה תגובות רצופות
            "last_topic": None,
            "waiting_for_response": False
        }
    
    def start_task(self, task_name):
        """
        מתחיל משימה חדשה.
        
        Args:
            task_name (str): שם המשימה (למשל: "searching web", "generating image")
        """
        self.context["current_task"] = task_name
        self.context["in_process"] = True
        self.save_context()
        print(f"📝 Context: Started task '{task_name}'")
    
    def end_task(self):
        """מסיים את המשימה הנוכחית"""
        if self.context["current_task"]:
            print(f"✅ Context: Finished task '{self.context['current_task']}'")
        self.context["current_task"] = None
        self.context["in_process"] = False
        self.save_context()
    
    def update_interaction(self, user_said_something=True):
        """
        מעדכן שהייתה אינטראקציה.
        
        Args:
            user_said_something (bool): האם המשתמש אמר משהו (True) או Nog יזם (False)
        """
        now = datetime.now().isoformat()
        self.context["last_interaction"] = now
        
        if user_said_something:
            self.context["conversation_depth"] += 1
        
        self.save_context()
    
    def reset_conversation(self):
        """
        מאפס את עומק השיחה (אם עבר זמן מסוים ללא אינטראקציה)
        """
        if self.context["last_interaction"]:
            last_time = datetime.fromisoformat(self.context["last_interaction"])
            if datetime.now() - last_time > timedelta(minutes=5):
                self.context["conversation_depth"] = 0
                self.save_context()
    
    def set_topic(self, topic):
        """
        מגדיר את הנושא הנוכחי של השיחה.
        
        Args:
            topic (str): הנושא (למשל: "bitcoin price", "weather")
        """
        self.context["last_topic"] = topic
        self.save_context()
    
    def get_context(self):
        """
        מחזיר את ההקשר הנוכחי.
        
        Returns:
            dict: ההקשר המלא
        """
        # בדיקה אוטומטית: האם עבר זמן רב
        self.reset_conversation()
        return self.context.copy()
    
    def is_busy(self):
        """
        בדיקה האם Nog עסוק כרגע.
        
        Returns:
            bool: True אם באמצע משימה
        """
        return self.context.get("in_process", False)
    
    def get_conversation_depth(self):
        """
        כמה תגובות רצופות היו.
        
        Returns:
            int: מספר תגובות רצופות
        """
        return self.context.get("conversation_depth", 0)

# יצירת מופע יחיד
context_manager = ContextManager()