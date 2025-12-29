import time
import math

class MemoryPriority:
    """
    מערכת דירוג זיכרונות לפי חשיבות, זמן, ושימוש.
    מבוסס על הנוסחה: Score = (Importance * 0.4) + (Similarity * 0.35) + (Decay * 0.15) + (Usage * 0.1)
    """

    @staticmethod
    def calculate_priority(memory_item, similarity_score=0.0):
        """
        חישוב ציון priority לזיכרון בודד.
        
        Args:
            memory_item (dict): המטא-דאטה של הזיכרון (כולל timestamp, importance, access_count).
            similarity_score (float): הציון שקיבלנו מ-ChromaDB (כמה הטקסט דומה).
        """
        
        # 1. חשיבות בסיסית (נקבעת בעת השמירה, ברירת מחדל 0.5)
        # המרה של text labels למספרים
        imp_str = memory_item.get('importance', 'medium')
        importance_map = {'high': 1.0, 'medium': 0.5, 'low': 0.2}
        importance = importance_map.get(imp_str, 0.5) if isinstance(imp_str, str) else 0.5

        # 2. דעיכה לפי זמן (Time Decay)
        # זיכרונות דועכים ככל שעובר הזמן (חצי-חיים של 30 יום)
        try:
            timestamp_str = memory_item.get('timestamp')
            # נרמול פורמטים שונים של זמן
            if not timestamp_str:
                timestamp = time.time()
            else:
                # מנסים לפרסר זמן, אם נכשל משתמשים בעכשיו
                timestamp = time.time() # Placeholder logic for simplicity unless parsing needed
                
            age_factor = MemoryPriority._calculate_decay(timestamp)
        except:
            age_factor = 1.0

        # 3. שימוש חוזר (Usage Bonus)
        # אם שלפנו את הזיכרון הזה הרבה פעמים, הוא כנראה חשוב
        access_count = memory_item.get('access_count', 0)
        usage_bonus = min(0.1, access_count * 0.01) # מקסימום בונוס של 10%

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
        """פונקציית דעיכה אקספוננציאלית"""
        days_old = (time.time() - timestamp_unix) / 86400
        # דעיכה: אחרי 30 יום הרלוונטיות יורדת לחצי
        decay = math.exp(-days_old / 30)
        return decay

    @staticmethod
    def sort_memories(memories_with_scores):
        """
        מקבל רשימה של (זיכרון, ציון_דמיון) ומחזיר רשימה ממויינת לפי הציון המשוקלל החדש
        """
        scored_memories = []
        for mem, sim_score in memories_with_scores:
            final_score = MemoryPriority.calculate_priority(mem['metadata'], sim_score)
            mem['final_score'] = final_score
            scored_memories.append(mem)
        
        # מיון מהגבוה לנמוך
        return sorted(scored_memories, key=lambda x: x['final_score'], reverse=True)