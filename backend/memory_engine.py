import os
import chromadb
from datetime import datetime
import uuid
import time
from memory_priority import MemoryPriority

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
    מקבל: importance (high/medium/low) או מספר.
    """
    try:
        # המרה בטוחה אם importance הוא מחרוזת
        imp_score = 0.5
        if isinstance(importance, str):
            if importance == "high": imp_score = 1.0
            elif importance == "low": imp_score = 0.2
        elif isinstance(importance, (int, float)):
            imp_score = float(importance)

        facts_collection.add(
            documents=[text],
            metadatas=[{
                "category": category, 
                "timestamp": time.time(),
                "importance": imp_score,
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
        raw_results = facts_collection.query(query_texts=[query], n_results=n_results + 3)
        memories_to_sort = []
        
        if raw_results['documents'] and raw_results['documents'][0]:
            docs = raw_results['documents'][0]
            metas = raw_results['metadatas'][0]
            distances = raw_results['distances'][0]
            ids = raw_results['ids'][0]

            for i in range(len(docs)):
                similarity = max(0, 1 - distances[i])
                mem_obj = {"content": docs[i], "metadata": metas[i], "id": ids[i]}
                memories_to_sort.append((mem_obj, similarity))

        sorted_memories = MemoryPriority.sort_memories(memories_to_sort)
        top_memories = sorted_memories[:n_results]
        
        for mem in top_memories:
            _update_access_count(mem['id'], mem['metadata'])

        combined_context = []
        for mem in top_memories:
            meta = mem['metadata']
            imp_marker = "⭐" if meta.get('importance', 0) > 0.8 else ""
            ts = meta.get('timestamp')
            date_str = "בעבר"
            try:
                if isinstance(ts, float):
                    date_str = datetime.fromtimestamp(ts).strftime('%d/%m')
            except: pass

            combined_context.append(f"[{date_str}]{imp_marker} {mem['content']}")
                
        if not combined_context: return "אין זיכרון רלוונטי."
        return "\n".join(combined_context)

    except Exception as e:
        print(f"Error retrieving memory: {e}")
        return ""

def _update_access_count(doc_id, metadata):
    try:
        new_count = metadata.get('access_count', 0) + 1
        metadata['access_count'] = new_count
        facts_collection.update(ids=[doc_id], metadatas=[metadata])
    except: pass