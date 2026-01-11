#!/usr/bin/env python3.11
"""
סקריפט בדיקת Azure Speech
בודק אם Azure מדבר עברית נכון
"""

import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

# טעינת הגדרות
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

azure_key = os.getenv("AZURE_SPEECH_KEY")
azure_region = os.getenv("AZURE_SPEECH_REGION")

print("🎤 בדיקת Azure Speech TTS לעברית")
print("=" * 60)
print(f"Region: {azure_region}")
print(f"Key: {azure_key[:10]}..." if azure_key else "Key: NOT FOUND")
print("=" * 60)

# קולות לבדיקה
VOICES = {
    "1": ("he-IL-AvriNeural", "אברי - גברי"),
    "2": ("he-IL-HilaNeural", "הילה - נשי"),
}

TEST_TEXT = "שלום מאור, אני נוג. אני כאן כדי לעזור לך בכל דבר שאתה צריך."

print("\nקולות זמינים:")
for num, (voice_id, desc) in VOICES.items():
    print(f"{num}. {desc} ({voice_id})")

choice = input("\nבחר קול (1/2): ").strip()

if choice not in VOICES:
    print("❌ בחירה לא תקינה")
    exit(1)

voice_id, voice_desc = VOICES[choice]
output_file = os.path.join(BASE_DIR, f"test_azure_{choice}.mp3")

print(f"\n🔊 מפיק דיבור: {voice_desc}...")

try:
    # הגדרת Azure
    speech_config = speechsdk.SpeechConfig(
        subscription=azure_key,
        region=azure_region
    )
    
    # הגדרת הקול
    speech_config.speech_synthesis_voice_name = voice_id
    
    # הגדרת פלט אודיו
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
    
    # יצירת synthesizer
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    print(f"טקסט: {TEST_TEXT}")
    print("מייצר אודיו...")
    
    # סינתוז הדיבור
    result = synthesizer.speak_text_async(TEST_TEXT).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"✅ הקובץ נוצר: {output_file}")
        print("🎧 מנגן עכשיו...")
        
        # נגן את הקובץ
        os.system(f"afplay {output_file}")
        
        print("\n" + "=" * 60)
        quality = input("האם הקול נשמע עברית טבעית? (y/n): ").strip().lower()
        
        if quality == 'y':
            print("\n✅ מעולה! הבעיה לא ב-Azure")
            print("הבעיה כנראה בקוד של wake_chat.py")
        else:
            print("\n❌ הבעיה היא ב-Azure")
            print("אולי צריך לנסות region אחר או לבדוק את החשבון")
            
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"\n❌ שגיאה: {cancellation.reason}")
        if cancellation.reason == speechsdk.CancellationReason.Error:
            print(f"פרטי שגיאה: {cancellation.error_details}")
            
except Exception as e:
    print(f"\n💥 שגיאה קריטית: {e}")
    import traceback
    traceback.print_exc()
