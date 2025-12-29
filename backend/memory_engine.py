import os
import chromadb
from chromadb.config import Settings
from datetime import datetime
import uuid

# הגדרות נתיבים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "brain_db")

# אתחול מסד הנתונים
client = chromadb.PersistentClient(path=DB_PATH)

# יצירת אוספים (Collections) לזיכרון
facts_collection = client.get_or_create_collection("facts")
episodes_collection = client.get_or_create_collection("episodes")

def save_memory(text, category="general"):
    """שומר עובדה יבשה (למשל: למאור יש פגישה מחר)"""
    try:
        facts_collection.add(
            documents=[text],
            metadatas=[{"category": category, "timestamp": datetime.now().isoformat()}],
            ids=[str(uuid.uuid4())]
        )
        return "זכרתי."
    except Exception as e:
        print(f"Error saving memory: {e}")
        return f"שגיאה בזיכרון: {e}"

def save_episode(description, user_emotion, ai_emotion, importance="medium"):
    """שומר חוויה רגשית עם הקשר של זמן ורגש"""
    try:
        episodes_collection.add(
            documents=[description],
            metadatas=[{
                "user_emotion": user_emotion,
                "ai_emotion": ai_emotion,
                "importance": importance,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }],
            ids=[str(uuid.uuid4())]
        )
        print(f"🧠 נצרבה חוויה: {description}")
        return "תיעדתי את החוויה בזיכרון לטווח ארוך."
    except Exception as e:
        print(f"Error saving episode: {e}")
        return f"שגיאה בתיעוד: {e}"

def retrieve_memory(query, n_results=3):
    """
    הלב של הזיכרון החדש:
    שולף לא רק את הטקסט, אלא מפרמט אותו עם הזמן והרגש שהיו אז.
    זה נותן למודל תחושת זמן והמשכיות.
    """
    try:
        # שליפת חוויות
        ep_results = episodes_collection.query(query_texts=[query], n_results=n_results)
        # שליפת עובדות
        fact_results = facts_collection.query(query_texts=[query], n_results=n_results)
        
        combined_context = []
        
        # עיבוד חוויות (הוספת מטא-דאטה לטקסט)
        if ep_results['documents'] and ep_results['documents'][0]:
            for i, doc in enumerate(ep_results['documents'][0]):
                meta = ep_results['metadatas'][0][i]
                timestamp = meta.get('timestamp', 'לא ידוע')
                emotion = meta.get('user_emotion', 'ניטרלי')
                combined_context.append(f"[חוויה מתאריך {timestamp} | רגש שלך: {emotion}]: {doc}")

        # עיבוד עובדות
        if fact_results['documents'] and fact_results['documents'][0]:
            for doc in fact_results['documents'][0]:
                combined_context.append(f"[עובדה]: {doc}")
                
        if not combined_context:
            return "אין זיכרון רלוונטי ספציפי."
            
        return "\n".join(combined_context)
    except Exception as e:
        print(f"Error retrieving memory: {e}")
        return ""