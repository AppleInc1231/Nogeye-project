# backend/memory_priority.py

import time
import math

class MemoryPriority:
    """
    מערכת דירוג זיכרונות לפי חשיבות, זמן, ושימוש.
    Score = (Importance * 0.4) + (Similarity * 0.35) + (Decay * 0.15) + (Usage * 0.1)
    """

    @staticmethod
    def calculate_priority(memory_item, similarity_score=0.0):
        """
        חישוב ציון priority לזיכרון בודד.
        
        Args:
            memory_item (dict): המטא-דאטה של הזיכרון (timestamp, importance, access_count).
            similarity_score (float): הציון מ-ChromaDB (כמה הטקסט דומה).
        
        Returns:
            float: ציון סופי משוקלל
        """
        
        # 1. חשיבות בסיסית (40%)
        importance_raw = memory_item.get('importance', 0.5)
        
        # תמיכה גם ב-string וגם ב-float
        if isinstance(importance_raw, str):
            importance_map = {'high': 1.0, 'medium': 0.5, 'low': 0.2}
            importance = importance_map.get(importance_raw, 0.5)
        else:
            importance = float(importance_raw)

        # 2. דעיכה לפי זמן (15%)
        timestamp = memory_item.get('timestamp')
        
        # תיקון קריטי: בדיקה אם timestamp הוא מספר תקין
        if timestamp and isinstance(timestamp, (int, float)):
            age_factor = MemoryPriority._calculate_decay(timestamp)
        else:
            # אם אין timestamp תקין, נתייחס לזיכרון כאילו הוא חדש
            age_factor = 1.0

        # 3. שימוש חוזר (10%)
        access_count = memory_item.get('access_count', 0)
        usage_bonus = min(0.1, access_count * 0.01)

        # --- הנוסחה הסופית ---
        score = (
            importance * 0.40 +
            similarity_score * 0.35 +
            age_factor * 0.15 +
            usage_bonus * 0.10
        )
        
        return score

    @staticmethod
    def _calculate_decay(timestamp_unix):
        """
        פונקציית דעיכה אקספוננציאלית.
        זיכרונות ישנים נחלשים עם הזמן (חצי-חיים של 30 יום).
        """
        try:
            days_old = (time.time() - float(timestamp_unix)) / 86400
            # דעיכה: אחרי 30 יום הרלוונטיות יורדת לחצי
            decay = math.exp(-days_old / 30)
            return max(0.1, decay)  # מינימום 0.1
        except:
            return 0.5  # ברירת מחדל במקרה של שגיאה

    @staticmethod
    def sort_memories(memories_with_scores):
        """
        מקבל רשימה של (mem_obj, similarity) ומחזיר רשימה ממוינת.
        
        Args:
            memories_with_scores: list של tuples: (mem_obj, similarity_score)
        
        Returns:
            list של mem_obj ממוינים לפי priority
        """
        scored_memories = []
        
        for mem_obj, sim_score in memories_with_scores:
            metadata = mem_obj.get('metadata', {})
            final_score = MemoryPriority.calculate_priority(metadata, sim_score)
            
            # שמירת הציון בתוך האובייקט (לדיבאג)
            mem_obj['final_score'] = final_score
            scored_memories.append((final_score, mem_obj))
        
        # מיון מהגבוה לנמוך
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        # החזרת רק האובייקטים (ללא הציונים)
        return [mem_obj for score, mem_obj in scored_memories]