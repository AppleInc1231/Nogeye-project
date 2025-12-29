import os
import chromadb
from datetime import datetime
import uuid
import time
from memory_priority import MemoryPriority  # <-- החיבור למודול הדירוג שיצרנו

# הגדרות נתיבים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "brain_db")

# אתחול מסד הנתונים
client = chromadb.PersistentClient(path=DB_PATH)

# יצירת אוספים (Collections)
facts_collection = client.get_or_create_collection("facts")
episodes_collection = client.get_or_create_collection("episodes")

def save_memory(text, category="general", importance="medium"):
    """
    שומר עובדה עם דירוג חשיבות.
    importance: 'high', 'medium', 'low'
    """
    try:
        facts_collection.add(
            documents=[text],
            metadatas=[{
                "category": category, 
                "timestamp": time.time(), # שומרים כ-Unix Timestamp לחישובי דעיכה
                "importance": importance,
                "access_count": 0
            }],
            ids=[str(uuid.uuid4())]
        )
        return f"נשמר בזיכרון ({importance})."
    except Exception as e:
        print(f"Error saving memory: {e}")
        return f"שגיאה בזיכרון: {e}"

def save_episode(description, user_emotion, ai_emotion, importance="medium"):
    """שומר חוויה רגשית"""
    try:
        episodes_collection.add(
            documents=[description],
            metadatas=[{
                "user_emotion": user_emotion,
                "ai_emotion": ai_emotion,
                "importance": importance,
                "timestamp": time.time(),
                "readable_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "access_count": 0
            }],
            ids=[str(uuid.uuid4())]
        )
        print(f"🧠 נצרבה חוויה: {description}")
        return "תיעדתי את החוויה."
    except Exception as e:
        print(f"Error saving episode: {e}")
        return f"שגיאה בתיעוד: {e}"

def retrieve_memory(query, n_results=5):
    """
    שליפת זיכרון חכמה המשתמשת ב-MemoryPriority
    """
    try:
        # 1. שליפה גולמית מ-ChromaDB (יותר תוצאות ממה שצריך, כדי שנסנן)
        raw_results = facts_collection.query(query_texts=[query], n_results=n_results + 3)
        
        memories_to_sort = []
        
        # 2. המרה לפורמט שהממיין שלנו מבין
        if raw_results['documents'] and raw_results['documents'][0]:
            docs = raw_results['documents'][0]
            metas = raw_results['metadatas'][0]
            distances = raw_results['distances'][0] # Chroma מחזיר מרחק (הפוך לדמיון)
            ids = raw_results['ids'][0]

            for i in range(len(docs)):
                # המרת מרחק לציון דמיון (0-1) בקירוב
                similarity = max(0, 1 - distances[i])
                
                mem_obj = {
                    "content": docs[i],
                    "metadata": metas[i],
                    "id": ids[i]
                }
                # שומרים כזוג (זיכרון, ציון דמיון)
                memories_to_sort.append((mem_obj, similarity))

        # 3. שימוש ב-MemoryPriority למיון חכם
        # זה ייתן עדיפות לזיכרונות חשובים וחדשים על פני סתם דומים
        sorted_memories = MemoryPriority.sort_memories(memories_to_sort)
        
        # 4. עדכון מונה שימוש (Access Count) לזיכרונות שנבחרו
        # (זה מחזק זיכרונות שמשתמשים בהם הרבה)
        top_memories = sorted_memories[:n_results]
        for mem in top_memories:
            _update_access_count(mem['id'], mem['metadata'])

        # 5. פרמוט הטקסט ל-GPT
        combined_context = []
        for mem in top_memories:
            meta = mem['metadata']
            imp_marker = "⭐" if meta.get('importance') == 'high' else ""
            
            # אם זה timestamp ישן (מחרוזת) או חדש (float), נסה להציג קריא
            ts = meta.get('timestamp')
            date_str = "בעבר"
            try:
                if isinstance(ts, float):
                    date_str = datetime.fromtimestamp(ts).strftime('%d/%m')
                else:
                    date_str = str(ts).split('T')[0]
            except: pass

            combined_context.append(f"[{date_str}]{imp_marker} {mem['content']}")
                
        if not combined_context:
            return "אין זיכרון רלוונטי."
            
        return "\n".join(combined_context)

    except Exception as e:
        print(f"Error retrieving memory: {e}")
        return ""

def _update_access_count(doc_id, metadata):
    """פונקציית עזר לעדכון מונה הצפיות בזיכרון"""
    try:
        new_count = metadata.get('access_count', 0) + 1
        metadata['access_count'] = new_count
        facts_collection.update(ids=[doc_id], metadatas=[metadata])
    except:
        pass