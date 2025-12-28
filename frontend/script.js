const fs = require('fs');
const path = require('path');

// נתיב לקובץ ה-JSON שהפייתון מעדכן
const DATA_PATH = path.join(__dirname, 'live.json');

const orb = document.getElementById('orb');
const statusText = document.getElementById('status-text');
const userText = document.getElementById('user-text');
const aiText = document.getElementById('ai-text');

// פונקציה שרצה כל 100 מילישניות ובודקת עדכונים
setInterval(() => {
    if (fs.existsSync(DATA_PATH)) {
        try {
            // קריאת הקובץ
            const rawData = fs.readFileSync(DATA_PATH);
            const data = JSON.parse(rawData);

            // עדכון הטקסטים
            userText.innerText = data.user || "";
            aiText.innerText = data.chat || "";

            // עדכון האנימציה של העיגול
            updateOrb(data.status);

        } catch (error) {
            console.error("Error reading JSON", error);
        }
    }
}, 100);

function updateOrb(status) {
    // מנקה את כל המחלקות הקודמות
    orb.className = 'orb';
    
    if (status === 'מוכנה' || status === 'מאזין') {
        orb.classList.add('listening');
        statusText.innerText = "מקשיב לך...";
    } else if (status === 'מדבר') {
        orb.classList.add('speaking');
        statusText.innerText = "NogEye מדבר...";
    } else {
        orb.classList.add('processing');
        statusText.innerText = "מעבד...";
    }
}