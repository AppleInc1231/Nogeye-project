# backend/user_model.py

import json
import os
from datetime import datetime, time
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
USER_MODEL_PATH = os.path.join(DATA_DIR, "user_model.json")

class UserModel:
    """
    מודל עמוק של המשתמש - לומד דפוסים, מתחזה מצבים, מסיק צרכים.
    
    זה מה שהופך את Nog מ"עוזר" ל"מישהו שמכיר אותך".
    
    Features:
    - Pattern Learning: מתי אתה פרודוקטיבי, מתי עייף, מה מפריע
    - State Prediction: מה המצב שלך עכשיו (ללא שאתה תגיד)
    - Need Inference: מה אתה צריך לפני שאתה מבין
    """
    
    def __init__(self):
        self.data = self.load_or_create()
    
    def load_or_create(self):
        if os.path.exists(USER_MODEL_PATH):
            try:
                with open(USER_MODEL_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_initial_model()
        else:
            return self.create_initial_model()
    
    def create_initial_model(self):
        """יצירת מודל ראשוני"""
        return {
            "user_info": {
                "name": "Maor",
                "location": "Dallas, TX",
                "timezone": "America/Chicago",
                "primary_language": "Hebrew",
                "work_type": "Entrepreneur/Developer"
            },
            
            "patterns": {
                "productive_hours": {
                    "morning": {"start": "09:00", "end": "12:00", "confidence": 0.3},
                    "evening": {"start": "20:00", "end": "23:00", "confidence": 0.5},
                    "late_night": {"start": "23:00", "end": "02:00", "confidence": 0.7}
                },
                
                "energy_dips": {
                    "post_lunch": {"time": "14:00-16:00", "severity": "medium", "observed": 0},
                    "early_morning": {"time": "06:00-08:00", "severity": "high", "observed": 0}
                },
                
                "distraction_triggers": {
                    "social_media": {"count": 0, "severity": "unknown"},
                    "news": {"count": 0, "severity": "unknown"},
                    "youtube": {"count": 0, "severity": "unknown"},
                    "bitcoin_price": {"count": 0, "severity": "medium"}
                },
                
                "peak_performance": {
                    "best_hours": [],
                    "best_days": [],
                    "flow_state_triggers": []
                }
            },
            
            "goals": {
                "stated": [],      # מטרות שהמשתמש אמר במפורש
                "inferred": []     # מטרות שהמערכת הסיקה מהתנהגות
            },
            
            "preferences": {
                "communication_style": "direct",  # או: warm, casual, formal
                "response_length": "medium",      # short, medium, long
                "humor_level": "high",            # low, medium, high
                "challenge_tolerance": "high"     # low, medium, high (כמה הוא מוכן לאתגור)
            },
            
            "behavioral_observations": {
                "works_late": 0,
                "early_riser": 0,
                "weekend_worker": 0,
                "task_switcher": 0,
                "deep_focus_sessions": 0
            },
            
            "emotional_patterns": {
                "stress_indicators": [],
                "motivation_boosters": [],
                "frustration_triggers": []
            },
            
            "last_updated": datetime.now().isoformat(),
            "observation_count": 0
        }
    
    def save(self):
        """שמירה לדיסק"""
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            with open(USER_MODEL_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving user_model: {e}")
    
    def learn_pattern(self, pattern_type, observation):
        """
        לומד דפוס חדש מתצפית.
        
        Args:
            pattern_type (str): "productive_time", "distraction", "energy", "goal"
            observation (dict): המידע שנצפה
        
        Examples:
            learn_pattern("productive_time", {"hour": 22, "task": "coding", "success": True})
            learn_pattern("distraction", {"trigger": "bitcoin_price", "duration_minutes": 15})
        """
        
        current_hour = datetime.now().hour
        
        if pattern_type == "productive_time":
            # עדכון שעות פרודוקטיביות
            if observation.get("success"):
                hour = observation.get("hour", current_hour)
                
                # סיווג לתקופת יום
                if 6 <= hour < 12:
                    period = "morning"
                elif 12 <= hour < 18:
                    period = "afternoon"
                elif 18 <= hour < 23:
                    period = "evening"
                else:
                    period = "late_night"
                
                # עדכן confidence
                if period in self.data["patterns"]["productive_hours"]:
                    current_conf = self.data["patterns"]["productive_hours"][period]["confidence"]
                    self.data["patterns"]["productive_hours"][period]["confidence"] = min(1.0, current_conf + 0.05)
        
        elif pattern_type == "distraction":
            trigger = observation.get("trigger", "unknown")
            if trigger in self.data["patterns"]["distraction_triggers"]:
                self.data["patterns"]["distraction_triggers"][trigger]["count"] += 1
                
                # עדכן חומרה לפי תדירות
                count = self.data["patterns"]["distraction_triggers"][trigger]["count"]
                if count > 10:
                    self.data["patterns"]["distraction_triggers"][trigger]["severity"] = "high"
                elif count > 5:
                    self.data["patterns"]["distraction_triggers"][trigger]["severity"] = "medium"
                else:
                    self.data["patterns"]["distraction_triggers"][trigger]["severity"] = "low"
        
        elif pattern_type == "energy_dip":
            time_str = observation.get("time", f"{current_hour:02d}:00")
            severity = observation.get("severity", "medium")
            
            # חפש או צור entry
            found = False
            for key, value in self.data["patterns"]["energy_dips"].items():
                if time_str in value["time"]:
                    value["observed"] += 1
                    found = True
                    break
            
            if not found:
                # צור חדש
                self.data["patterns"]["energy_dips"][f"dip_{len(self.data['patterns']['energy_dips'])}"] = {
                    "time": time_str,
                    "severity": severity,
                    "observed": 1
                }
        
        elif pattern_type == "goal_inferred":
            goal_text = observation.get("goal")
            if goal_text and goal_text not in self.data["goals"]["inferred"]:
                self.data["goals"]["inferred"].append(goal_text)
        
        self.data["observation_count"] += 1
        self.save()
        print(f"📊 Learned: {pattern_type} - {observation}")
    
    def predict_current_state(self):
        """
        מנבא מה המצב הנוכחי של המשתמש בלי שהוא אמר.
        
        Returns:
            dict: {
                "energy_level": "high/medium/low",
                "productivity_potential": 0.0-1.0,
                "likely_mood": "focused/tired/distracted",
                "recommended_approach": "challenging/supportive/gentle"
            }
        """
        
        now = datetime.now()
        current_hour = now.hour
        current_day = now.strftime("%A")
        
        prediction = {
            "energy_level": "medium",
            "productivity_potential": 0.5,
            "likely_mood": "neutral",
            "recommended_approach": "balanced",
            "reasoning": []
        }
        
        # בדיקה 1: האם זו שעת peak?
        for period, times in self.data["patterns"]["productive_hours"].items():
            if times["confidence"] > 0.6:
                start_h = int(times["start"].split(":")[0])
                end_h = int(times["end"].split(":")[0])
                
                # טיפול במעבר חצות
                if start_h > end_h:
                    if current_hour >= start_h or current_hour < end_h:
                        prediction["energy_level"] = "high"
                        prediction["productivity_potential"] = 0.8
                        prediction["likely_mood"] = "focused"
                        prediction["recommended_approach"] = "challenging"
                        prediction["reasoning"].append(f"Peak productive period: {period}")
                else:
                    if start_h <= current_hour < end_h:
                        prediction["energy_level"] = "high"
                        prediction["productivity_potential"] = 0.8
                        prediction["likely_mood"] = "focused"
                        prediction["recommended_approach"] = "challenging"
                        prediction["reasoning"].append(f"Peak productive period: {period}")
        
        # בדיקה 2: האם זו שעת energy dip?
        for dip_name, dip_data in self.data["patterns"]["energy_dips"].items():
            if dip_data["observed"] > 2:  # אם נצפה לפחות 3 פעמים
                time_range = dip_data["time"]
                # פרסור פשוט
                if "-" in time_range:
                    start_str, end_str = time_range.split("-")
                    start_h = int(start_str.split(":")[0])
                    end_h = int(end_str.split(":")[0])
                    
                    if start_h <= current_hour < end_h:
                        prediction["energy_level"] = "low"
                        prediction["productivity_potential"] = 0.3
                        prediction["likely_mood"] = "tired"
                        prediction["recommended_approach"] = "gentle"
                        prediction["reasoning"].append(f"Known energy dip: {dip_name}")
        
        # בדיקה 3: התנהגויות ידועות
        if self.data["behavioral_observations"]["works_late"] > 5:
            if current_hour >= 22:
                prediction["productivity_potential"] = min(1.0, prediction["productivity_potential"] + 0.2)
                prediction["reasoning"].append("User is a night owl")
        
        if self.data["behavioral_observations"]["early_riser"] > 5:
            if 6 <= current_hour < 9:
                prediction["productivity_potential"] = min(1.0, prediction["productivity_potential"] + 0.2)
                prediction["reasoning"].append("User is an early riser")
        
        return prediction
    
    def infer_need(self, context):
        """
        מסיק מה המשתמש צריך עכשיו לפי ההקשר.
        
        Args:
            context (dict): הקשר נוכחי (מה קורה, מה נאמר לאחרונה, וכו')
        
        Returns:
            str or None: המלצה מבוססת הבנה עמוקה, או None אם לא בטוח
        """
        
        state = self.predict_current_state()
        recent_activity = context.get("recent_activity", "")
        
        needs = []
        
        # אם אנרגיה נמוכה
        if state["energy_level"] == "low":
            needs.append("Suggest a break or lighter task")
        
        # אם הרבה task switching
        if self.data["behavioral_observations"]["task_switcher"] > 5:
            if "distracted" in state["likely_mood"]:
                needs.append("Encourage single focus")
        
        # אם שעת peak אבל לא מנוצל
        if state["productivity_potential"] > 0.7:
            if "idle" in recent_activity or "browsing" in recent_activity:
                needs.append("Challenge to use peak time wisely")
        
        # החזר הצורך הראשון (הכי דחוף)
        return needs[0] if needs else None
    
    def get_communication_preferences(self):
        """
        מחזיר העדפות תקשורת לשימוש ב-GPT context.
        
        Returns:
            str: תיאור טקסטואלי של העדפות
        """
        prefs = self.data["preferences"]
        
        style_desc = {
            "direct": "Be direct and to the point",
            "warm": "Be warm and encouraging",
            "casual": "Be casual and friendly",
            "formal": "Be professional and formal"
        }
        
        length_desc = {
            "short": "Keep responses very brief (1-2 sentences)",
            "medium": "Moderate response length (2-4 sentences)",
            "long": "Detailed responses when needed"
        }
        
        return f"""
USER COMMUNICATION PREFERENCES:
- Style: {style_desc.get(prefs['communication_style'], 'balanced')}
- Response Length: {length_desc.get(prefs['response_length'], 'medium')}
- Humor Level: {prefs['humor_level']}
- Challenge Tolerance: {prefs['challenge_tolerance']} (willingness to be challenged)
"""
    
    def update_goal(self, goal_text, goal_type="stated"):
        """
        מוסיף או מעדכן מטרה.
        
        Args:
            goal_text (str): תיאור המטרה
            goal_type (str): "stated" (אמר במפורש) או "inferred" (הסקנו)
        """
        if goal_type == "stated":
            if goal_text not in self.data["goals"]["stated"]:
                self.data["goals"]["stated"].append(goal_text)
        else:
            if goal_text not in self.data["goals"]["inferred"]:
                self.data["goals"]["inferred"].append(goal_text)
        
        self.save()
        print(f"🎯 Goal Updated ({goal_type}): {goal_text}")
    
    def get_summary(self):
        """
        מחזיר סיכום המודל לשימוש ב-GPT context או לדיבאג.
        
        Returns:
            str: סיכום קריא
        """
        state = self.predict_current_state()
        
        summary = f"""
USER MODEL SUMMARY:
==================

CURRENT STATE PREDICTION:
- Energy: {state['energy_level']}
- Productivity Potential: {state['productivity_potential']:.0%}
- Likely Mood: {state['likely_mood']}
- Recommended Approach: {state['recommended_approach']}
- Reasoning: {', '.join(state['reasoning']) if state['reasoning'] else 'Baseline'}

KNOWN PATTERNS:
- Works late: {'Yes' if self.data['behavioral_observations']['works_late'] > 3 else 'Unknown'}
- Early riser: {'Yes' if self.data['behavioral_observations']['early_riser'] > 3 else 'Unknown'}
- Deep focus: {'Yes' if self.data['behavioral_observations']['deep_focus_sessions'] > 3 else 'Unknown'}

GOALS:
- Stated: {len(self.data['goals']['stated'])} goals
- Inferred: {len(self.data['goals']['inferred'])} goals

OBSERVATIONS: {self.data['observation_count']} total
"""
        return summary

# יצירת מופע גלובלי
user_model = UserModel()