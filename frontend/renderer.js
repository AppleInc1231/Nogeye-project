const fs = require('fs');
const path = require('path');

const userTextEl = document.getElementById("user-text");
const chatTextEl = document.getElementById("chat-text");
const statusEl = document.getElementById("status");
const tempEl = document.getElementById("temperature");
const waveEls = document.querySelectorAll(".wave");

function updateFromJSON() {
  const filePath = path.join(__dirname, '..', 'frontend', 'live.json');

  fs.readFile(filePath, "utf8", (err, data) => {
    if (err) return;

    try {
      const parsed = JSON.parse(data);
      statusEl.textContent = parsed.status || "מוכן";
      userTextEl.textContent = parsed.user || "";
      chatTextEl.textContent = parsed.chat || "";

      if (parsed.status === "מאזין") {
        waveEls.forEach(wave => wave.style.opacity = "1");
      } else {
        waveEls.forEach(wave => wave.style.opacity = "0.2");
      }
    } catch (e) {}
  });
}

async function loadWeather() {
  try {
    const res = await fetch("https://api.open-meteo.com/v1/forecast?latitude=32.7767&longitude=-96.7970&current_weather=true");
    const data = await res.json();
    tempEl.textContent = data.current_weather.temperature;
  } catch {
    tempEl.textContent = "שגיאה";
  }
}

loadWeather();
setInterval(updateFromJSON, 500);