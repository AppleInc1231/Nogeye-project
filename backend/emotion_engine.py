import time
import json
import os

# הגדרות נתיבים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MOOD_PATH = os.path.join(DATA_DIR, "mood.json")

class EmotionEngine:
    """
    מנוע רגש דינמי עם momentum וזיכרון.
    """
    def __init__(self):
        self.momentum = 0.0      # -1 (עצוב/כועס) עד +1 (שמח/מרוצה)
        self.stability = 0.8     # כמה מהר הרגש משתנה (0=תנודתי, 1=יציב)
        self.energy = 0.8        # רמת אנרגיה 0-1
        
        # טריגרים לשינוי רגש
        self.triggers = {
            'positive': ['תודה', 'אלוף', 'מלך', 'מעולה', 'אוהב', 'טוב'],
            'negative': ['טיפש', 'גרוע', 'מעצבן', 'סתום', 'די', 'חלאס'],
            'stress': ['עבודה', 'לחץ', 'פרויקט', 'דחוף', 'מהר'],
            'calm': ['רגוע', 'שקט', 'מוזיקה', 'כיף']
        }
        
        # טעינת מצב אחרון אם קיים
        self._load_state()

    def analyze(self, text, silence_duration=0):
        """
        ניתוח רגשי מתקדם שמחזיר את המצב העדכני.
        """
        # 1. זיהוי רגש מהטקסט הנוכחי
        detected_impact = self._detect_emotion_impact(text)
        
        # 2. חישוב השינוי (Delta)
        delta = detected_impact * (1 - self.stability)
        
        # 3. עדכון המומנטום (הרגש המצטבר)
        self.momentum += delta
        
        # 4. דעיכה טבעית (הרגש חוזר לאט לאט ל-0 / ניטרלי)
        # ככל שעבר יותר זמן, הדעיכה חזקה יותר
        decay_factor = 0.95
        if silence_duration > 300: # אם היה שקט של 5 דקות
            decay_factor = 0.8
        self.momentum *= decay_factor
        
        # 5. הגבלת הטווח בין -1 ל-1
        self.momentum = max(-1.0, min(1.0, self.momentum))
        
        # 6. ניהול אנרגיה
        self._update_energy(silence_duration, detected_impact)
        
        # 7. שמירת המצב לדיסק
        self._save_state()
        
        return {
            'state': self._get_emotion_label(),
            'momentum': round(self.momentum, 2),
            'energy': round(self.energy, 2)
        }

    def _detect_emotion_impact(self, text):
        """מחזיר מספר בין -1 ל-1 בהתאם למילים בטקסט"""
        if not text: return 0
        text = text.lower()
        
        if any(w in text for w in self.triggers['positive']): return 0.2
        if any(w in text for w in self.triggers['negative']): return -0.3 # עלבון פוגע יותר ממחמאה
        if any(w in text for w in self.triggers['stress']): return -0.1
        if any(w in text for w in self.triggers['calm']): return 0.1
        return 0

    def _update_energy(self, silence_duration, impact):
        """אנרגיה יורדת בפעילות ועולה במנוחה"""
        # אם יש אינטראקציה, האנרגיה יורדת קצת
        if impact != 0:
            self.energy -= 0.02
        
        # מנוחה מטעינה אנרגיה
        if silence_duration > 60:
            self.energy += 0.05
            
        self.energy = max(0.1, min(1.0, self.energy))

    def _get_emotion_label(self):
        """תרגום המספר למילה"""
        if self.momentum > 0.5: return 'happy'
        if self.momentum > 0.2: return 'content'
        if self.momentum > -0.2: return 'neutral'
        if self.momentum > -0.6: return 'annoyed'
        return 'angry'

    def _save_state(self):
        data = {
            "current_mood": self._get_emotion_label(),
            "momentum": self.momentum,
            "energy_level": int(self.energy * 100)
        }
        try:
            with open(MOOD_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except: pass

    def _load_state(self):
        if os.path.exists(MOOD_PATH):
            try:
                with open(MOOD_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.momentum = data.get("momentum", 0.0)
                    self.energy = data.get("energy_level", 80) / 100.0
            except: pass