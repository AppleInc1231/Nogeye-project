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

# --- ייבוא המוח החדש והזיכרון ---
from memory_engine import save_memory, retrieve_memory, save_episode
from consciousness import brain
# --- ייבוא מכונת המצבים החדשה ---
from conversation_state import state_machine, State

# השתקת אזהרות
warnings.filterwarnings("ignore")

# --- טעינת הגדרות ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "chat-voice-key.json")

# --- מנגנוני הגנה ויציבות ---
file_lock = threading.Lock() 

try:
    pygame.mixer.init()
except:
    pass

is_speaking = False
stop_flag = False
last_interaction_time = time.time()
is_dreaming = False

# Cache ליומן
calendar_cache = {"data": "לא נבדק", "timestamp": 0}

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
        
        # עדכון מצב: סיימנו לדבר
        # אם היינו בשיחה עמוקה, נשאר שם. אחרת חוזרים ל-IDLE
        if state_machine.interaction_count > 0:
             state_machine.set_state(State.DEEP_CONVERSATION)
        else:
             state_machine.set_state(State.IDLE)
             
    except Exception as e:
        print(f"Audio Play Error: {e}")
        is_speaking = False
        state_machine.set_state(State.IDLE)

def speak(text):
    global is_speaking, stop_flag
    
    # עדכון מצב: מדבר
    state_machine.set_state(State.SPEAKING)
    
    if is_speaking:
        stop_flag = True
        time.sleep(0.1)
    if not text or len(text.strip()) == 0:
        state_machine.set_state(State.IDLE) # שחרור מצב אם אין טקסט
        return

    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="he-IL", name=voice_id)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        
        with open(OUTPUT_AUDIO, "wb") as out:
            out.write(response.audio_content)
            
        # הפעלת הנגן בתהליך נפרד
        threading.Thread(target=play_audio_thread).start()
        
    except Exception as e:
        print(f"TTS Error: {e}")
        state_machine.set_state(State.IDLE) # שחרור במקרה שגיאה

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

# --- Cache ליומן ---
def get_calendar_events_cached():
    global calendar_cache
    if time.time() - calendar_cache["timestamp"] < 600: # 10 דקות
        return calendar_cache["data"]
    
    print("📅 מרענן יומן (Cache Expired)...")
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
        data = events if events else "היומן ריק להיום."
        calendar_cache = {"data": data, "timestamp": time.time()}
        return data
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
            subprocess.run(["open", "-a", line.replace("APP:", "").strip()])
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
        elif line.startswith("SEARCH_CMD:"):
            return search_web(line.replace("SEARCH_CMD:", "").strip())
        elif line.startswith("WATCH_VIDEO:"):
            return get_youtube_transcript(line.replace("WATCH_VIDEO:", "").strip())
        elif line.startswith("READ_URL:"):
            return read_url_content(line.replace("READ_URL:", "").strip())
            
    except:
        pass
    return None

def ask_gpt(messages):
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        return response.choices[0].message.content.strip()
    except:
        return None

# --- הוספתי את הפונקציה שהייתה חסרה בקוד הראשון ---
def startup_greeting():
    print("🌅 מכין תדרוך בוקר...")
    try:
        weather_info = search_web("weather Dallas")
        news_info = search_web("top news Dallas Texas")
    except:
        weather_info = news_info = "לא זמין"
    
    calendar_data = get_calendar_events_cached()
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

# --- פונקציית השיחה הראשית (הגרסה החכמה) ---
def chat_with_gpt(prompt, image_data=None, selected_context=None, extra_info=None, decision_data=None):
    global last_interaction_time
    last_interaction_time = time.time()
    update_relationship(impact=0.5)
    
    # עדכון מצב: חושב
    state_machine.set_state(State.THINKING)
    state_machine.increment_interaction() # ספירת אינטראקציה

    update_ui("מעבד נתונים...", prompt, "")
    
    memory = safe_read_json(MEMORY_PATH, {"conversations": []})
    calendar_data = get_calendar_events_cached()
    relevant_memories = retrieve_memory(prompt, n_results=4) 
    
    psyche_profile = safe_read_json(PSYCHE_PATH, {})
    rel = safe_read_json(RELATIONSHIP_PATH, {"affinity_score": 0, "relationship_tier": "Stranger"})
    
    # --- הזרקת החלטות המוח לפרומפט ---
    brain_instruction = ""
    if decision_data:
        style = decision_data.get('response_style', 'normal')
        
        if style == 'short_tired': brain_instruction = "STATUS: Low energy. Be very brief, almost tired. Don't elaborate."
        elif style == 'terse': brain_instruction = "STATUS: Annoyed. Be sharp, short, and to the point. No politeness."
        elif style == 'action_oriented': brain_instruction = "STATUS: HIGH URGENCY. Skip all pleasantries. Execute commands immediately."
        elif style == 'friendly_chatty': brain_instruction = "STATUS: High Affinity. Be warm, funny, use slang, be a 'bro'."
    
    current_time = datetime.now().strftime("%H:%M")
    recent_context = "\n".join(list(ambient_buffer))

    system_content = f"""
    IDENTITY: {json.dumps(psyche_profile)}
    RELATIONSHIP: {rel['relationship_tier']}
    
    BRAIN DIRECTIVE: {brain_instruction}
    
    CONTEXT:
    Time: {current_time}
    Calendar: {calendar_data}
    Recent Audio: {recent_context}
    Memory: {relevant_memories}
    
    MISSION: Analyze intent -> Strategize -> Act.
    
    STRICT COMMAND RULES:
    - To open apps: APP: Name
    - To search: SEARCH_CMD: query
    - To watch: WATCH_VIDEO: url
    - To note: REMEMBER: text
    - Commands must be on a separate line.
    
    TONE: Conversational, Israeli male, sharp, authentic. No robotic pleasantries.
    """
    
    messages = [{"role": "system", "content": system_content}]
    messages.extend(memory.get("conversations", [])[-6:])
    
    final_prompt = prompt
    if selected_context:
        final_prompt += f"\n\n[טקסט מסומן]:\n{selected_context}"
    if extra_info:
        final_prompt += f"\n\n[מידע נוסף]:\n{extra_info}"
        
    content_payload = [{"type": "text", "text": final_prompt}]
    if image_data:
        content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})
        
    messages.append({"role": "user", "content": content_payload})

    # --- Agent Loop ---
    turns = 0
    max_turns = 3
    
    while turns < max_turns:
        answer = ask_gpt(messages)
        if not answer:
            speak("החיבור נקטע לשנייה.")
            break

        lines = answer.split('\n')
        spoken_response = ""
        tool_output = None
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            cmd_result = execute_line(line)
            if cmd_result:
                tool_output = cmd_result
                update_ui("פעולה", prompt, f"מבצע: {line}")
            
            if not any(line.startswith(cmd) for cmd in ["APP:", "WEBSITE:", "TYPE:", "REMEMBER:", "WHATSAPP:", "SYSTEM:", "CLOSE:", "CREATE_FILE:", "SET_WALLPAPER:", "ADD_EVENT:", "SAVE_EPISODE:", "SEARCH_CMD:", "WATCH_VIDEO:", "READ_URL:", "AGENT_MODE:", "EVOLVE", "GENERATE_IMAGE:", "FIND:"]):
                spoken_response += line + " "

        if spoken_response.strip():
            update_internal_monologue(f"אמרתי למאור: {spoken_response[:50]}...")
            update_ui("מדבר", prompt, spoken_response)
            speak(spoken_response)
            print(f"Nog: {spoken_response}")
            
        memory["conversations"].append({"role": "user", "content": final_prompt})
        memory["conversations"].append({"role": "assistant", "content": answer})
        safe_write_json(MEMORY_PATH, memory)

        if tool_output:
            messages.append({"role": "assistant", "content": answer})
            messages.append({"role": "system", "content": f"Command Result: {tool_output}. Now respond to Maor based on this."})
            turns += 1
            final_prompt = "" 
        else:
            break

def proactive_check_loop():
    print("💓 דופק מודעות הופעל (כולל ראייה פסיבית)...")
    
    last_vision_time = 0
    vision_interval = 600 
    check_interval = 300   

    while True:
        time.sleep(60) 
        if is_speaking: continue
        
        current_time = time.time()
        
        # --- שלב 1: ראייה פסיבית ---
        if current_time - last_vision_time > vision_interval:
            print("👁️ מבצע סריקה ויזואלית שקטה...")
            img_data = capture_webcam()
            if img_data:
                try:
                    vision_prompt = "ניתוח סיטואציה: תאר במשפט אחד מה רואים בחדר. אל תדבר למשתמש."
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are Nog's visual cortex. Analyze the image briefly for internal context only."},
                            {"role": "user", "content": [
                                {"type": "text", "text": vision_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}
                            ]}
                        ],
                        max_tokens=50
                    )
                    visual_context = response.choices[0].message.content.strip()
                    print(f"👁️ ראיתי: {visual_context}")
                    ambient_buffer.append(f"[ראייה {datetime.now().strftime('%H:%M')}]: {visual_context}")
                    last_vision_time = current_time
                except Exception as e:
                    print(f"Vision Error: {e}")

        # --- שלב 2: מחשבה ויוזמה (דרך המוח החדש) ---
        if current_time % check_interval < 60: 
            # התייעצות עם המוח האם ליזום
            decision = brain.process_input("Proactive check", "proactive")
            
            if decision["should_respond"]:
                prompt = "יזום פנייה קצרה למאור בהתבסס על ההקשר (ראייה/שמע אחרונים)."
                chat_with_gpt(prompt, decision_data=decision)
            else:
                psyche = load_psyche()
                curr_clock = datetime.now().strftime("%H:%M")
                calendar_data = get_calendar_events_cached()
                recent_context = "\n".join(list(ambient_buffer))
                
                thought_prompt = f"""
                Identity: Nog. Time: {curr_clock}. Context: {recent_context}. Calendar: {calendar_data}.
                Generate a short internal thought about the situation (no speaking).
                """
                try:
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": thought_prompt}])
                    thought = res.choices[0].message.content.strip()
                    print(f"💭 מחשבה שקטה: {thought}")
                    update_internal_monologue(thought)
                except: pass

def listen_loop():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    update_ui("מוכנה")
    print("\n🎤 --- Nog Connected to Brain (V5) ---")
    
    # עכשיו הפונקציה מוגדרת ולא תהיה שגיאה
    threading.Thread(target=startup_greeting).start()
    threading.Thread(target=proactive_check_loop, daemon=True).start()
    threading.Thread(target=subconscious_loop, daemon=True).start()

    while True:
        # בדיקה האם מותר להקשיב (מכונת מצבים)
        if not state_machine.should_listen():
            time.sleep(0.1)
            continue

        try:
            with mic as source:
                try:
                    audio = recognizer.listen(source, timeout=0.8, phrase_time_limit=8)
                except sr.WaitTimeoutError:
                    continue 
                try:
                    text = recognizer.recognize_google(audio, language="he-IL").lower()
                except:
                    continue

                if text:
                    if any(w in text for w in ["עצור", "שתוק", "חלאס", "stop"]):
                        global stop_flag
                        if is_speaking:
                            stop_flag = True
                            print("🛑 קטיעת דיבור זוהתה.")
                            continue

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
                        
                        # --- התייעצות עם המוח המרכזי לפני תגובה ---
                        decision = brain.process_input(query, "speech")
                        
                        if decision["should_respond"]:
                            chat_with_gpt(query, img, sel_txt, decision_data=decision)
                        else:
                            print(f"🧠 המוח החליט להתעלם: {decision['internal_reasoning']}")
                            update_ui("מתעלם")
                            
        except Exception as e:
            print(f"Listen Loop Error: {e}")

if __name__ == "__main__":
    listen_loop()