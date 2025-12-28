import os
import speech_recognition as sr
import json
import threading
import pygame
import time
import warnings
import pyautogui
import base64
import subprocess 
import webbrowser 
import pyperclip
from io import BytesIO
from dotenv import load_dotenv
from google.cloud import texttospeech
from openai import OpenAI
from duckduckgo_search import DDGS  # <--- הרכיב החדש לחיפוש באינטרנט

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
    pass

is_speaking = False
stop_flag = False

tts_client = texttospeech.TextToSpeechClient()
voice_id = "he-IL-Wavenet-D"  # קול גברי

# נתיבים
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MEMORY_PATH = os.path.join(DATA_DIR, "memory.json")
LIVE_JSON_PATH = os.path.join(BASE_DIR, "..", "frontend", "live.json")
OUTPUT_AUDIO = os.path.join(BASE_DIR, "output.mp3")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

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

    if not text or len(text.strip()) == 0:
        return

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

def capture_screen():
    try:
        screenshot = pyautogui.screenshot()
        if screenshot.mode in ("RGBA", "P"):
            screenshot = screenshot.convert("RGB")
        buffered = BytesIO()
        screenshot.save(buffered, format="JPEG", quality=50)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    except Exception as e:
        return None

def get_selected_text():
    try:
        pyperclip.copy("") 
        pyautogui.keyDown('command'); pyautogui.press('c'); pyautogui.keyUp('command')
        for i in range(10):
            time.sleep(0.1)
            content = pyperclip.paste()
            if content and len(content.strip()) > 0: return content
        return ""
    except: return ""

# --- פונקציית החוקר (חיפוש באינטרנט) ---
def search_web(query):
    print(f"🌐 מחפש באינטרנט: {query}")
    try:
        results_text = ""
        # שימוש ב-DDGS לחיפוש מהיר
        with DDGS() as ddgs:
            # לוקח 3 תוצאות ראשונות
            results = list(ddgs.text(query, region='il-he', max_results=3))
            
            for i, r in enumerate(results):
                results_text += f"\nמקור {i+1}: {r['title']} - {r['body']}"
        
        if not results_text:
            return "לא מצאתי מידע באינטרנט."
            
        return results_text
    except Exception as e:
        print(f"Network error: {e}")
        return "הייתה בעיה בחיבור לאינטרנט."

def execute_system_command(command_str):
    print(f"⚙️ מבצע פקודה: {command_str}")
    try:
        if command_str.startswith("WEBSITE:"):
            url = command_str.replace("WEBSITE:", "").strip()
            webbrowser.open(url)
            return "פתחתי."
        elif command_str.startswith("APP:"):
            app_name = command_str.replace("APP:", "").strip()
            subprocess.run(["open", "-a", app_name])
            return f"פתחתי את {app_name}."
        elif command_str.startswith("TYPE:"):
            text_to_type = command_str.replace("TYPE:", "").strip()
            pyperclip.copy(text_to_type)
            pyautogui.hotkey('command', 'v')
            return "הקלדתי." 
    except Exception as e:
        return "תקלה."
    return None

def chat_with_gpt(prompt, image_data=None, selected_context=None, web_results=None):
    update_ui("מדבר", prompt, "")
    
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            memory_data = json.load(f)
    except:
        memory_data = {"conversations": []}
    
    # --- המוח של Nog ---
    system_content = """אתה Nog, עוזר אישי חכם וגבר.
    
    הוראות:
    1. אם המשתמש שואל על מידע עדכני (חדשות, מחירים, מזג אוויר, תאריכים), ענה בפקודה אחת בלבד: SEARCH_CMD: נושא החיפוש.
    2. אם קיבלת תוצאות חיפוש (בקונטקסט), ענה למשתמש על בסיסן בקצרה.
    3. לכתיבת טקסט השתמש בפקודה: TYPE:.
    4. לפתיחת דברים: APP:, WEBSITE:.
    5. היה תכליתי וחברי ("אחי", "גבר").
    """
    
    messages = [{"role": "system", "content": system_content}]
    messages.extend(memory_data.get("conversations", [])[-5:])

    # בניית הפרומפט הסופי
    final_prompt = prompt
    
    if selected_context:
        final_prompt += f"\n\n[טקסט מסומן מהמשתמש]:\n{selected_context}"
    
    if web_results:
         final_prompt += f"\n\n[תוצאות חיפוש מהאינטרנט לשימושך]:\n{web_results}\n\nהנחיה: ענה למשתמש על בסיס המידע הזה."

    content_payload = [{"type": "text", "text": final_prompt}]

    if image_data:
        content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})

    messages.append({"role": "user", "content": content_payload})

    try:
        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        answer = response.choices[0].message.content.strip()
        
        # 1. בדיקה אם הוא רוצה לחפש באינטרנט
        if "SEARCH_CMD:" in answer:
            search_query = answer.replace("SEARCH_CMD:", "").strip()
            speak("בודק לך את זה...")
            update_ui("חושב", prompt, "מחפש ברשת...")
            
            # ביצוע החיפוש האמיתי
            real_results = search_web(search_query)
            
            # שליחה חוזרת ל-GPT עם התוצאות (רקורסיה)
            chat_with_gpt(prompt, image_data, selected_context, web_results=real_results)
            return

        # 2. ביצוע פקודות רגילות
        if any(answer.startswith(cmd) for cmd in ["APP:", "WEBSITE:", "TYPE:"]):
            feedback = execute_system_command(answer)
            update_ui("פעולה", prompt, answer)
            if feedback and not answer.startswith("TYPE:"):
                speak(feedback)
        else:
            # 3. תשובה רגילה
            if "conversations" not in memory_data: memory_data["conversations"] = []
            
            # שומר בזיכרון רק אם זה לא היה סבב ביניים של חיפוש
            if not web_results:
                memory_data["conversations"].append({"role": "user", "content": final_prompt})
                memory_data["conversations"].append({"role": "assistant", "content": answer})
                with open(MEMORY_PATH, "w", encoding="utf-8") as f:
                    json.dump(memory_data, f, ensure_ascii=False, indent=2)
                
            update_ui("מדבר", prompt, answer)
            speak(answer)
            print(f"Nog: {answer}")
            
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        speak("נתקלתי בבעיה.")

def listen_loop():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    update_ui("מוכנה")
    print("\n🎤 --- Nog מוכן ---")

    while True:
        try:
            if is_speaking:
                time.sleep(0.1); continue

            with mic as source:
                try: audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=5)
                except sr.WaitTimeoutError: continue 

                try: text = recognizer.recognize_google(audio, language="he-IL").lower()
                except: continue

                if any(w in text for w in ["צ'אט", "צאט", "היי", "נוג", "נוגה"]):
                    print(f"שמעתי: {text}")
                    query = text.replace("צ'אט", "").replace("צאט", "").replace("היי", "").replace("נוגה", "").replace("נוג", "").strip()
                    
                    if not query: continue

                    img = None; sel_txt = None
                    keywords_vision = ["תסתכל", "תראה", "רואה", "מסך", "תמונה"]
                    keywords_selection = ["זה", "הזאת", "הזה", "מסומן", "תקרא", "טפל", "תסכם", "מה כתוב"]

                    if any(w in query for w in keywords_selection):
                        sel_txt = get_selected_text()
                        if sel_txt: print("✅ טקסט הועתק")

                    if not sel_txt and any(w in query for w in keywords_vision):
                        speak("מסתכל...")
                        img = capture_screen()
                    
                    chat_with_gpt(query, img, sel_txt)
        
        except Exception: pass

if __name__ == "__main__":
    listen_loop()