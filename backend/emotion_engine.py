import json
import os
import time

# הגדרות נתיבים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MOOD_PATH = os.path.join(DATA_DIR, "mood.json")

class EmotionEngine:
    """
    מנוע רגש דינמי המותאם לארכיטקטורת Consciousness v8.
    """
    def __init__(self):
        self.momentum = 0.0      # -1 (דיכאון) עד +1 (אופוריה)
        self.energy = 0.8        # רמת אנרגיה 0-1
        self.load_state()

    def load_state(self):
        """טעינת המצב האחרון מהקובץ"""
        if os.path.exists(MOOD_PATH):
            try:
                with open(MOOD_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.momentum = float(data.get("momentum", 0.0))
                    # תמיכה לאחור בשמות משתנים ישנים
                    energy_val = data.get("energy", data.get("energy_level", 80))
                    if energy_val > 1: energy_val /= 100.0 # המרה מאחוזים לשבר עשרוני
                    self.energy = float(energy_val)
            except:
                self.momentum = 0.0
                self.energy = 0.8

    def save_state(self):
        """שמירת המצב לדיסק"""
        try:
            data = {
                "current_mood": self.get_mood_description(),
                "momentum": self.momentum,
                "energy": self.energy,
                "timestamp": time.time()
            }
            with open(MOOD_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving mood: {e}")

    def update_mood(self, stimulus):
        """
        זו הפונקציה הקריטית שהייתה חסרה!
        מקבלת גירוי (-1.0 עד 1.0) מ-Consciousness ומעדכנת את הרגש.
        """
        # 1. אינרציה: הרגש הישן משפיע ב-80%, החדש ב-20%
        # זה מונע מנוג להיות מאני-דפרסיבי שמשתנה כל שנייה
        self.momentum = (self.momentum * 0.8) + (stimulus * 0.2)
        
        # הגבלת גבולות
        self.momentum = max(-1.0, min(1.0, self.momentum))

        # 2. ניהול אנרגיה
        # כל אינטראקציה (stimulus != 0) עולה קצת אנרגיה
        if stimulus != 0:
            self.energy -= 0.02
        else:
            # מנוחה (stimulus == 0) מעלה אנרגיה
            self.energy += 0.05
        
        # אם קרה משהו מרגש מאוד (חיובי או שלילי) זה נותן בוסט לאדרנלין
        if abs(stimulus) > 0.4:
            self.energy += 0.1

        # גבולות אנרגיה
        self.energy = max(0.1, min(1.0, self.energy))

        self.save_state()
        print(f"💓 Mood Updated: {self.momentum:.2f} ({self.get_mood_description()}), Energy: {self.energy:.2f}")

    def get_mood_description(self):
        """תרגום המספר למילה"""
        if self.momentum > 0.5: return "Happy"
        if self.momentum > 0.2: return "Content"
        if self.momentum > -0.2: return "Neutral"
        if self.momentum > -0.6: return "Annoyed"
        return "Angry"