import os
import speech_recognition as sr
import json
import threading
import pygame
import time
import warnings
from dotenv import load_dotenv
from google.cloud import texttospeech
from openai import OpenAI

# השתקת אזהרות
warnings.filterwarnings("ignore")

# --- טעינת הגדרות ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# נתיב למפתח של גוגל
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "chat-voice-key.json")

# אתחול סאונד
try:
    pygame.mixer.init()
except:
    print("⚠️ אין התקן שמע")

is_speaking = False
stop_flag = False

tts_client = texttospeech.TextToSpeechClient()
voice_id = "he-IL-Wavenet-C" 

# נתיבים
MEMORY_PATH = os.path.join(BASE_DIR, "..", "data", "memory.json")
LIVE_JSON_PATH = os.path.join(BASE_DIR, "..", "frontend", "live.json")
OUTPUT_AUDIO = os.path.join(BASE_DIR, "output.mp3")

def update_ui(status, user_text="", chat_text=""):
    try:
        data = {"status": status, "user": user_text, "chat": chat_text}
        with open(LIVE_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except:
        pass

def play_audio_thread():
    global is_speaking, stop_flag
    try:
        pygame.mixer.music.load(OUTPUT_AUDIO)
        pygame.mixer.music.play()
        is_speaking = True
        while pygame.mixer.music.get_busy():
            if stop_flag:
                pygame.mixer.music.stop()
                break
            time.sleep(0.05)
        is_speaking = False
        stop_flag = False
    except Exception as e:
        print(f"❌ שגיאה בניגון: {e}")
        is_speaking = False

def speak(text):
    global is_speaking, stop_flag
    if is_speaking:
        stop_flag = True
        time.sleep(0.1)

    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="he-IL", name=voice_id)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        
        with open(OUTPUT_AUDIO, "wb") as out:
            out.write(response.audio_content)
        
        threading.Thread(target=play_audio_thread).start()
    except Exception as e:
        print(f"❌ שגיאה ב-TTS: {e}")

def chat_with_gpt(prompt):
    update_ui("מדבר", prompt, "")
    
    # 1. טעינת הזיכרון
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            memory_data = json.load(f)
    except:
        memory_data = {"conversations": [], "facts": {}, "user_name": ""}
    
    # 2. בניית ה"אישיות" עם הזיכרון
    system_content = "אתה NogEye, עוזר אישי חכם. ענה בעברית טבעית וקצרה."
    
    # הזרקת השם
    user_name = memory_data.get("user_name", "")
    if user_name:
        system_content += f" שם המשתמש הוא {user_name}."
    
    # הזרקת העובדות (הכלב לואי, דאלאס וכו')
    facts = memory_data.get("facts", {})
    if facts:
        facts_list = list(facts.values())
        system_content += " עובדות שאתה יודע על המשתמש: " + ". ".join(facts_list) + "."

    messages = [{"role": "system", "content": system_content}]
    
    # הוספת היסטוריית שיחה קצרה
    recent_convs = memory_data.get("conversations", [])[-5:]
    messages.extend(recent_convs)
    
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=messages
        )
        answer = response.choices[0].message.content
        
        # שמירת השיחה החדשה לזיכרון
        if "conversations" not in memory_data:
            memory_data["conversations"] = []
            
        memory_data["conversations"].append({"role": "user", "content": prompt})
        memory_data["conversations"].append({"role": "assistant", "content": answer})
        
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
            
        update_ui("מדבר", prompt, answer)
        speak(answer)
        print(f"NogEye: {answer}")
    except Exception as e:
        print(f"❌ שגיאה ב-OpenAI: {e}")

def listen_loop():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    update_ui("מוכנה")
    print("\n🎤 --- NogEye מאזין... (אמור 'צ'אט') ---")

    while True:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                # מנגנון למניעת האזנה עצמית (כשהוא מדבר הוא לא מקשיב)
                if is_speaking:
                    time.sleep(0.5)
                    continue

                audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
                text = recognizer.recognize_google(audio, language="he-IL").lower()
                
                if "צ'אט" in text or "צאט" in text or "היי" in text:
                    print(f"שמעתי: {text}") # מדפיס רק כשיש זיהוי רלוונטי
                    query = text.replace("צ'אט", "").replace("צאט", "").replace("היי", "").strip()
                    if not query:
                        speak("כן מאור, אני כאן.")
                    else:
                        chat_with_gpt(query)
            except:
                pass

if __name__ == "__main__":
    listen_loop()