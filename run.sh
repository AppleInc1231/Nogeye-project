#!/bin/bash

# נתיבים (כדי שהמחשב יכיר את הפקודות)
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# הולך לתיקייה המדויקת
cd /Users/sror-nog/Desktop/NogEye

# --- שלב הניקוי המקדים ---
# מוודא שאין שום NogEye שרץ כרגע לפני שמתחילים חדש
# זה ימנע את המצב של "לופים" ורעשים כפולים
pkill -f wake_chat.py

# --- הפעלה ---
echo "🧠 Starting new Brain..."
python3.11 backend/wake_chat.py &

# מחכה רגע שהמוח ייטען
sleep 2

echo "👁️ Starting UI..."
cd frontend
# מפעיל את המסך ומחכה עד שתלחץ על האיקס
/opt/homebrew/bin/npx electron .

# --- שלב הניקוי הסופי ---
# ברגע שלחצת על האיקס בחלון, השורה הזו רצה:
echo "🛑 Shutting down..."
pkill -f wake_chat.py