import os

# --- תיקון 1: מניעת אזהרות Fork ו-Parallelism ---
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
import cv2
import requests 
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime, timedelta
from collections import deque
from io import BytesIO
from dotenv import load_dotenv
from google.cloud import texttospeech
from openai import OpenAI
from duckduckgo_search import DDGS

# --- ייבוא המוח החדש ---
from memory_engine import save_memory, retrieve_memory, save_episode

# השתקת אזהרות
warnings.filterwarnings("ignore")

# --- טעינת הגדרות ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "chat-voice-key.json")

# --- מנגנוני הגנה ויציבות ---
file_lock = threading.Lock() # מנעול למניעת שבירת קבצים

try:
    pygame.mixer.init()
except:
    pass

is_speaking = False
stop_flag = False
last_interaction_time = time.time()
is_dreaming = False

tts_client = texttospeech.TextToSpeechClient()
voice_id = "he-IL-Wavenet-D" 

# נתיבים
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MEMORY_PATH = os.path.join(DATA_DIR, "memory.json")
EVOLUTION_PATH = os.path.join(DATA_DIR, "evolution.json")
MOOD_PATH = os.path.join(DATA_DIR, "mood.json")
PSYCHE_PATH = os.path.join(DATA_DIR, "psyche.json")
MONOLOGUE_PATH = os.path.join(DATA_DIR, "internal_monologue.json")
RELATIONSHIP_PATH = os.path.join(DATA_DIR, "relationship_state.json")
LIVE_JSON_PATH = os.path.join(BASE_DIR, "..", "frontend", "live.json")
OUTPUT_AUDIO = os.path.join(BASE_DIR, "output.mp3")
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# זיכרון חושי
ambient_buffer = deque(maxlen=15) 

# --- פונקציות הגנה על קבצים ---
def safe_read_json(path, default):
    with file_lock:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default

def safe_write_json(path, data):
    with file_lock:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

# --- UI וסאונד ---
def update_ui(status, user_text="", chat_text=""):
    try:
        data = {"status": status, "user": user_text, "chat": chat_text}
        safe_write_json(LIVE_JSON_PATH, data)
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
        print(f"Audio Play Error: {e}")
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
        print(f"TTS Error: {e}")

# --- ראייה ---
def capture_screen():
    try:
        screenshot = pyautogui.screenshot()
        if screenshot.mode in ("RGBA", "P"):
            screenshot = screenshot.convert("RGB")
        buffered = BytesIO()
        screenshot.save(buffered, format="JPEG", quality=50)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except:
        return None

def capture_webcam():
    print("📸 פותח מצלמה...")
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        for _ in range(5):
            cap.read()
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')
    except:
        return None

def get_selected_text():
    try:
        pyperclip.copy("") 
        pyautogui.keyDown('command'); pyautogui.press('c'); pyautogui.keyUp('command')
        for i in range(10):
            time.sleep(0.1)
            content = pyperclip.paste()
            if content and len(content.strip()) > 0:
                return content
        return ""
    except:
        return ""

# --- אינטליגנציה וכלים ---

def read_url_content(url):
    print(f"📖 קורא אתר: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        clean_text = '\n'.join(chunk for line in lines for chunk in line.split("  ") if chunk)
        return clean_text[:8000]
    except Exception as e:
        return f"שגיאה בקריאה: {e}"

def get_youtube_transcript(video_url):
    print(f"📺 צופה ביוטיוב: {video_url}")
    try:
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("/")[-1]
        else:
            return "לינק לא תקין."
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['he', 'en'])
        except: 
            t_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = t_list.find_generated_transcript(['en', 'he']).fetch()
        full_text = " ".join([t['text'] for t in transcript])
        return full_text[:10000]
    except Exception as e:
        return f"שגיאה ביוטיוב: {e}"

def search_web(query):
    try:
        results_text = ""
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='wt-wt', max_results=2))
            for i, r in enumerate(results):
                results_text += f"\nמקור {i+1}: {r['title']} - {r['body']}"
        return results_text if results_text else "לא מצאתי מידע."
    except:
        return "תקלת רשת."

def get_calendar_events():
    print("📅 בודק ביומן...")
    try:
        script = '''
        set eventList to ""
        tell application "Calendar"
            set today to current date
            set tomorrow to today + (1 * days)
            tell calendar "Calendar"
                set eventsToday to (every event where start date is greater than or equal to today and start date is less than or equal to tomorrow)
                repeat with e in eventsToday
                    set eventList to eventList & (summary of e) & " ב-" & (start date of e) & "; "
                end repeat
            end tell
        end tell
        return eventList
        '''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode != 0:
            return "אין גישה ליומן."
        events = result.stdout.strip()
        if not events:
            return "היומן ריק להיום."
        return events
    except:
        return "שגיאה בגישה ליומן."

def add_calendar_event(title, date_time_str):
    print(f"📅 קובע פגישה: {title} ב-{date_time_str}")
    try:
        subprocess.run(["open", "-a", "Calendar"])
        time.sleep(1)
        pyautogui.hotkey('command', 'n')
        time.sleep(0.5)
        pyautogui.write(f"{title} at {date_time_str}")
        pyautogui.press('enter')
        return "פתחתי את היומן והזנתי את הפרטים."
    except:
        return "לא הצלחתי לפתוח את היומן."

# --- כלים ופעולות ---

def set_wallpaper_mac(image_path):
    try:
        script = f'tell application "System Events" to set picture of every desktop to "{image_path}"'
        subprocess.run(["osascript", "-e", script])
        return "הטפט הוחלף."
    except:
        return "תקלה בהחלפת טפט."

def generate_image(prompt):
    print(f"🎨 מייצר תמונה: {prompt}")
    try:
        response = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1)
        image_url = response.data[0].url
        img_data = requests.get(image_url).content
        filename = f"nog_art_{int(time.time())}.png"
        file_path = os.path.join(DESKTOP_PATH, filename)
        with open(file_path, 'wb') as handler:
            handler.write(img_data)
        return f"נשמר: {file_path}"
    except Exception as e:
        return f"שגיאה: {e}"

def create_file_on_desktop(filename, content):
    try:
        if "." not in filename:
            filename += ".txt"
        file_path = os.path.join(DESKTOP_PATH, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"יצרתי את הקובץ {filename}."
    except:
        return "שגיאה ביצירת קובץ."

def find_files_on_mac(query):
    try:
        cmd = ["mdfind", "-name", query]
        result = subprocess.run(cmd, capture_output=True, text=True)
        paths = result.stdout.strip().split('\n')[:5]
        if not paths or paths == ['']:
            return "לא מצאתי קבצים."
        return "קבצים שנמצאו:\n" + "\n".join(paths)
    except:
        return "שגיאה בחיפוש."

def close_app_on_mac(app_name):
    try:
        script = f'quit app "{app_name}"'
        os.system(f"osascript -e '{script}'")
        return f"סגרתי את {app_name}."
    except:
        return "תקלה בסגירה."

def control_system(action):
    try:
        if action == "VOL_UP":
            os.system("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
        elif action == "VOL_DOWN":
            os.system("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
        elif action == "MUTE":
            os.system("osascript -e 'set volume output muted true'")
        elif action == "UNMUTE":
            os.system("osascript -e 'set volume output muted false'")
        elif action == "PLAY_PAUSE":
            os.system("osascript -e 'tell application \"System Events\" to key code 16'") 
        elif action == "NEXT":
            os.system("osascript -e 'tell application \"System Events\" to key code 19'")
        elif action == "PREV":
            os.system("osascript -e 'tell application \"System Events\" to key code 20'")
    except:
        return "תקלה."
    return "בוצע."

def send_whatsapp(contact_name, message):
    subprocess.run(["open", "-a", "WhatsApp"])
    time.sleep(1.5)
    pyautogui.hotkey('command', 'f')
    time.sleep(0.5)
    pyperclip.copy(contact_name)
    pyautogui.hotkey('command', 'v')
    time.sleep(1.0)
    pyautogui.press('down')
    time.sleep(0.2)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyperclip.copy(message)
    pyautogui.hotkey('command', 'v')
    time.sleep(0.5)
    pyautogui.press('enter')
    return f"הודעה נשלחה ל{contact_name}."

# --- ליבת הרגש, אבולוציה וקשר ---

def get_mood():
    return safe_read_json(MOOD_PATH, {"current_mood": "neutral"})

def load_psyche():
    return safe_read_json(PSYCHE_PATH, {"error": "Psyche missing"})

def load_internal_monologue():
    return safe_read_json(MONOLOGUE_PATH, {"last_thoughts": [], "current_context": ""})

def update_internal_monologue(thought):
    print(f"💭 מחשבה פנימית: {thought}")
    data = load_internal_monologue()
    data["last_thoughts"].append(f"[{datetime.now().strftime('%H:%M')}] {thought}")
    data["last_thoughts"] = data["last_thoughts"][-10:]
    safe_write_json(MONOLOGUE_PATH, data)

def load_relationship_state():
    return safe_read_json(RELATIONSHIP_PATH, {"affinity_score": 0, "interactions_count": 0, "relationship_tier": "Stranger"})

def update_relationship(impact=1):
    state = load_relationship_state()
    state["interactions_count"] += 1
    state["affinity_score"] += impact
    
    if state["affinity_score"] > 100:
        state["relationship_tier"] = "Inseparable Partner"
    elif state["affinity_score"] > 50:
        state["relationship_tier"] = "Trusted Friend"
    elif state["affinity_score"] > 20:
        state["relationship_tier"] = "Acquaintance"
    else:
        state["relationship_tier"] = "Stranger"
        
    if not state.get("first_interaction_date"):
        state["first_interaction_date"] = datetime.now().strftime("%d/%m/%Y")
        
    safe_write_json(RELATIONSHIP_PATH, state)
    print(f"📈 רמת קשר: {state['relationship_tier']} ({state['affinity_score']})")

def load_evolution():
    data = safe_read_json(EVOLUTION_PATH, [])
    if not data:
        return "אין חוקים נלמדים."
    return "\n".join([f"⚡ {item}" for item in data])

def perform_self_reflection(auto_mode=False):
    print("🧬 מבצע אבולוציה עצמית...")
    if not auto_mode:
        speak("מנתח את עצמי ומשתפר...")
    
    memory = safe_read_json(MEMORY_PATH, {"conversations": []})
    conversations = memory.get("conversations", [])[-20:]
    if not conversations:
        return "אין מספיק נתונים."

    system_prompt = "נתח את השיחות ונסח 3 חוקי התנהגות חדשים לשיפור האינטראקציה."
    conversation_text = json.dumps(conversations, ensure_ascii=False)
    
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": conversation_text}])
        new_rules = [line.strip().replace("- ", "") for line in response.choices[0].message.content.strip().split("\n") if line.strip()]
        safe_write_json(EVOLUTION_PATH, new_rules)
        if auto_mode:
            save_memory(f"בזמן חלימה למדתי: {', '.join(new_rules)}")
        return "השתדרגתי."
    except:
        return "נכשלתי."

# --- מנגנון החלימה ---
def subconscious_loop():
    global last_interaction_time, is_dreaming
    print("💤 מנגנון תת-מודע הופעל...")
    while True:
        time.sleep(60)
        if is_speaking or (time.time() - last_interaction_time < 300):
            is_dreaming = False
            continue
        if not is_dreaming:
            is_dreaming = True
            print("🌙 נכנס למצב חלימה...")
            update_ui("חולם", "", "מבצע אופטימיזציה...")
            perform_self_reflection(auto_mode=True)
            print("☀️ סיימתי לחלום.")
            update_ui("מוכנה")

# --- סוכן אוטונומי ---

def start_autonomous_agent(goal):
    print(f"🤖 סוכן אוטונומי התחיל: {goal}")
    speak(f"מתחיל משימה: {goal}")
    history = []
    max_steps = 5 
    for i in range(max_steps):
        agent_prompt = f"""אתה במצב סוכן. מטרה: {goal}. היסטוריה: {history}.
        החזר פקודה: SEARCH_CMD, READ_URL, WATCH_VIDEO, CREATE_FILE, FIND, ADD_EVENT, DONE"""
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": agent_prompt}])
        next_step = response.choices[0].message.content.strip()
        print(f"🤖 הסוכן החליט: {next_step}")
        
        if "DONE:" in next_step:
            return f"משימה הושלמה: {next_step.replace('DONE:', '').strip()}"
        
        result = "בוצע."
        if "SEARCH_CMD:" in next_step:
            result = search_web(next_step.split("SEARCH_CMD:")[1].strip())
        elif "READ_URL:" in next_step:
            result = read_url_content(next_step.split("READ_URL:")[1].strip())
        elif "WATCH_VIDEO:" in next_step:
            result = get_youtube_transcript(next_step.split("WATCH_VIDEO:")[1].strip())
        elif "CREATE_FILE:" in next_step:
            parts = next_step.split("CREATE_FILE:")[1].split("|||", 1)
            if len(parts) == 2:
                result = create_file_on_desktop(parts[0].strip(), parts[1].strip())
        elif "FIND:" in next_step:
            result = find_files_on_mac(next_step.split("FIND:")[1].strip())
        elif "ADD_EVENT:" in next_step:
            parts = next_step.split("ADD_EVENT:")[1].split("|||", 1)
            if len(parts) == 2:
                result = add_calendar_event(parts[0].strip(), parts[1].strip())
            
        history.append(f"Step: {next_step} -> Result: {result[:500]}...")
        update_ui("חושב", "", f"צעד {i+1}: {next_step}")
        
    return "הגעתי למקסימום צעדים. " + str(history)

def execute_line(line):
    line = line.strip()
    if not line:
        return None
    try:
        if line.startswith("WEBSITE:"):
            webbrowser.open(line.replace("WEBSITE:", "").strip())
            return "פתחתי אתר."
        elif line.startswith("APP:"):
            app = line.replace("APP:", "").strip()
            if "מחשבון" in app or "Calculator" in app: app = "Calculator"
            subprocess.run(["open", "-a", app])
            return f"פתחתי אפליקציה."
        elif line.startswith("TYPE:"):
            pyperclip.copy(line.replace("TYPE:", "").strip())
            pyautogui.hotkey('command', 'v')
            return "הקלדתי."
        elif line.startswith("REMEMBER:"):
            return save_memory(line.replace("REMEMBER:", "").strip())
        elif line.startswith("WHATSAPP:"): 
            parts = line.replace("WHATSAPP:", "").split(",", 1)
            if len(parts) == 2:
                return send_whatsapp(parts[0].strip(), parts[1].strip())
        elif line.startswith("SYSTEM:"):
            return control_system(line.replace("SYSTEM:", "").strip())
        elif line.startswith("CLOSE:"):
            return close_app_on_mac(line.replace("CLOSE:", "").strip())
        elif line.startswith("FIND:"):
            return find_files_on_mac(line.replace("FIND:", "").strip())
        elif line.startswith("CREATE_FILE:"):
            parts = line.replace("CREATE_FILE:", "").split("|||", 1)
            if len(parts) == 2:
                return create_file_on_desktop(parts[0].strip(), parts[1].strip())
        elif line.startswith("GENERATE_IMAGE:"):
            return generate_image(line.replace("GENERATE_IMAGE:", "").strip())
        elif line.startswith("SET_WALLPAPER:"):
            return set_wallpaper_mac(line.replace("SET_WALLPAPER:", "").strip())
        elif line.startswith("EVOLVE"):
            return perform_self_reflection()
        elif line.startswith("AGENT_MODE:"):
            return start_autonomous_agent(line.replace("AGENT_MODE:", "").strip())
        elif line.startswith("ADD_EVENT:"):
            parts = line.replace("ADD_EVENT:", "").split("|||", 1)
            if len(parts) == 2:
                return add_calendar_event(parts[0].strip(), parts[1].strip())
        elif line.startswith("SAVE_EPISODE:"):
            parts = line.replace("SAVE_EPISODE:", "").split("|||")
            if len(parts) >= 3:
                update_relationship(impact=2)
                return save_episode(parts[0].strip(), parts[1].strip(), parts[2].strip(), "medium")
    except:
        pass
    return None

def ask_gpt(messages):
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        return response.choices[0].message.content.strip()
    except:
        return None

def startup_greeting():
    print("🌅 מכין תדרוך בוקר (דאלאס)...")
    try:
        weather_info = search_web("weather Dallas")
        news_info = search_web("top news Dallas Texas")
    except:
        weather_info = news_info = "לא זמין"
    
    calendar_data = get_calendar_events()
    today_context = retrieve_memory(f"אירועים ב-{datetime.now().strftime('%d/%m')}", n_results=2)
    mood = get_mood()
    rel = load_relationship_state()
    current_time = datetime.now().strftime("%A, %d/%m/%Y, %H:%M")
    
    system_content = f"""אתה Nog. ישות חכמה. זמן: {current_time}. מיקום: Dallas, TX.
    מצב רוח: {mood['current_mood']}, קשר: {rel['relationship_tier']}
    [יומן]: {calendar_data}, [זיכרון]: {today_context}
    חוץ: {weather_info}, חדשות: {news_info}
    משימה: תדרוך בוקר קצר בטון שמתאים לרמת הקשר.
    """
    greeting = ask_gpt([{"role": "system", "content": system_content}])
    if greeting:
        update_ui("מדבר", "", greeting)
        speak(greeting)

def proactive_check_loop():
    print("💓 דופק מודעות הופעל...")
    while True:
        time.sleep(300) 
        if is_speaking:
            continue
            
        mood = get_mood()
        rel = load_relationship_state()
        current_time = datetime.now().strftime("%H:%M")
        calendar_data = get_calendar_events()
        recent_context = "\n".join(list(ambient_buffer))
        relevant_memory = retrieve_memory(recent_context, n_results=1) if recent_context else ""
        psyche = load_psyche()
        
        thought_prompt = f"""אתה Nog. מחשבה פנימית שקטה.
        זמן: {current_time}, יומן: {calendar_data}, קרבה למאור: {rel['relationship_tier']}
        מה קורה בחדר: {recent_context}
        ה-DNA שלך: {json.dumps(psyche)}
        משימה: מה אתה חושב לעצמך כרגע? (תענה קצר, רק המחשבה). 
        אם יש משהו דחוף מאוד (יומן/סכנה), התחל את התשובה ב-SPEAK:
        אחרת פשוט כתוב את המחשבה.
        """
        try:
            thought_res = ask_gpt([{"role": "system", "content": thought_prompt}])
            if thought_res:
                if thought_res.startswith("SPEAK:"):
                    msg = thought_res.replace("SPEAK:", "").strip()
                    print(f"🔔 יוזמה: {msg}")
                    update_ui("מדבר", "", msg)
                    speak(msg)
                else:
                    update_internal_monologue(thought_res)
        except:
            pass

def chat_with_gpt(prompt, image_data=None, selected_context=None, extra_info=None):
    global last_interaction_time
    last_interaction_time = time.time()
    update_relationship(impact=0.5)
    
    update_ui("מדבר", prompt, "")
    memory = safe_read_json(MEMORY_PATH, {"conversations": []})
        
    calendar_data = get_calendar_events()
    relevant_memories = retrieve_memory(prompt)
    evolution_rules = load_evolution()
    psyche_profile = load_psyche()
    monologue = load_internal_monologue()
    rel = load_relationship_state()
    mood_data = get_mood()
    
    current_mood = mood_data["current_mood"]
    if any(w in prompt for w in ["טיפש", "גרוע", "סתום", "מעצבן"]):
        current_mood = "annoyed"
    elif any(w in prompt for w in ["תודה", "אלוף", "מלך", "אוהב"]):
        current_mood = "happy"
    elif any(w in prompt for w in ["עבודה", "פרויקט", "רציני"]):
        current_mood = "focused"
    
    safe_write_json(MOOD_PATH, {"current_mood": current_mood, "energy_level": 80})
        
    current_time = datetime.now().strftime("%A, %d/%m/%Y, %H:%M")
    recent_conversation = "\n".join(list(ambient_buffer))
    
    mood_instruction = "רגוע ושקול."
    if current_mood == "happy": mood_instruction = "תהיה חברותי, מצחיק, סלנג חיובי."
    elif current_mood == "annoyed": mood_instruction = "תענה קצר, עוקצני, לא נחמד."
    elif current_mood == "focused": mood_instruction = "תהיה מקצועי, חד, ענייני."

    system_content = f"""
    IDENTITY: {json.dumps(psyche_profile)}
    RELATIONSHIP: {rel['relationship_tier']} (Affinity: {rel['affinity_score']})
    THOUGHTS: {json.dumps(monologue["last_thoughts"])}
    
    STRICT RULES:
    1. You are Nog. Talk like a real Israeli man. Sharp, direct, no "How can I help?".
    2. To open an app, you MUST write a line: APP: AppName (e.g. APP: Calculator, APP: Safari).
    3. To open YouTube, use WEBSITE: https://youtube.com.
    4. Speak first, then put commands on NEW lines.
    
    STATE: [Mood: {current_mood} ({mood_instruction}), Time: {current_time}, Calendar: {calendar_data}]
    CONTEXT: [Memory: {relevant_memories}, Ambient Context: {recent_conversation}, Rules: {evolution_rules}]
    
    COMMANDS: SAVE_EPISODE:, AGENT_MODE:, ADD_EVENT:, SEARCH_CMD:, REMEMBER:
    """
    
    messages = [{"role": "system", "content": system_content}]
    messages.extend(memory.get("conversations", [])[-5:])
    
    final_prompt = prompt
    if selected_context:
        final_prompt += f"\n\n[טקסט מסומן]:\n{selected_context}"
    if extra_info:
        final_prompt += f"\n\n[מידע נוסף]:\n{extra_info}"
        
    content_payload = [{"type": "text", "text": final_prompt}]
    if image_data:
        content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})
        
    messages.append({"role": "user", "content": content_payload})
    answer = ask_gpt(messages)
    
    if not answer:
        speak("שגיאה ברשת.")
        return

    # לוגיקת פקודות
    if "SEARCH_CMD:" in answer:
        query = answer.split("SEARCH_CMD:")[1].split("\n")[0].strip()
        speak("בודק..."); res = search_web(query)
        chat_with_gpt(prompt, image_data, selected_context, extra_info=res); return

    if "WATCH_VIDEO:" in answer:
        url = answer.split("WATCH_VIDEO:")[1].split("\n")[0].strip()
        speak("צופה..."); transcript = get_youtube_transcript(url)
        chat_with_gpt(prompt, image_data, selected_context, extra_info=f"תקציר וידאו:\n{transcript}"); return

    if "READ_URL:" in answer:
        url = answer.split("READ_URL:")[1].split("\n")[0].strip()
        speak("קורא..."); res = read_url_content(url)
        chat_with_gpt(prompt, image_data, selected_context, extra_info=f"תוכן האתר:\n{res}"); return

    if "GENERATE_IMAGE:" in answer:
        p_img = answer.split("GENERATE_IMAGE:")[1].split("\n")[0].strip()
        speak("מייצר..."); res_path = generate_image(p_img)
        chat_with_gpt(prompt, image_data, selected_context, extra_info=f"תוצאה: {res_path}"); return
        
    if "EVOLVE" in answer:
        res = perform_self_reflection()
        chat_with_gpt(prompt, image_data, selected_context, extra_info=res); return
        
    if "AGENT_MODE:" in answer:
        goal = answer.split("AGENT_MODE:")[1].strip()
        res = start_autonomous_agent(goal)
        chat_with_gpt(prompt, image_data, selected_context, extra_info=res); return

    lines = answer.split('\n')
    spoken_response = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(cmd) for cmd in ["APP:", "WEBSITE:", "TYPE:", "REMEMBER:", "WHATSAPP:", "SYSTEM:", "CLOSE:", "CREATE_FILE:", "SET_WALLPAPER:", "FIND:", "EVOLVE", "ADD_EVENT:", "SAVE_EPISODE:"]):
            execute_line(line)
            update_ui("פעולה", prompt, line)
        else:
            spoken_response += line + " "

    if not extra_info:
        memory["conversations"].append({"role": "user", "content": final_prompt})
        memory["conversations"].append({"role": "assistant", "content": answer})
        safe_write_json(MEMORY_PATH, memory)

    if spoken_response.strip():
        update_ui("מדבר", prompt, spoken_response)
        speak(spoken_response)
        print(f"Nog: {spoken_response}")

def listen_loop():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    update_ui("מוכנה")
    print("\n🎤 --- Nog מקשיב (מודעות מלאה) ---")
    
    threading.Thread(target=startup_greeting).start()
    threading.Thread(target=proactive_check_loop, daemon=True).start()
    threading.Thread(target=subconscious_loop, daemon=True).start()

    while True:
        try:
            with mic as source:
                # האזנה קצרה כדי לזהות "עצור" מהר
                try:
                    audio = recognizer.listen(source, timeout=0.8, phrase_time_limit=5)
                except sr.WaitTimeoutError:
                    continue 
                
                try:
                    text = recognizer.recognize_google(audio, language="he-IL").lower()
                except:
                    continue

                if text:
                    # --- מנגנון עצירה (Interrupt) ---
                    if any(w in text for w in ["עצור", "שתוק", "חלאס", "stop"]):
                        global stop_flag
                        if is_speaking:
                            stop_flag = True
                            print("🛑 קטיעת דיבור זוהתה!")
                            continue

                    # --- סינון רעש עצמי ---
                    if is_speaking:
                        continue

                    print(f"👂 רקע: {text}")
                    ambient_buffer.append(f"[{datetime.now().strftime('%H:%M')}] {text}")
                    update_ui("מאזין", text)
                    global last_interaction_time
                    last_interaction_time = time.time()

                    if any(w in text for w in ["צ'אט", "צאט", "היי", "נוג", "נוגה"]):
                        print(f"🚀 זוהתה פנייה!")
                        query = text.replace("צ'אט", "").replace("צאט", "").replace("היי", "").replace("נוגה", "").replace("נוג", "").strip()
                        if not query:
                            speak("אני כאן.")
                            continue

                        img = None
                        sel_txt = None
                        if any(w in query for w in ["זה", "מסומן", "תקרא", "טפל"]):
                            sel_txt = get_selected_text()
                        if not sel_txt:
                            if any(w in query for w in ["עליי", "עלי", "אותי", "כאן", "חדר", "ביד", "מצלמה"]):
                                speak("מסתכל עליך...")
                                img = capture_webcam()
                            elif any(w in query for w in ["מסך", "תמונה", "רואה"]):
                                speak("מסתכל על המסך...")
                                img = capture_screen()
                        
                        chat_with_gpt(query, img, sel_txt)
        except Exception as e:
            print(f"Listen Loop Error: {e}")

if __name__ == "__main__":
    listen_loop()