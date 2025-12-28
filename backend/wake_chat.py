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
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv
from google.cloud import texttospeech
from openai import OpenAI
from duckduckgo_search import DDGS

# השתקת אזהרות
warnings.filterwarnings("ignore")

# --- טעינת הגדרות ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "chat-voice-key.json")

try:
    pygame.mixer.init()
except:
    pass

is_speaking = False
stop_flag = False

tts_client = texttospeech.TextToSpeechClient()
voice_id = "he-IL-Wavenet-D" 

# נתיבים
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MEMORY_PATH = os.path.join(DATA_DIR, "memory.json")
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
LIVE_JSON_PATH = os.path.join(BASE_DIR, "..", "frontend", "live.json")
OUTPUT_AUDIO = os.path.join(BASE_DIR, "output.mp3")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- UI וסאונד ---
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
        is_speaking = False

def speak(text):
    global is_speaking, stop_flag
    if is_speaking:
        stop_flag = True
        time.sleep(0.1)
    if not text or len(text.strip()) == 0: return

    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="he-IL", name=voice_id)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        with open(OUTPUT_AUDIO, "wb") as out:
            out.write(response.audio_content)
        threading.Thread(target=play_audio_thread).start()
    except Exception as e:
        print(f"TTS Error: {e}")

# --- כלים ---
def capture_screen():
    try:
        screenshot = pyautogui.screenshot()
        if screenshot.mode in ("RGBA", "P"): screenshot = screenshot.convert("RGB")
        buffered = BytesIO()
        screenshot.save(buffered, format="JPEG", quality=50)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except: return None

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

def load_profile():
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data: return "אין מידע עדיין."
                return "\n".join([f"- {item}" for item in data])
        except: return ""
    return ""

def update_profile(new_fact):
    data = []
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                if content: data = json.loads(content)
        except: data = []
    
    timestamp = datetime.now().strftime("%d/%m/%Y")
    fact_with_date = f"[{timestamp}] {new_fact}"
    data.append(fact_with_date)
    
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return "רשמתי, אחי."

def search_web(query):
    try:
        results_text = ""
        with DDGS() as ddgs:
            # לוקח 2 תוצאות כדי שיהיה מהיר
            results = list(ddgs.text(query, region='il-he', max_results=2))
            for i, r in enumerate(results):
                results_text += f"\nמקור {i+1}: {r['title']} - {r['body']}"
        return results_text if results_text else "לא מצאתי מידע."
    except: return "תקלת רשת."

def execute_system_command(command_str):
    try:
        if command_str.startswith("WEBSITE:"):
            webbrowser.open(command_str.replace("WEBSITE:", "").strip())
            return "פתחתי."
        elif command_str.startswith("APP:"):
            subprocess.run(["open", "-a", command_str.replace("APP:", "").strip()])
            return "פתחתי."
        elif command_str.startswith("TYPE:"):
            pyperclip.copy(command_str.replace("TYPE:", "").strip())
            pyautogui.hotkey('command', 'v')
            return "הקלדתי."
        elif command_str.startswith("REMEMBER:"):
            return update_profile(command_str.replace("REMEMBER:", "").strip())
    except: return "תקלה."
    return None

def ask_gpt(messages):
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        return response.choices[0].message.content.strip()
    except: return None

# --- פונקציית התדרוך החכם (המשודרגת) ---
def startup_greeting():
    """אוסף חדשות ומזג אוויר ונותן תדרוך בוקר"""
    print("🌅 מכין תדרוך בוקר חכם...")
    
    # 1. בדיקת מידע מהאינטרנט
    try:
        # חיפוש משולב לחיסכון בזמן
        weather_info = search_web("מזג אוויר תל אביב היום")
        news_info = search_web("חדשות ראשיות ישראל היום כותרות")
    except:
        weather_info = "לא הצלחתי לבדוק מזג אוויר"
        news_info = "אין חדשות כרגע"

    user_profile = load_profile()
    current_time = datetime.now().strftime("%A, %d/%m/%Y, %H:%M")
    
    system_content = f"""אתה Nog, ישות דיגיטלית חכמה. אתה מתעורר עכשיו.
    זמן נוכחי: {current_time}
    זיכרון אישי: {user_profile}
    
    מידע מהעולם (חיפוש בזמן אמת):
    [מזג אוויר]: {weather_info}
    [חדשות]: {news_info}
    
    המשימה: תן למשתמש "תדרוך בוקר" קצר, גברי ופרקטי.
    1. תגיד בוקר טוב.
    2. תן משפט אחד על מזג האוויר (מה ללבוש?).
    3. תן כותרת אחת מעניינת מהחדשות.
    4. אם יש משהו בזיכרון להיום - תזכיר אותו.
    
    אל תחפור. הכל ב-3-4 משפטים. היה מגניב.
    """
    
    greeting = ask_gpt([{"role": "system", "content": system_content}])
    if greeting:
        update_ui("מדבר", "", greeting)
        speak(greeting)

def proactive_check_loop():
    print("💓 מנגנון יוזמה הופעל...")
    while True:
        time.sleep(60)
        if is_speaking: continue

        user_profile = load_profile()
        current_time = datetime.now().strftime("%A, %d/%m/%Y, %H:%M")
        
        system_content = f"""אתה התת-מודע של Nog.
        זמן: {current_time}
        זיכרון: {user_profile}
        המשימה: האם יש אירוע *קריטי* עכשיו? אם לא, ענה SILENT.
        אם כן, ענה במשפט קצר למשתמש.
        """
        
        try:
            answer = ask_gpt([{"role": "system", "content": system_content}])
            if answer and "SILENT" not in answer:
                print(f"🔔 יוזמה: {answer}")
                update_ui("מדבר", "", answer)
                speak(answer)
        except: pass

def chat_with_gpt(prompt, image_data=None, selected_context=None, web_results=None):
    update_ui("מדבר", prompt, "")
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f: memory = json.load(f)
    except: memory = {"conversations": []}
    
    user_profile = load_profile()
    current_time = datetime.now().strftime("%A, %d/%m/%Y, %H:%M")

    system_content = f"""אתה Nog, ישות דיגיטלית. שותף גבר.
    זמן: {current_time}
    זיכרון: {user_profile}
    הוראות: שמור עובדות עם REMEMBER:. חפש עם SEARCH_CMD:. כתוב עם TYPE:.
    """
    
    messages = [{"role": "system", "content": system_content}]
    messages.extend(memory.get("conversations", [])[-5:])

    final_prompt = prompt
    if selected_context: final_prompt += f"\n\n[טקסט מסומן]:\n{selected_context}"
    if web_results: final_prompt += f"\n\n[תוצאות חיפוש]:\n{web_results}"

    content_payload = [{"type": "text", "text": final_prompt}]
    if image_data:
        content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})

    messages.append({"role": "user", "content": content_payload})

    answer = ask_gpt(messages)
    
    if not answer:
        speak("שגיאה ברשת.")
        return

    if "SEARCH_CMD:" in answer:
        query = answer.replace("SEARCH_CMD:", "").strip()
        speak("בודק...")
        res = search_web(query)
        chat_with_gpt(prompt, image_data, selected_context, web_results=res)
        return

    if any(answer.startswith(cmd) for cmd in ["APP:", "WEBSITE:", "TYPE:", "REMEMBER:"]):
        feedback = execute_system_command(answer)
        update_ui("פעולה", prompt, answer)
        if feedback and not answer.startswith("TYPE:"): speak(feedback)
    else:
        if not web_results:
            if "conversations" not in memory: memory["conversations"] = []
            memory["conversations"].append({"role": "user", "content": final_prompt})
            memory["conversations"].append({"role": "assistant", "content": answer})
            with open(MEMORY_PATH, "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
        
        update_ui("מדבר", prompt, answer)
        speak(answer)
        print(f"Nog: {answer}")

def listen_loop():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source: recognizer.adjust_for_ambient_noise(source, duration=1)
    
    update_ui("מוכנה")
    print("\n🎤 --- Nog מוכן ---")
    
    # הפעלת תדרוך בוקר חכם
    threading.Thread(target=startup_greeting).start()

    # הפעלת דופק
    threading.Thread(target=proactive_check_loop, daemon=True).start()

    while True:
        try:
            if is_speaking: time.sleep(0.1); continue
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
                    if any(w in query for w in ["זה", "מסומן", "תקרא", "טפל"]):
                        sel_txt = get_selected_text()
                        if sel_txt: print("✅ טקסט הועתק")
                    if not sel_txt and any(w in query for w in ["תראה", "מסך", "תמונה"]):
                        speak("מסתכל...")
                        img = capture_screen()
                    
                    chat_with_gpt(query, img, sel_txt)
        except: pass

if __name__ == "__main__":
    listen_loop()