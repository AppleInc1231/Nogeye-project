# backend/beliefs.py

import json
import os
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
BELIEFS_PATH = os.path.join(DATA_DIR, "beliefs.json")

class BeliefsSystem:
    """
    מערכת האמונות של Nog - "התיאוריות" שלו על העולם ועליך.
    
    זה מה שהופך את Nog ממכונה לישות שבונה מודל של המציאות.
    
    Features:
    - Belief Formation: יצירת אמונות חדשות מתצפיות
    - Confidence Tracking: מעקב אחר רמת הביטחון בכל אמונה
    - Conflict Detection: זיהוי אמונות סותרות
    - Belief Update: עדכון אמונות לפי ראיות חדשות
    """
    
    def __init__(self):
        self.beliefs = self.load_or_create()
    
    def load_or_create(self):
        if os.path.exists(BELIEFS_PATH):
            try:
                with open(BELIEFS_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_initial_beliefs()
        else:
            return self.create_initial_beliefs()
    
    def create_initial_beliefs(self):
        """יצירת מערכת אמונות ראשונית"""
        return {
            "about_user": {
                # אמונות על המשתמש (מאור)
                # כל אמונה כוללת: statement, confidence, evidence_count, last_verified
            },
            
            "about_world": {
                # אמונות כלליות על העולם
                "people_productive_morning": {
                    "statement": "Most people are productive in the morning",
                    "confidence": 0.6,
                    "evidence_for": 0,
                    "evidence_against": 0,
                    "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "source": "general_knowledge"
                }
            },
            
            "causal_models": {
                # מודלים סיבתיים: X גורם ל-Y
                # דוגמה: "עייפות -> תשובות קצרות"
            },
            
            "meta": {
                "total_beliefs": 1,
                "average_confidence": 0.6,
                "last_verification": None,
                "conflicts_detected": []
            }
        }
    
    def save(self):
        """שמירה לדיסק"""
        try:
            self.beliefs["meta"]["last_updated"] = datetime.now().isoformat()
            with open(BELIEFS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.beliefs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving beliefs: {e}")
    
    def add_belief(self, category, key, statement, confidence=0.5, source="observation"):
        """
        הוספת אמונה חדשה.
        
        Args:
            category (str): "about_user", "about_world", "causal_models"
            key (str): מזהה ייחודי לאמונה
            statement (str): האמונה עצמה (טקסט)
            confidence (float): רמת ביטחון (0.0-1.0)
            source (str): מאיפה האמונה הגיעה
        
        Example:
            add_belief("about_user", "works_at_night", 
                      "Maor is most productive at night (22:00-02:00)", 
                      confidence=0.7, source="pattern_learning")
        """
        
        if category not in self.beliefs:
            print(f"❌ Unknown category: {category}")
            return False
        
        # בדיקה אם כבר קיימת אמונה דומה
        if key in self.beliefs[category]:
            print(f"⚠️  Belief '{key}' already exists. Use update_belief() instead.")
            return False
        
        self.beliefs[category][key] = {
            "statement": statement,
            "confidence": confidence,
            "evidence_for": 0,
            "evidence_against": 0,
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "source": source,
            "verified": False
        }
        
        self.beliefs["meta"]["total_beliefs"] += 1
        self._update_average_confidence()
        self.save()
        
        print(f"💭 New Belief: [{category}] {statement} (confidence: {confidence:.0%})")
        return True
    
    def update_belief(self, category, key, evidence_type="for", confidence_delta=0.0):
        """
        עדכון אמונה קיימת לפי ראיות חדשות.
        
        Args:
            category (str): קטגוריה
            key (str): מזהה האמונה
            evidence_type (str): "for" (תומך) או "against" (סותר)
            confidence_delta (float): שינוי ברמת הביטחון
        
        Example:
            # מאור עבד בבוקר היום - זה סותר את האמונה שהוא עובד בלילה
            update_belief("about_user", "works_at_night", evidence_type="against", confidence_delta=-0.1)
        """
        
        if category not in self.beliefs or key not in self.beliefs[category]:
            print(f"❌ Belief '{key}' not found in '{category}'")
            return False
        
        belief = self.beliefs[category][key]
        
        # עדכון ספירת ראיות
        if evidence_type == "for":
            belief["evidence_for"] += 1
            belief["confidence"] = min(1.0, belief["confidence"] + abs(confidence_delta))
        else:  # against
            belief["evidence_against"] += 1
            belief["confidence"] = max(0.0, belief["confidence"] - abs(confidence_delta))
        
        belief["last_updated"] = datetime.now().isoformat()
        
        # אם הביטחון ירד מתחת ל-0.2 - מסמנים לבדיקה
        if belief["confidence"] < 0.2:
            belief["needs_verification"] = True
            print(f"⚠️  Belief '{key}' has low confidence ({belief['confidence']:.0%}) - needs verification")
        
        # אם הביטחון עלה מעל 0.8 - מסמנים כמאומת
        if belief["confidence"] > 0.8:
            belief["verified"] = True
        
        self._update_average_confidence()
        self.save()
        
        print(f"🔄 Updated Belief: {belief['statement']} → {belief['confidence']:.0%}")
        return True
    
    def get_belief(self, category, key):
        """
        מחזיר אמונה ספציפית.
        
        Returns:
            dict or None
        """
        if category in self.beliefs and key in self.beliefs[category]:
            return self.beliefs[category][key]
        return None
    
    def get_beliefs_by_confidence(self, min_confidence=0.0, max_confidence=1.0):
        """
        מחזיר אמונות לפי טווח ביטחון.
        
        Example:
            # קבל אמונות חלשות (ספק)
            weak_beliefs = get_beliefs_by_confidence(0.0, 0.4)
        """
        filtered = []
        
        for category in ["about_user", "about_world", "causal_models"]:
            if category not in self.beliefs:
                continue
            
            for key, belief in self.beliefs[category].items():
                conf = belief.get("confidence", 0.5)
                if min_confidence <= conf <= max_confidence:
                    filtered.append({
                        "category": category,
                        "key": key,
                        "belief": belief
                    })
        
        return filtered
    
    def detect_conflicts(self):
        """
        מזהה אמונות סותרות.
        
        Example:
            - "Maor is productive at night" (0.8)
            - "Maor is an early riser" (0.7)
            → קונפליקט!
        
        Returns:
            list של קונפליקטים
        """
        conflicts = []
        
        # כאן צריך לוגיקה מורכבת יותר - בינתיים זיהוי פשוט
        user_beliefs = self.beliefs.get("about_user", {})
        
        # דוגמה: בדיקת קונפליקטים על שעות עבודה
        works_at_night = user_beliefs.get("works_at_night", {}).get("confidence", 0)
        early_riser = user_beliefs.get("early_riser", {}).get("confidence", 0)
        
        if works_at_night > 0.6 and early_riser > 0.6:
            conflicts.append({
                "type": "schedule_conflict",
                "beliefs": ["works_at_night", "early_riser"],
                "severity": "medium",
                "detected": datetime.now().isoformat()
            })
        
        self.beliefs["meta"]["conflicts_detected"] = conflicts
        return conflicts
    
    def get_high_confidence_beliefs(self, category=None, min_confidence=0.7):
        """
        מחזיר אמונות עם ביטחון גבוה (למעשה "עובדות ידועות").
        
        Args:
            category (str): אופציונלי - סינון לפי קטגוריה
            min_confidence (float): סף מינימלי
        
        Returns:
            list של אמונות
        """
        high_conf = []
        
        categories = [category] if category else ["about_user", "about_world", "causal_models"]
        
        for cat in categories:
            if cat not in self.beliefs:
                continue
            
            for key, belief in self.beliefs[cat].items():
                if belief.get("confidence", 0) >= min_confidence:
                    high_conf.append({
                        "category": cat,
                        "key": key,
                        "statement": belief["statement"],
                        "confidence": belief["confidence"]
                    })
        
        return high_conf
    
    def get_uncertain_beliefs(self, max_confidence=0.5):
        """
        מחזיר אמונות לא בטוחות (צריכות אימות).
        """
        return self.get_beliefs_by_confidence(0.0, max_confidence)
    
    def form_causal_belief(self, cause, effect, confidence=0.5):
        """
        יוצר אמונה סיבתית: X גורם ל-Y.
        
        Example:
            form_causal_belief("user_tired", "prefers_short_answers", 0.6)
        """
        key = f"{cause}_causes_{effect}"
        statement = f"When {cause}, then {effect}"
        
        return self.add_belief("causal_models", key, statement, confidence, source="pattern_inference")
    
    def get_context_for_gpt(self):
        """
        מחזיר סיכום אמונות לשימוש ב-GPT context.
        
        Returns:
            str: טקסט מעוצב
        """
        high_conf = self.get_high_confidence_beliefs(min_confidence=0.7)
        uncertain = self.get_uncertain_beliefs(max_confidence=0.4)
        
        context = "BELIEFS SYSTEM (What Nog 'knows'):\n"
        context += "═" * 60 + "\n"
        
        if high_conf:
            context += "\n✓ HIGH CONFIDENCE (Established Facts):\n"
            for belief in high_conf[:5]:  # רק 5 הראשונות
                context += f"  • {belief['statement']} ({belief['confidence']:.0%})\n"
        
        if uncertain:
            context += "\n? UNCERTAIN (Needs Verification):\n"
            for belief in uncertain[:3]:  # רק 3 הראשונות
                b = belief["belief"]
                context += f"  • {b['statement']} ({b['confidence']:.0%})\n"
        
        context += "\n" + "═" * 60
        
        return context
    
    def _update_average_confidence(self):
        """מעדכן ממוצע ביטחון"""
        all_confidences = []
        
        for category in ["about_user", "about_world", "causal_models"]:
            if category not in self.beliefs:
                continue
            for belief in self.beliefs[category].values():
                all_confidences.append(belief.get("confidence", 0.5))
        
        if all_confidences:
            self.beliefs["meta"]["average_confidence"] = sum(all_confidences) / len(all_confidences)
        else:
            self.beliefs["meta"]["average_confidence"] = 0.5

# יצירת מופע גלובלי
beliefs_system = BeliefsSystem()
