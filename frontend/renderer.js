const fs = require('fs');
const path = require('path');
const { ipcRenderer } = require('electron');

// --- הגדרת נתיבים ---
const DATA_DIR = path.join(__dirname, '..', 'data');
const LIVE_JSON_PATH = path.join(__dirname, 'live.json');
const MOOD_PATH = path.join(DATA_DIR, 'mood.json');
const MONOLOGUE_PATH = path.join(DATA_DIR, 'internal_monologue.json');
const INBOX_PATH = path.join(DATA_DIR, 'inbox.json'); // הוספנו את זה מהקובץ הישן

// --- אלמנטים ב-HTML ---
const orb = document.getElementById('orb');
const statusDiv = document.getElementById('status');
const transDiv = document.getElementById('transcription');
const respDiv = document.getElementById('response');
const thoughtDiv = document.getElementById('thought-bubble');

// אלמנטים של המדדים
const moodVal = document.getElementById('mood-val');
const moodBar = document.getElementById('mood-bar');
const energyVal = document.getElementById('energy-val');
const energyBar = document.getElementById('energy-bar');

// משתנה עזר כדי לא לרענן את המסך בזמן גרירה
let isDragging = false;

// --- כפתור סגירה ---
const closeBtn = document.getElementById('close-btn');
if (closeBtn) {
    document.getElementById('close-btn').addEventListener('click', () => {
        ipcRenderer.send('close-app');
    });
}

// --- פונקציית עזר לקריאה בטוחה ---
function safeReadJson(filePath) {
    try {
        if (fs.existsSync(filePath)) {
            const raw = fs.readFileSync(filePath, 'utf-8');
            return JSON.parse(raw);
        }
    } catch (e) { return null; }
    return null;
}

// --- לוגיקה של גרירת קבצים (Drag & Drop) ---
document.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    isDragging = true;
    orb.classList.add('thinking'); // משתמשים באנימציה קיימת לסימון
    statusDiv.innerText = "📂 זרוק עליי את הקובץ!";
    thoughtDiv.innerText = "אני מוכן לקבל את המידע...";
});

document.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    isDragging = false;
    statusDiv.innerText = "ממתין";
});

document.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    isDragging = false;
    
    if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        const filePath = file.path; 
        
        statusDiv.innerText = "📥 קולט קובץ...";
        sendToInbox("file_upload", filePath);
    }
});

// פונקציה לכתיבה לתיבת הדואר של פייתון
function sendToInbox(type, data) {
    const message = {
        type: type,
        content: data,
        timestamp: Date.now()
    };
    try {
        fs.writeFileSync(INBOX_PATH, JSON.stringify(message));
        console.log("Sent to inbox:", message);
    } catch (err) {
        console.error("Error writing to inbox:", err);
    }
}

// --- הלוגיקה הראשית (UI Update Loop) ---
function updateUI() {
    // אם המשתמש גורר קובץ כרגע, לא נרענן את המסך כדי לא להפריע לו
    if (isDragging) return;

    // 1. עדכון סטטוס וצ'אט (live.json)
    const liveData = safeReadJson(LIVE_JSON_PATH);
    if (liveData) {
        statusDiv.innerText = liveData.status || "ממתין";
        
        if (liveData.user) {
            transDiv.innerText = `"${liveData.user}"`;
            transDiv.style.opacity = 1;
        } else {
            transDiv.style.opacity = 0.5;
        }

        if (liveData.chat) {
            respDiv.innerText = liveData.chat;
        }

        // עדכון אנימציית ה-Orb
        orb.className = ""; 
        if (liveData.status.includes("מאזין")) orb.classList.add("listening");
        else if (liveData.status.includes("חושב") || liveData.status.includes("מעבד")) orb.classList.add("thinking");
        else if (liveData.status.includes("מדבר") || liveData.status.includes("פעולה")) orb.classList.add("speaking");
    }

    // 2. עדכון מדדים ביומטריים (mood.json)
    const moodData = safeReadJson(MOOD_PATH);
    if (moodData && energyBar && moodBar) {
        const energy = moodData.energy_level !== undefined ? moodData.energy_level : 100;
        energyVal.innerText = energy + "%";
        energyBar.style.width = energy + "%";
        energyBar.style.background = energy > 40 ? "#00ff9d" : "#ff4444";

        let momentum = moodData.momentum !== undefined ? moodData.momentum : 0;
        moodVal.innerText = momentum.toFixed(2);
        const normalizedWidth = ((momentum + 1) / 2) * 100;
        moodBar.style.width = `${Math.max(5, Math.min(100, normalizedWidth))}%`; 
        moodBar.style.background = momentum < -0.2 ? "#ff4444" : "#00f2ff";
    }

    // 3. עדכון מחשבות (internal_monologue.json)
    const monoData = safeReadJson(MONOLOGUE_PATH);
    if (monoData && monoData.last_thoughts && monoData.last_thoughts.length > 0 && thoughtDiv) {
        const lastThought = monoData.last_thoughts[monoData.last_thoughts.length - 1];
        const cleanThought = lastThought.replace(/\[.*?\]/, '').trim();
        thoughtDiv.innerText = "💭 " + (cleanThought.length > 80 ? cleanThought.substring(0, 80) + "..." : cleanThought);
    }
}

// הפעלה כל 150 מילי-שניות
setInterval(updateUI, 150);