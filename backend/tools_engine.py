import os
import subprocess
import webbrowser
import time
import pyautogui
import pyperclip
import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from dotenv import load_dotenv
from memory_engine import save_memory, save_episode

# --- ייבוא מותנה למנועי חיפוש ופיננסים (מונע קריסה אם חסר) ---
try:
    from googlesearch import search
except ImportError:
    search = None

try:
    import yfinance as yf
except ImportError:
    yf = None

# --- טעינת הגדרות ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

# --- פונקציית עזר לעדכון ה-Frontend (הבועות הסגולות) ---
def broadcast_tool_activity(message):
    try:
        # איתור הנתיב לקובץ ה-JSON של הממשק
        live_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "live.json")
        
        current_data = {}
        # קריאה זהירה של מה שכבר יש שם
        if os.path.exists(live_json_path):
            with open(live_json_path, "r", encoding="utf-8") as f:
                try:
                    current_data = json.load(f)
                except: pass
        
        # עדכון הסטטוס בלבד
        current_data["status"] = message
        
        # שמירה חזרה
        with open(live_json_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Broadcast Error: {e}")

class ToolsEngine:
    """
    מנהל את כל הכלים והיכולות הטכניות של Nog.
    כולל: חיפוש חכם (פיננסי + גוגל), שליטה במחשב, וואטסאפ ויוטיוב.
    """
    
    def handle_command(self, command_line):
        """
        מקבל שורת פקודה ומבצע אותה.
        """
        command_line = command_line.strip()
        if not command_line: return None
        
        try:
            # --- חיפוש חכם (השינוי הגדול) ---
            if command_line.startswith("SEARCH_CMD:"):
                query = command_line.replace("SEARCH_CMD:", "").strip()
                return self.search_smart(query)

            # --- שאר הפקודות המקוריות שלך ---
            elif command_line.startswith("WEBSITE:"):
                url = command_line.replace("WEBSITE:", "").strip()
                webbrowser.open(url)
                return "פתחתי את האתר."
                
            elif command_line.startswith("APP:"):
                app_name = command_line.replace("APP:", "").strip()
                subprocess.run(["open", "-a", app_name])
                return f"פתחתי את {app_name}."
                
            elif command_line.startswith("TYPE:"):
                text = command_line.replace("TYPE:", "").strip()
                pyperclip.copy(text)
                pyautogui.hotkey('command', 'v')
                return "הקלדתי."
                
            elif command_line.startswith("REMEMBER:"):
                content = command_line.replace("REMEMBER:", "").strip()
                return save_memory(content, importance="high")
                
            elif command_line.startswith("WHATSAPP:"): 
                parts = command_line.replace("WHATSAPP:", "").split(",", 1)
                if len(parts) == 2:
                    return self._send_whatsapp(parts[0].strip(), parts[1].strip())
                    
            elif command_line.startswith("SYSTEM:"):
                action = command_line.replace("SYSTEM:", "").strip()
                return self._control_system(action)
                
            elif command_line.startswith("CLOSE:"):
                app = command_line.replace("CLOSE:", "").strip()
                return self._close_app(app)
                
            elif command_line.startswith("FIND:"):
                query = command_line.replace("FIND:", "").strip()
                return self._find_files(query)
                
            elif command_line.startswith("CREATE_FILE:"):
                parts = command_line.replace("CREATE_FILE:", "").split("|||", 1)
                if len(parts) == 2:
                    return self._create_file(parts[0].strip(), parts[1].strip())
                    
            elif command_line.startswith("GENERATE_IMAGE:"):
                prompt = command_line.replace("GENERATE_IMAGE:", "").strip()
                return self._generate_image(prompt)
                
            elif command_line.startswith("SET_WALLPAPER:"):
                path = command_line.replace("SET_WALLPAPER:", "").strip()
                return self._set_wallpaper(path)
                
            elif command_line.startswith("WATCH_VIDEO:"):
                url = command_line.replace("WATCH_VIDEO:", "").strip()
                return self._get_youtube_transcript(url)
                
            elif command_line.startswith("READ_URL:"):
                url = command_line.replace("READ_URL:", "").strip()
                return self._read_url_content(url)

            elif command_line.startswith("ADD_EVENT:"):
                parts = command_line.replace("ADD_EVENT:", "").split("|||", 1)
                if len(parts) == 2:
                    return self.add_calendar_event(parts[0].strip(), parts[1].strip())

            elif command_line.startswith("AGENT_MODE:"):
                goal = command_line.replace("AGENT_MODE:", "").strip()
                return self.start_autonomous_agent(goal)

            elif command_line.startswith("SAVE_EPISODE:"):
                parts = command_line.replace("SAVE_EPISODE:", "").split("|||")
                if len(parts) >= 3:
                    return save_episode(parts[0].strip(), parts[1].strip(), parts[2].strip(), "medium")
                
        except Exception as e:
            print(f"Tool Error: {e}")
            return f"שגיאה בביצוע הפעולה: {e}"
            
        return None

    # --- חיפוש חכם: קריפטו/מניות דרך Yahoo, כל השאר דרך Google ---
    def search_smart(self, query):
        broadcast_tool_activity(f"בודק מידע על: {query}...")
        
        # 1. בדיקה אם זה עניין כספי (ביטקוין, מניות)
        query_lower = query.lower()
        finance_keywords = ["bitcoin", "btc", "price", "stock", "מחיר", "ביטקוין", "מניה", "שער", "ethereum", "eth"]
        
        if yf and any(w in query_lower for w in finance_keywords):
            print(f"📈 Yahoo Finance Check: {query}")
            try:
                symbol = None
                if "bitcoin" in query_lower or "btc" in query_lower or "ביטקוין" in query_lower:
                    symbol = "BTC-USD"
                elif "ethereum" in query_lower or "eth" in query_lower:
                    symbol = "ETH-USD"
                elif "apple" in query_lower:
                    symbol = "AAPL"
                elif "google" in query_lower:
                    symbol = "GOOGL"
                elif "tesla" in query_lower:
                    symbol = "TSLA"
                elif "microsoft" in query_lower:
                    symbol = "MSFT"
                elif "nvidia" in query_lower:
                    symbol = "NVDA"
                
                if symbol:
                    broadcast_tool_activity(f"מושך נתונים פיננסיים: {symbol}")
                    ticker = yf.Ticker(symbol)
                    # משיכת מחיר בזמן אמת (או סגירה אחרונה)
                    data = ticker.history(period="1d")
                    if not data.empty:
                        last_price = data['Close'].iloc[-1]
                        return f"המחיר הנוכחי של {symbol} הוא ${last_price:,.2f}."
            except Exception as e:
                print(f"Finance Error: {e}")
                # אם נכשל ב-Yahoo, ממשיכים לגוגל כרגיל

        # 2. חיפוש בגוגל (ברירת מחדל לכל השאר)
        return self.search_web(query)

    def search_web(self, query):
        """פונקציה פומבית לחיפוש (מנוע Google)"""
        try:
            broadcast_tool_activity(f"מחפש בגוגל: {query}")
            print(f"🔎 Google Search: {query}")
            
            if not search:
                return "מנוע החיפוש (googlesearch) לא מותקן."
            
            results_text = ""
            # advanced=True נותן לנו גם כותרת ותיאור
            count = 0
            for result in search(query, num_results=3, advanced=True):
                title = result.title
                desc = result.description
                url = result.url
                results_text += f"\nתוצאה {count+1}: {title}\n{desc}\n({url})\n"
                count += 1
            
            if not results_text:
                # ניסיון גיבוי לחיפוש רגיל (רק לינקים) אם ה-advanced נכשל
                for url in search(query, num_results=3):
                    results_text += f"- {url}\n"
            
            return results_text if results_text else "לא נמצאו תוצאות בגוגל."

        except Exception as e:
            print(f"❌ Google Error: {e}")
            return f"שגיאה בחיפוש: {str(e)}"

    # --- שאר המימושים (ללא שינוי מהקוד המקורי שלך) ---

    def add_calendar_event(self, title, date_time_str):
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

    def start_autonomous_agent(self, goal):
        print(f"🤖 סוכן אוטונומי התחיל: {goal}")
        history = []
        max_steps = 5 
        
        for i in range(max_steps):
            broadcast_tool_activity(f"סוכן אוטונומי: שלב {i+1}")
            agent_prompt = f"""You are in AGENT MODE. Goal: {goal}. History: {history}.
            Return ONLY one command: SEARCH_CMD, READ_URL, WATCH_VIDEO, CREATE_FILE, FIND, ADD_EVENT, DONE: result"""
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[{"role": "user", "content": agent_prompt}]
                )
                next_step = response.choices[0].message.content.strip()
                
                if "DONE:" in next_step:
                    return f"משימה הושלמה: {next_step.replace('DONE:', '').strip()}"
                
                result = self.handle_command(next_step)
                history.append(f"Step: {next_step} -> Result: {str(result)[:200]}...")
            except Exception as e:
                return f"שגיאה בסוכן: {e}"
            
        return "הגעתי למקסימום צעדים. " + str(history)

    def _read_url_content(self, url):
        broadcast_tool_activity("קורא תוכן דף אינטרנט...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            clean_text = '\n'.join(chunk for line in lines for chunk in line.split("  ") if chunk)
            return clean_text[:4000]
        except Exception as e: return f"שגיאה בקריאה: {e}"

    def _get_youtube_transcript(self, video_url):
        broadcast_tool_activity("מוריד תמלול וידאו...")
        try:
            if "v=" in video_url: video_id = video_url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in video_url: video_id = video_url.split("/")[-1]
            else: return "לינק לא תקין."
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['he', 'en'])
            except: 
                t_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = t_list.find_generated_transcript(['en', 'he']).fetch()
            full_text = " ".join([t['text'] for t in transcript])
            return full_text[:6000]
        except Exception as e: return f"שגיאה ביוטיוב: {e}"

    def _control_system(self, action):
        cmd = ""
        if action == "VOL_UP": cmd = "set volume output volume (output volume of (get volume settings) + 10)"
        elif action == "VOL_DOWN": cmd = "set volume output volume (output volume of (get volume settings) - 10)"
        elif action == "MUTE": cmd = "set volume output muted true"
        elif action == "UNMUTE": cmd = "set volume output muted false"
        
        if cmd:
            os.system(f"osascript -e '{cmd}'")
            return "בוצע."
        return "פקודה לא מוכרת."

    def _close_app(self, app_name):
        try:
            script = f'quit app "{app_name}"'
            os.system(f"osascript -e '{script}'")
            return f"סגרתי את {app_name}."
        except: return "תקלה בסגירה."

    def _find_files(self, query):
        try:
            cmd = ["mdfind", "-name", query]
            result = subprocess.run(cmd, capture_output=True, text=True)
            paths = result.stdout.strip().split('\n')[:5]
            if not paths or paths == ['']: return "לא מצאתי קבצים."
            return "קבצים שנמצאו:\n" + "\n".join(paths)
        except: return "שגיאה בחיפוש."

    def _create_file(self, filename, content):
        try:
            if "." not in filename: filename += ".txt"
            file_path = os.path.join(DESKTOP_PATH, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"יצרתי את הקובץ {filename}."
        except: return "שגיאה ביצירת קובץ."

    def _generate_image(self, prompt):
        broadcast_tool_activity(f"מייצר תמונה: {prompt}")
        try:
            response = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1)
            image_url = response.data[0].url
            img_data = requests.get(image_url).content
            filename = f"nog_art_{int(time.time())}.png"
            file_path = os.path.join(DESKTOP_PATH, filename)
            with open(file_path, 'wb') as handler:
                handler.write(img_data)
            return f"נשמר: {file_path}"
        except Exception as e: return f"שגיאה: {e}"

    def _set_wallpaper(self, image_path):
        try:
            script = f'tell application "System Events" to set picture of every desktop to "{image_path}"'
            subprocess.run(["osascript", "-e", script])
            return "הטפט הוחלף."
        except: return "תקלה בהחלפת טפט."

    def _send_whatsapp(self, contact_name, message):
        broadcast_tool_activity(f"שולח וואטסאפ ל-{contact_name}")
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

# יצירת מופע יחיד לשימוש
tools = ToolsEngine()