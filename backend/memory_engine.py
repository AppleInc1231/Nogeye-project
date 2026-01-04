import json
import os
import datetime
from openai import OpenAI
from dotenv import load_dotenv

# טעינת הגדרות
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MEMORY_PATH = os.path.join(DATA_DIR, "memory.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# וודא שהתיקייה קיימת
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def _load_memory():
    """טוען את קובץ הזיכרון בבטחה"""
    if not os.path.exists(MEMORY_PATH):
        return {
            "conversations": [],
            "facts": {},
            "preferences": {}
        }
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"conversations": [], "facts": {}, "preferences": {}}

def _save_memory_file(data):
    """שומר את קובץ הזיכרון"""
    try:
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving memory file: {e}")

def save_memory(content, importance="medium"):
    """
    שמירה ידנית של זיכרון (פקודת REMEMBER)
    שומר את זה כעובדה (Fact)
    """
    data = _load_memory()
    timestamp = str(datetime.datetime.now())
    
    # אתחול אם חסר
    if "facts" not in data:
        data["facts"] = {}

    # יצירת מפתח ייחודי
    key = f"manual_{timestamp}"
    data["facts"][key] = content
    
    _save_memory_file(data)
    return f"זכרתי: {content}"

def retrieve_memory(query, n_results=5):
    """
    שליפת זיכרון רלוונטי לשיחה.
    מחזיר שילוב של העובדות האחרונות + קצת מהשיחה האחרונה.
    """
    data = _load_memory()
    
    # 1. שליפת עובדות (מציג את ה-20 האחרונות כדי שיהיה הקשר רחב על המשתמש)
    facts_list = list(data.get("facts", {}).values())
    # לוקחים את ה-20 האחרונות
    recent_facts = facts_list[-20:]
    facts_str = "\n".join([f"- {f}" for f in recent_facts])
    
    # 2. שליפת השיחה האחרונה (Context) - מציג עד 10 הודעות לשליפה מהירה
    # (ההיסטוריה המלאה של ה-50 נשלחת בנפרד ב-wake_chat)
    recent_convo = data.get("conversations", [])[-10:]
    convo_str = json.dumps(recent_convo, ensure_ascii=False)
    
    return f"User Facts:\n{facts_str}\n\nRecent Interaction Snippet:\n{convo_str}"

def save_episode(description, user_emotion, ai_emotion, importance="medium"):
    """שמירת אפיזודה משמעותית - הכנה לעתיד"""
    # כרגע נשמור את זה כעובדה, בעתיד אפשר להרחיב למסד וקטורי
    content = f"Episode: {description} (User: {user_emotion}, AI: {ai_emotion})"
    save_memory(content, importance)
    return "נשמר ביומן האירועים."

# --- המנוע החדש: אופטימיזציה חכמה (Consolidation) ---
def consolidate_memory():
    """
    הפונקציה הזו רצה בזמן 'חלימה'.
    היא לוקחת את היסטוריית השיחה הארוכה,
    מזקקת ממנה עובדות חדשות על המשתמש,
    ומוחקת את המלל המיותר כדי לשמור על קובץ קטן ומהיר.
    """
    data = _load_memory()
    conversations = data.get("conversations", [])
    
    # סף הניקוי: אם יש פחות מ-60 הודעות, לא נוגעים כלום (כדי שיהיה רצף)
    if len(conversations) < 1:
        return
        
    print("🧠 מבצע תהליך גיבוש זיכרון (Learning)...")
    
    # חלוקה: את הישנים מנתחים, את ה-50 האחרונים שומרים כמו שהם (זיכרון עבודה)
    to_analyze = conversations[:-50] 
    to_keep = conversations[-50:]
    
    # הופכים את השיחות הישנות לטקסט בשביל ה-AI
    conversation_text = json.dumps(to_analyze, ensure_ascii=False)
    
    # הפרומפט לזיקוק עובדות
    prompt = f"""
    Analyze this conversation log between AI and User (Maor).
    Extract clear, distinct FACTS about the user (preferences, hobbies, work, pets, location, plans, fears).
    Ignore small talk ("hello", "how are you", "search for X").
    
    Return the output as a clean list of facts in Hebrew.
    If nothing new was learned about the user personally, return "NO_NEW_INFO".
    
    Log:
    {conversation_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a memory consolidation engine. Extract facts."},
                {"role": "user", "content": prompt}
            ]
        )
        
        result = response.choices[0].message.content.strip()
        
        if "facts" not in data:
            data["facts"] = {}

        if "NO_NEW_INFO" not in result:
            timestamp = str(datetime.datetime.now())
            # הוספת העובדות החדשות
            new_facts = result.split("\n")
            for fact in new_facts:
                clean_fact = fact.replace("- ", "").strip()
                if clean_fact and len(clean_fact) > 5:
                    # מפתח ייחודי לכל עובדה
                    key = f"{timestamp}_{clean_fact[:10]}"
                    data["facts"][key] = clean_fact
                    print(f"💡 נלמד ונשמר: {clean_fact}")
        
        # מחיקת ההיסטוריה הישנה ושמירה
        data["conversations"] = to_keep
        _save_memory_file(data)
        print("✅ הזיכרון עבר אופטימיזציה: הודעות ישנות נוקו, עובדות נשמרו.")
        
    except Exception as e:
        print(f"Memory Consolidation Error: {e}")

# להפעלה ידנית לבדיקה
if __name__ == "__main__":
    consolidate_memory()