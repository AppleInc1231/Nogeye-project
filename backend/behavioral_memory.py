"""
Behavioral Memory - זיכרון התנהגותי
=====================================

שומר העדפות וחוקי התנהגות שנלמדו מהאינטראקציות.

דוגמאות:
- "המשתמש מעדיף תשובות קצרות"
- "אל תזכיר פגישות אלא אם נשאל"
- "דבר ישיר, בלי נימוסים"
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
BEHAVIORAL_MEMORY_PATH = os.path.join(DATA_DIR, "behavioral_memory.json")

class BehavioralMemory:
    """
    זיכרון של איך להתנהג עם המשתמש הספציפי הזה.
    """
    
    def __init__(self):
        self.load_memory()
    
    def load_memory(self):
        """טעינת הזיכרון ההתנהגותי"""
        if os.path.exists(BEHAVIORAL_MEMORY_PATH):
            try:
                with open(BEHAVIORAL_MEMORY_PATH, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except:
                self.memory = self._default_memory()
        else:
            self.memory = self._default_memory()
    
    def save_memory(self):
        """שמירת הזיכרון"""
        try:
            with open(BEHAVIORAL_MEMORY_PATH, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Behavioral memory save error: {e}")
    
    def _default_memory(self):
        """זיכרון התחלתי"""
        return {
            "communication_preferences": {
                "response_length": "normal",  # short / normal / detailed
                "formality": "casual",  # formal / casual / direct
                "explanation_level": "balanced",  # minimal / balanced / extensive
                "humor": "moderate"  # none / moderate / high
            },
            "learned_rules": [
                # דוגמה: "Always be brief when answering time-related questions"
            ],
            "do_not": [
                # דוגמה: "Don't remind about meetings unless asked"
            ],
            "conversation_patterns": {
                "typical_greeting": None,
                "preferred_topics": [],
                "avoided_topics": []
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def add_rule(self, rule_text, category="learned_rules"):
        """
        מוסיף כלל התנהגות חדש.
        
        Args:
            rule_text (str): הכלל (למשל: "Be concise in the mornings")
            category (str): "learned_rules" או "do_not"
        """
        if category not in ["learned_rules", "do_not"]:
            print(f"Invalid category: {category}")
            return
        
        # בדיקת כפילות
        if rule_text not in self.memory[category]:
            self.memory[category].append(rule_text)
            self.memory["last_updated"] = datetime.now().isoformat()
            self.save_memory()
            print(f"📝 Learned new rule: {rule_text}")
            return True
        return False
    
    def remove_rule(self, rule_text, category="learned_rules"):
        """מוחק כלל"""
        if rule_text in self.memory[category]:
            self.memory[category].remove(rule_text)
            self.save_memory()
            print(f"🗑️ Removed rule: {rule_text}")
            return True
        return False
    
    def update_preference(self, preference_type, value):
        """
        מעדכן העדפה.
        
        Args:
            preference_type (str): "response_length", "formality", etc.
            value (str): הערך החדש
        """
        if preference_type in self.memory["communication_preferences"]:
            old_value = self.memory["communication_preferences"][preference_type]
            self.memory["communication_preferences"][preference_type] = value
            self.memory["last_updated"] = datetime.now().isoformat()
            self.save_memory()
            print(f"🔄 Updated {preference_type}: {old_value} → {value}")
            return True
        return False
    
    def get_rules_for_decision(self):
        """
        מחזיר את כל החוקים בפורמט מתאים ל-Decision Core.
        
        Returns:
            dict: חוקים מסודרים
        """
        return {
            "communication_prefs": self.memory["communication_preferences"],
            "learned_rules": self.memory["learned_rules"],
            "do_not": self.memory["do_not"],
            "patterns": self.memory["conversation_patterns"]
        }
    
    def apply_to_style(self, base_style):
        """
        מתאים סגנון תגובה לפי ההעדפות שנלמדו.
        
        Args:
            base_style (str): הסגנון הבסיסי מה-Decision Core
            
        Returns:
            str: סגנון מותאם
        """
        prefs = self.memory["communication_preferences"]
        
        # התאמה לפי אורך מועדף
        if prefs["response_length"] == "short":
            if base_style in ["normal", "friendly"]:
                return "short"
        
        # התאמה לפי פורמליות
        if prefs["formality"] == "direct":
            if base_style == "friendly":
                return "terse"  # ישיר יותר
        
        return base_style
    
    def get_context_instructions(self):
        """
        מחזיר הוראות טקסטואליות ל-GPT בהתבסס על מה שנלמד.
        
        Returns:
            str: הוראות מפורטות
        """
        prefs = self.memory["communication_preferences"]
        instructions = []
        
        # אורך תשובות
        if prefs["response_length"] == "short":
            instructions.append("⚠️ USER PREFERENCE: Keep answers SHORT (1-3 sentences max)")
        elif prefs["response_length"] == "detailed":
            instructions.append("✓ USER PREFERENCE: Provide DETAILED explanations")
        
        # פורמליות
        if prefs["formality"] == "direct":
            instructions.append("⚠️ USER PREFERENCE: Be DIRECT. No pleasantries or politeness")
        elif prefs["formality"] == "formal":
            instructions.append("✓ USER PREFERENCE: Maintain FORMAL tone")
        
        # הסברים
        if prefs["explanation_level"] == "minimal":
            instructions.append("⚠️ USER PREFERENCE: Don't explain WHY, just answer")
        elif prefs["explanation_level"] == "extensive":
            instructions.append("✓ USER PREFERENCE: Always explain reasoning")
        
        # חוקים שנלמדו
        if self.memory["learned_rules"]:
            instructions.append("\n📚 LEARNED RULES:")
            for rule in self.memory["learned_rules"][-5:]:  # 5 אחרונים
                instructions.append(f"  • {rule}")
        
        # איסורים
        if self.memory["do_not"]:
            instructions.append("\n🚫 DO NOT:")
            for rule in self.memory["do_not"][-5:]:
                instructions.append(f"  • {rule}")
        
        return "\n".join(instructions) if instructions else ""
    
    def analyze_feedback(self, user_message):
        """
        מנתח פידבק מהמשתמש ומעדכן את הזיכרון אוטומטית.
        
        Args:
            user_message (str): מה המשתמש אמר
            
        Returns:
            bool: True אם נלמד משהו חדש
        """
        msg_lower = user_message.lower()
        learned_something = False
        
        # זיהוי ביקורת על אורך
        if any(phrase in msg_lower for phrase in ["ארוך מדי", "תמיד עונה ארוך", "תקצר", "too long", "be brief"]):
            self.update_preference("response_length", "short")
            self.add_rule("User prefers concise answers - keep responses under 3 sentences")
            learned_something = True
        
        # זיהוי דרישה לפירוט
        if any(phrase in msg_lower for phrase in ["תסביר יותר", "תפרט", "למה", "explain more", "give details"]):
            self.update_preference("response_length", "detailed")
            self.update_preference("explanation_level", "extensive")
            learned_something = True
        
        # זיהוי דרישה לישירות
        if any(phrase in msg_lower for phrase in ["תדבר ישיר", "בלי נימוסים", "תפסיק להתנצל", "be direct", "stop apologizing"]):
            self.update_preference("formality", "direct")
            self.add_rule("Be direct and honest, skip politeness")
            learned_something = True
        
        # זיהוי דרישה לחום
        if any(phrase in msg_lower for phrase in ["תהיה יותר חברי", "תהיה יותר חם", "be friendly", "be warmer"]):
            self.update_preference("formality", "casual")
            self.update_preference("humor", "high")
            learned_something = True
        
        return learned_something

# יצירת מופע יחיד
behavioral_memory = BehavioralMemory()