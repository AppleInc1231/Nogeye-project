const fs = require('fs');
const path = require('path');

// נתיב לקובץ הסטטוס החי
const LIVE_JSON_PATH = path.join(__dirname, 'live.json');

// אלמנטים גרפיים
const orb = document.getElementById('orb');
const statusDiv = document.getElementById('status');
const transDiv = document.getElementById('transcription');
const respDiv = document.getElementById('response');

function updateUI() {
    try {
        if (fs.existsSync(LIVE_JSON_PATH)) {
            // קריאת המידע מהמוח
            const rawData = fs.readFileSync(LIVE_JSON_PATH, 'utf-8');
            const data = JSON.parse(rawData);
            
            // 1. עדכון טקסטים
            statusDiv.innerText = data.status || "ממתין";
            
            // מציג מה אתה אמרת
            if (data.user) {
                transDiv.innerText = `"${data.user}"`;
                transDiv.style.opacity = 1;
            } else {
                transDiv.style.opacity = 0.5; // עמעום כשאין דיבור
            }

            // מציג מה Nog ענה
            if (data.chat) {
                respDiv.innerText = data.chat;
            }

            // 2. עדכון ה-Orb (הלב הוויזואלי)
            // ניקוי קלאסים קודמים כדי לאפשר מעבר חלק
            orb.classList.remove("listening", "thinking", "speaking");
            
            // זיהוי המצב והפעלת האנימציה המתאימה
            if (data.status.includes("מאזין")) {
                orb.classList.add("listening");
            } 
            else if (data.status.includes("חושב") || data.status.includes("חולם")) {
                orb.classList.add("thinking");
            } 
            else if (data.status.includes("מדבר")) {
                orb.classList.add("speaking");
            }

        }
    } catch (e) {
        // התעלמות משגיאות קריאה רגעיות (קורה כשמנסים לקרוא בדיוק כשנכתב)
        console.log("Waiting for sync...", e);
    }
}

// קצב רענון מהיר (כל 100 מילי-שניות) לתגובה חלקה
setInterval(updateUI, 100);