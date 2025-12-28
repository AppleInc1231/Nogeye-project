const fs = require('fs');
const path = require('path');
const { ipcRenderer } = require('electron');

// נתיבים
const LIVE_JSON_PATH = path.join(__dirname, 'live.json');

// אלמנטים
const orb = document.getElementById('orb');
const statusText = document.getElementById('status-text');
const userText = document.getElementById('user-text');
const aiText = document.getElementById('ai-text');

// 1. כפתור סגירה
const closeBtn = document.getElementById('close-btn');
if (closeBtn) {
    closeBtn.addEventListener('click', () => {
        ipcRenderer.send('close-app');
    });
}

// 2. לולאת עדכון ממשק
setInterval(() => {
    if (fs.existsSync(LIVE_JSON_PATH)) {
        try {
            const rawData = fs.readFileSync(LIVE_JSON_PATH);
            const data = JSON.parse(rawData);

            userText.innerText = data.user || "";
            aiText.innerText = data.chat || "";
            updateOrb(data.status);

        } catch (error) {
            // התעלמות משגיאות קריאה רגעיות
        }
    }
}, 100);

function updateOrb(status) {
    orb.className = 'orb';
    
    if (status === 'מוכנה' || status === 'מאזין') {
        orb.classList.add('listening');
        statusText.innerText = "מקשיב לך...";
    } else if (status === 'מדבר' || status === 'פעולה') {
        orb.classList.add('speaking');
        statusText.innerText = "Nog עובד...";
    } else if (status === 'חושב' || status === 'מעבד') {
        orb.classList.add('processing');
        statusText.innerText = "מעבד...";
    }
}