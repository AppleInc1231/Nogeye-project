const { app, BrowserWindow, ipcMain } = require('electron');
const { exec } = require('child_process'); // רכיב להרצת פקודות מערכת

function createWindow() {
  const win = new BrowserWindow({
    width: 600,            // הרחבתי קצת שיהיה מקום להילה
    height: 750,
    frame: false,          // ללא מסגרת (נקי)
    transparent: true,     // שקוף (כדי לראות רק את העיגול)
    alwaysOnTop: true,     // צף מעל הכל
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    }
  });

  win.loadFile('index.html');
}

// --- מנגנון ניקוי תהליכים (חשוב מאוד!) ---

// פונקציית ההשמדה - הורגת את הפייתון כדי שלא יישאר זומבי
function killPython() {
    console.log("Killing Python process...");
    // הורג את הסקריפט הספציפי שלנו
    exec('pkill -f wake_chat.py');
}

// אירוע סגירה יזום מהממשק (אם יהיה כפתור X)
ipcMain.on('close-app', () => {
    killPython(); 
    setTimeout(() => {
        app.quit();   
    }, 500);
});

app.whenReady().then(createWindow);

// סגירה כללית (Cmd+Q או סגירת חלון)
app.on('window-all-closed', () => {
    killPython(); // מוודא הריגה
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// רשת ביטחון אחרונה לפני יציאה
app.on('will-quit', () => {
    killPython();
});