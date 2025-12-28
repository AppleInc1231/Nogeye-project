const { app, BrowserWindow, ipcMain } = require('electron');
const { exec } = require('child_process'); // רכיב להרצת פקודות מערכת

function createWindow() {
  const win = new BrowserWindow({
    width: 500,
    height: 700,
    frame: false,        
    transparent: true,   
    alwaysOnTop: true,   
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  win.loadFile('index.html');
}

// פונקציית ההשמדה - הורגת את הפייתון
function killPython() {
    console.log("Killing Python process...");
    // מריץ פקודת מערכת לחיסול המוח
    exec('pkill -f wake_chat.py');
}

// כשלוחצים על האיקס בממשק
ipcMain.on('close-app', () => {
    killPython(); // קודם הורג את המוח
    setTimeout(() => {
        app.quit();   // ואז סוגר את האפליקציה
    }, 500);
});

app.whenReady().then(createWindow);

// כשהחלון נסגר בכל דרך אחרת (Cmd+Q)
app.on('window-all-closed', () => {
    killPython();
    app.quit();
});

// לפני שהאפליקציה יוצאת סופית
app.on('will-quit', () => {
    killPython();
});