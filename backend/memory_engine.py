import json
import os
import datetime
import chromadb
import uuid
from openai import OpenAI
from dotenv import load_dotenv

# --- הגדרות נתיבים ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MEMORY_PATH = os.path.join(DATA_DIR, "memory.json")
# כאן יישמר המוח הוקטורי (התיקייה החדשה)
DB_PATH = os.path.join(DATA_DIR, "brain_db") 
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# וודא שהתיקייה קיימת
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- אתחול ChromaDB (המוח הוקטורי) ---
# זה יוצר אוטומטית את הקבצים הדרושים בתיקיית data/brain_db
try:
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    # אוסף העובדות (כמו טבלה בבסיס נתונים)
    facts_collection = chroma_client.get_or_create_collection("facts")
    print("🧠 ChromaDB Vector Engine Initialized Successfully.")
except Exception as e:
    print(f"⚠️ Failed to initialize ChromaDB: {e}")
    facts_collection = None

# --- פונקציות עזר לקובץ JSON (זיכרון לטווח קצר) ---
def _load_memory():
    """טוען את קובץ הזיכרון (רק לשיחה שוטפת)"""
    if not os.path.exists(MEMORY_PATH):
        return {"conversations": []}
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"conversations": []}

def _save_memory_file(data):
    try:
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving memory file: {e}")

# --- הפונקציות הראשיות ---

def save_memory(content, importance="medium"):
    """
    שמירה ידנית (REMEMBER) למסד הוקטורי.
    זה נשמר לנצח ב-ChromaDB.
    """
    if not facts_collection:
        return "שגיאה: מסד הנתונים לא זמין."

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    doc_id = str(uuid.uuid4())
    
    try:
        facts_collection.add(
            documents=[content],
            metadatas=[{"timestamp": timestamp, "type": "manual_fact", "importance": importance}],
            ids=[doc_id]
        )
        return f"נשמר בזיכרון הטווח הארוך: {content}"
    except Exception as e:
        return f"שגיאה בשמירה: {e}"

def retrieve_memory(query, n_results=5):
    """
    שליפה חכמה (RAG):
    1. מחפש עובדות רלוונטיות ב-ChromaDB (לפי דמיון סמנטי).
    2. מושך את סוף השיחה מקובץ ה-JSON.
    """
    facts_str = "No relevant long-term facts found."
    
    # 1. חיפוש ב-ChromaDB
    if facts_collection:
        try:
            results = facts_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if results['documents'] and results['documents'][0]:
                found_facts = results['documents'][0]
                # מנקה כפילויות ומסדר יפה
                facts_str = "\n".join([f"- {fact}" for fact in found_facts])
        except Exception as e:
            print(f"Vector search error: {e}")

    # 2. שליפת השיחה האחרונה (Context) מקובץ ה-JSON
    data = _load_memory()
    # לוקחים רק את ה-10 האחרונות כדי לתת הקשר מיידי
    recent_convo = data.get("conversations", [])[-10:]
    convo_str = json.dumps(recent_convo, ensure_ascii=False)
    
    return f"Long-Term Memory (Facts):\n{facts_str}\n\nShort-Term Memory (Recent Chat):\n{convo_str}"

def save_episode(description, user_emotion, ai_emotion, importance="medium"):
    """שמירת אפיזודה - נכנס גם ל-ChromaDB"""
    content = f"Episode: {description} | User Emotion: {user_emotion}"
    return save_memory(content, importance)

# --- המנוע החדש: Consolidation לתוך ChromaDB ---
def consolidate_memory():
    """
    הפונקציה שרצה בחלום:
    1. לוקחת שיחות ישנות מ-JSON.
    2. מחלצת עובדות בעזרת GPT.
    3. דוחפת את העובדות ל-ChromaDB (נצח).
    4. מוחקת את השיחות הישנות מה-JSON.
    """
    data = _load_memory()
    conversations = data.get("conversations", [])
    
    # סף הניקוי: 60 הודעות (כדי לא לנקות כל רגע)
    if len(conversations) < 60:
        return
        
    print("🧠 מבצע תהליך גיבוש זיכרון לטווח ארוך (ChromaDB)...")
    
    # משאירים את ה-50 האחרונות בזיכרון עבודה (Short Term)
    to_analyze = conversations[:-50] 
    to_keep = conversations[-50:]
    
    conversation_text = json.dumps(to_analyze, ensure_ascii=False)
    
    prompt = f"""
    Analyze this conversation log between AI and User (Maor).
    Extract clear, distinct FACTS about the user (preferences, hobbies, work, pets, location, plans).
    Ignore small talk.
    Return a list of facts in Hebrew. 
    If nothing new was learned, return "NO_NEW_INFO".
    Log: {conversation_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip()
        
        if "NO_NEW_INFO" not in result and facts_collection:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            new_facts = result.split("\n")
            
            # הכנה להוספה בבת אחת (Batch)
            docs = []
            metas = []
            ids = []
            
            for fact in new_facts:
                clean_fact = fact.replace("- ", "").strip()
                # סינון זבל (שורות ריקות או קצרות מדי)
                if clean_fact and len(clean_fact) > 5:
                    docs.append(clean_fact)
                    metas.append({"timestamp": timestamp, "type": "consolidated_fact"})
                    ids.append(str(uuid.uuid4()))
                    print(f"💡 נלמד ונשמר ב-ChromaDB: {clean_fact}")
            
            if docs:
                facts_collection.add(documents=docs, metadatas=metas, ids=ids)
        
        # מחיקת ההיסטוריה הישנה מה-JSON
        data["conversations"] = to_keep
        _save_memory_file(data)
        print("✅ הזיכרון עבר אופטימיזציה: הועבר ל-Vector DB.")
        
    except Exception as e:
        print(f"Consolidation Error: {e}")

# לבדיקה ידנית
if __name__ == "__main__":
    consolidate_memory()