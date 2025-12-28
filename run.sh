#!/bin/bash

# 1. סגירת מופעים קודמים (כדי למנוע כפילויות)
echo "🧹 מנקה תהליכים ישנים..."
pkill -f wake_chat.py

# 2. הפעלת המוח (Backend) ברקע
echo "🧠 מפעיל את NogEye Backend..."
# אנחנו משתמשים ב-& כדי שזה ירוץ ברקע ולא יתקע את הסקריפט
python3.11 backend/wake_chat.py &

# שומרים את המזהה של התהליך כדי שנוכל לסגור אותו בסוף
BACKEND_PID=$!

# מחכים 2 שניות שהמוח ייטען
sleep 2

# 3. הפעלת הפנים (Frontend)
echo "👁️ מפעיל את הממשק..."
cd frontend
npx electron .

# 4. כשהחלון נסגר - סוגרים גם את המוח
echo "🛑 סוגר את המערכת..."
kill $BACKEND_PID
