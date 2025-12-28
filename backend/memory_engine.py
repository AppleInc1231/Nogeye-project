import chromadb
import os
import uuid
from datetime import datetime

# הגדרת נתיב למסד הנתונים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "brain_db")

# אתחול הלקוח
client = chromadb.PersistentClient(path=DB_PATH)

# אוסף עובדות (מה שהיה עד עכשיו)
facts_collection = client.get_or_create_collection(name="nog_facts")

# אוסף חוויות (החדש! - Episodic Memory)
episodes_collection = client.get_or_create_collection(name="nog_episodes")

def save_memory(text, metadata_type="fact"):
    """שומר עובדה יבשה בזיכרון"""
    print(f"💾 שומר עובדה: {text}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    facts_collection.add(
        documents=[text],
        metadatas=[{"type": metadata_type, "timestamp": timestamp}],
        ids=[str(uuid.uuid4())]
    )
    return "נשמר בזיכרון."

def save_episode(description, user_emotion, ai_emotion, importance_level):
    """שומר חוויה סובייקטיבית עם רגשות"""
    print(f"🧠 שומר חוויה רגשית: {description} | רגש: {user_emotion}")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # אנחנו שומרים את הטקסט, אבל מצמידים לו "תגיות רגש" במטא-דאטה
    episodes_collection.add(
        documents=[description],
        metadatas=[{
            "type": "episode",
            "timestamp": timestamp,
            "user_emotion": user_emotion,
            "ai_emotion": ai_emotion,
            "importance": importance_level
        }],
        ids=[str(uuid.uuid4())]
    )
    return "החוויה נצרבה בזיכרון הרגשי."

def retrieve_memory(query, n_results=3):
    """שולף גם עובדות וגם חוויות רלוונטיות"""
    print(f"🔍 מחפש במוח (עובדות + חוויות) ל: '{query}'...")
    
    # חיפוש בעובדות
    fact_results = facts_collection.query(query_texts=[query], n_results=n_results)
    facts = fact_results['documents'][0] if fact_results['documents'] else []
    
    # חיפוש בחוויות
    episode_results = episodes_collection.query(query_texts=[query], n_results=n_results)
    episodes = episode_results['documents'][0] if episode_results['documents'] else []
    
    combined_memory = ""
    if facts:
        combined_memory += "--- FACTS ---\n" + "\n".join([f"- {m}" for m in facts]) + "\n"
    if episodes:
        combined_memory += "--- PAST EXPERIENCES & FEELINGS ---\n" + "\n".join([f"- {m}" for m in episodes])
        
    if not combined_memory: return ""
    return combined_memory