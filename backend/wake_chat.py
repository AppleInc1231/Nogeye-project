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
import cv2
import subprocess
import pyperclip
from datetime import datetime, timedelta
from collections import deque
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI

# --- ייבוא Azure Speech (קול עברית מושלם) ---
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("⚠️  Azure Speech לא מותקן - משתמש ב-Google TTS")
    from google.cloud import texttospeech

# --- ייבוא המוח, הזיכרון והכלים ---
from memory_engine import save_memory, retrieve_memory, save_episode, consolidate_memory
from consciousness import brain
from conversation_state import state_machine, State
from tools_engine import tools 

# השתקת אזהרות
warnings.filterwarnings("ignore")

# --- טעינת הגדרות ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- אתחול Azure Speech או Google ---
if AZURE_AVAILABLE:
    azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
    azure_region = os.getenv("AZURE_SPEECH_REGION")
    speech_config = speechsdk.SpeechConfig(subscription=azure_speech_key, region=azure_region)
    speech_config.speech_synthesis_voice_name = "he-IL-AvriNeural"  # קול גברי ישראלי
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    print("🎤 Azure Speech Engine: ACTIVE (Avri - Israeli Male Voice)")
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "chat-voice-key.json")
    tts_client = texttospeech.TextToSpeechClient()
    voice_id = "he-IL-Wavenet-D"
    print("🎤 Google TTS: ACTIVE (fallback)")

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

# --- UI ---
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
        
        if state_machine.interaction_count > 0:
             state_machine.set_state(State.DEEP_CONVERSATION)
        else:
             state_machine.set_state(State.IDLE)
             
    except Exception as e:
        print(f"Audio Play Error: {e}")
        is_speaking = False
        state_machine.set_state(State.IDLE)

# ═══════════════════════════════════════════════════════════
# 🎤 מנוע TTS משודרג - Azure (קול עברית מושלם)
# ═══════════════════════════════════════════════════════════

def clean_text_for_tts(text):
    """
    מנקה טקסט לפני TTS:
    1. מסיר תווים מיוחדים של XML
    2. מנקה שורות ריקות
    3. מסיר רווחים מיותרים
    """
    import html
    
    # ניקוי בסיסי
    text = text.strip()
    
    # Escape תווי XML מיוחדים
    text = html.escape(text)
    
    # מסיר שורות ריקות מרובות
    text = ' '.join(text.split())
    
    # מגביל אורך (Azure מקסימום 3000 תווים)
    if len(text) > 3000:
        text = text[:3000]
    
    return text

def speak(text):
    global is_speaking, stop_flag
    
    state_machine.set_state(State.SPEAKING)
    
    if is_speaking:
        stop_flag = True
        time.sleep(0.1)
    if not text or len(text.strip()) == 0:
        state_machine.set_state(State.IDLE)
        return

    try:
        # ניקוי הטקסט לפני TTS
        clean_text = clean_text_for_tts(text)
        
        print(f"🗣️ Speaking: {clean_text[:50]}...")  # הדפסת התחלת הטקסט לדיבאג
        
        current_mood = brain.emotion_engine.momentum 
        current_energy = brain.emotion_engine.energy 
        
        # --- Azure Speech: קול עברי אמיתי עם רגש ---
        if AZURE_AVAILABLE:
            # התאמת הקול לפי רגש
            rate = "0%"  # ברירת מחדל (מהירות רגילה)
            pitch = "0%"  # ברירת מחדל (גובה רגיל)
            
            if current_mood < -0.4:  # עצבני
                rate = "+10%"  # מהר יותר
                pitch = "-5%"  # נמוך יותר (רציני)
            elif current_energy < 0.4:  # עייף
                rate = "-10%"  # לאט יותר
                pitch = "-3%"  # קצת נמוך
            elif current_mood > 0.6:  # שמח
                rate = "+5%"  # קצת מהר
                pitch = "+5%"  # גבוה יותר (שמח)
            
            # SSML עם רגש (עכשיו עם טקסט מנוקה!)
            ssml = f"""
            <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='he-IL'>
                <voice name='he-IL-AvriNeural'>
                    <prosody rate='{rate}' pitch='{pitch}'>
                        {clean_text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # הגדרת פורמט אודיו
            audio_config = speechsdk.audio.AudioOutputConfig(filename=OUTPUT_AUDIO)
            
            # יצירת synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            # סינתוז הדיבור
            result = synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # הצלחה - נגן את הקול
                pass
            else:
                print(f"Azure TTS Error: {result.reason}")
                if result.reason == speechsdk.ResultReason.Canceled:
                    cancellation = result.cancellation_details
                    print(f"Error details: {cancellation.error_details}")
                state_machine.set_state(State.IDLE)
                return
        
        # --- Google TTS: גיבוי ---
        else:
            speaking_rate = 1.0
            if current_mood < -0.4: 
                speaking_rate = 1.2
            elif current_energy < 0.4: 
                speaking_rate = 0.9
            elif current_mood > 0.6: 
                speaking_rate = 1.1

            ssml_text = f"""
            <speak>
                <prosody rate="{speaking_rate}">
                    {text}
                </prosody>
            </speak>
            """

            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            voice = texttospeech.VoiceSelectionParams(language_code="he-IL", name=voice_id)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
            
            with open(OUTPUT_AUDIO, "wb") as out:
                out.write(response.audio_content)
        
        # נגן את הקול
        threading.Thread(target=play_audio_thread).start()
        
    except Exception as e:
        print(f"TTS Error: {e}")
        state_machine.set_state(State.IDLE)

# --- ראייה (Input Only) ---
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

# --- Cache ליומן ---
def get_calendar_events_cached():
    global calendar_cache
    if time.time() - calendar_cache["timestamp"] < 600: 
        return calendar_cache["data"]
    
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
            save_memory(f"בזמן חלימה למדתי: {', '.join(new_rules)}", importance="high")
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
            
            try:
                consolidate_memory()
            except Exception as e:
                print(f"Consolidation Error: {e}")
                
            update_ui("חולם", "", "מבצע אופטימיזציה...")
            perform_self_reflection(auto_mode=True)
            print("☀️ סיימתי לחלום.")
            update_ui("מוכנה")

def ask_gpt(messages):
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        return response.choices[0].message.content.strip()
    except:
        return None

# --- תדרוך בוקר ---
def startup_greeting():
    print("🌅 מכין תדרוך בוקר...")
    
    try:
        weather_info = tools.search_web_ddg("weather Dallas")
    except:
        weather_info = "לא זמין"

    calendar_data = get_calendar_events_cached()
    mood = get_mood()
    rel = load_relationship_state()
    current_time = datetime.now().strftime("%A, %d/%m/%Y, %H:%M")
    
    system_content = f"""אתה Nog. ישות חכמה. זמן: {current_time}. מיקום: Dallas, TX.
    מצב רוח: {mood['current_mood']}, קשר: {rel['relationship_tier']}
    [יומן]: {calendar_data}
    חוץ: {weather_info}
    משימה: תדרוך בוקר קצר בטון שמתאים לרמת הקשר.
    """
    greeting = ask_gpt([{"role": "system", "content": system_content}])
    if greeting:
        update_ui("מדבר", "", greeting)
        speak(greeting)

def generate_deep_thought(user_text, ai_response):
    """מייצרת מחשבה אנליטית עמוקה"""
    try:
        psyche = load_psyche()
        mood = get_mood()
        
        prompt = f"""
        ANALYSIS MODE.
        My Identity: {json.dumps(psyche)}
        Current Mood: {mood.get('current_mood')}
        
        INTERACTION:
        User: "{user_text}"
        Me: "{ai_response}"
        
        MISSION: Write 1 short sentence of internal monologue.
        DO NOT summarize what was said.
        INSTEAD: Analyze the user's hidden emotion, intent, or plan my next strategy.
        
        Output (Hebrew/English):
        """
        
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": prompt}],
            max_tokens=60
        )
        thought = response.choices[0].message.content.strip()
        update_internal_monologue(thought)
        return thought
    except Exception as e:
        print(f"Thought Error: {e}")
        return None

# --- פונקציית השיחה הראשית ---
def chat_with_gpt(prompt, image_data=None, selected_context=None, extra_info=None, decision_data=None):
    global last_interaction_time
    last_interaction_time = time.time()
    update_relationship(impact=0.5)
    
    state_machine.set_state(State.THINKING)
    state_machine.increment_interaction() 

    update_ui("מעבד נתונים...", prompt, "")
    
    memory = safe_read_json(MEMORY_PATH, {"conversations": []})
    calendar_data = get_calendar_events_cached()
    relevant_memories = retrieve_memory(prompt, n_results=4) 
    
    psyche_profile = safe_read_json(PSYCHE_PATH, {})
    rel = safe_read_json(RELATIONSHIP_PATH, {"affinity_score": 0, "relationship_tier": "Stranger"})
    
    brain_instruction = ""
    if decision_data:
        style = decision_data.get('response_style', 'normal')
        
        if style == 'short_tired': 
            brain_instruction = "STATUS: Low energy. Be very brief, almost tired. Don't elaborate."
        elif style == 'terse': 
            brain_instruction = "STATUS: Annoyed. Be sharp, short, and to the point. No politeness."
        elif style == 'action_oriented': 
            brain_instruction = "STATUS: HIGH URGENCY. Skip all pleasantries. Execute commands immediately."
        elif style == 'friendly_chatty': 
            brain_instruction = "STATUS: High Affinity. Be warm, funny, use slang, be a 'bro'."
    
    current_time = datetime.now().strftime("%H:%M")
    recent_context = "\n".join(list(ambient_buffer))

    learned_rules_text = decision_data.get('learned_context', 'None') if decision_data else 'None'

    system_content = f"""
    IDENTITY: {json.dumps(psyche_profile)}
    RELATIONSHIP: {rel['relationship_tier']}
    LEARNED RULES (EVOLUTION): {learned_rules_text}
    
    BRAIN DIRECTIVE: {brain_instruction}
    
    *** IMPORTANT: YOU HAVE REAL-TIME INTERNET ACCESS ***
    If the user asks for prices (Bitcoin, stocks), news, or real-time facts:
    You MUST output the command: SEARCH_CMD: query
    Do NOT say "I cannot browse". You CAN via this command.
    
    CONTEXT:
    Time: {current_time}
    Calendar: {calendar_data}
    Recent Audio: {recent_context}
    Memory: {relevant_memories}
    
    MISSION: Analyze intent -> Strategize -> Act.
    
    COMMANDS (One per line):
    APP: Name | WEBSITE: url | SEARCH_CMD: query | WATCH_VIDEO: url | REMEMBER: text
    WHATSAPP: name, msg | SYSTEM: VOL_UP/DOWN/MUTE | CLOSE: app | FIND: file
    CREATE_FILE: name ||| content | GENERATE_IMAGE: prompt | ADD_EVENT: title at date
    AGENT_MODE: goal | SAVE_EPISODE: desc ||| emotion_u ||| emotion_ai
    
    TONE: Conversational, Israeli male, sharp, authentic. No robotic pleasantries.
    """
    
    messages = [{"role": "system", "content": system_content}]
    messages.extend(memory.get("conversations", [])[-50:])
    
    final_prompt = prompt
    if selected_context:
        final_prompt += f"\n\n[טקסט מסומן]:\n{selected_context}"
    if extra_info:
        final_prompt += f"\n\n[מידע נוסף]:\n{extra_info}"
        
    content_payload = [{"type": "text", "text": final_prompt}]
    if image_data:
        content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})
        
    messages.append({"role": "user", "content": content_payload})

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
            if not line: 
                continue
            
            cmd_result = tools.handle_command(line)
            
            if cmd_result:
                tool_output = cmd_result
                update_ui("פעולה", prompt, f"מבצע: {line}")
            
            if not cmd_result:
                if not any(line.startswith(cmd) for cmd in ["APP:", "WEBSITE:", "TYPE:", "REMEMBER:", "WHATSAPP:", "SYSTEM:", "CLOSE:", "CREATE_FILE:", "SET_WALLPAPER:", "ADD_EVENT:", "SAVE_EPISODE:", "SEARCH_CMD:", "WATCH_VIDEO:", "READ_URL:", "AGENT_MODE:", "EVOLVE", "GENERATE_IMAGE:", "FIND:"]):
                    spoken_response += line + " "

        if spoken_response.strip():
            update_ui("מדבר", prompt, spoken_response)
            speak(spoken_response)
            print(f"Nog: {spoken_response}")
            threading.Thread(target=generate_deep_thought, args=(prompt, spoken_response)).start()
            
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
    print("💓 דופק מודעות הופעל...")
    
    last_vision_time = 0
    vision_interval = 1800
    check_interval = 300   

    while True:
        time.sleep(60) 
        if is_speaking: 
            continue
        
        current_hour = datetime.now().hour
        if 23 <= current_hour or current_hour < 7:
            continue

        current_time = time.time()
        
        if current_time - last_vision_time > vision_interval:
            print("👁️ מבצע סריקה ויזואלית שקטה...")
            img_data = capture_webcam()
            if img_data:
                try:
                    vision_prompt = "ניתוח סיטואציה: תאר במשפט אחד מה רואים בחדר."
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Analyze image context briefly."},
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

        if current_time % check_interval < 60: 
            decision = brain.process_input("Proactive check", "proactive")
            
            if decision["should_respond"]:
                prompt = "יזום פנייה קצרה למאור בהתבסס על ההקשר."
                chat_with_gpt(prompt, decision_data=decision)
            else:
                psyche = load_psyche()
                curr_clock = datetime.now().strftime("%H:%M")
                calendar_data = get_calendar_events_cached()
                
                thought_prompt = f"""
                Identity: Nog. Time: {curr_clock}. Calendar: {calendar_data}.
                Generate a short internal thought about the situation.
                """
                try:
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": thought_prompt}])
                    thought = res.choices[0].message.content.strip()
                    update_internal_monologue(thought)
                except: 
                    pass

# --- לולאת ההקשבה ---
def listen_loop():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
    update_ui("מוכנה")
    print("\n🎤 --- Nog Connected to Brain (Azure Hebrew Voice Ready) ---")
    
    threading.Thread(target=startup_greeting).start()
    threading.Thread(target=proactive_check_loop, daemon=True).start()
    threading.Thread(target=subconscious_loop, daemon=True).start()

    while True:
        try:
            with mic as source:
                try:
                    audio = recognizer.listen(source, timeout=0.8, phrase_time_limit=5)
                except sr.WaitTimeoutError:
                    continue 
                try:
                    text = recognizer.recognize_google(audio, language="he-IL").lower()
                except:
                    continue

                if text:
                    if is_speaking:
                        if any(w in text for w in ["עצור", "שתוק", "חלאס", "stop", "מספיק", "רגע"]):
                            print("🛑 פקודת עצירה זוהתה! משתיק...")
                            global stop_flag
                            stop_flag = True
                            pygame.mixer.music.stop()
                            update_ui("הושתק")
                            continue
                        else:
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
                        
                        decision = brain.process_input(query, "speech")
                        
                        if decision["should_respond"]:
                            chat_with_gpt(query, img, sel_txt, decision_data=decision)
                        else:
                            update_ui("מתעלם")
                            
        except Exception as e:
            print(f"Listen Loop Error: {e}")

if __name__ == "__main__":
    listen_loop()