#!/usr/bin/env python3.11
"""
סקריפט בדיקת קולות ElevenLabs
מאפשר לבדוק קולות שונים בעברית
"""

import os
from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

# טעינת API key
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# הקולות לבדיקה
VOICES = {
    "1": {
        "name": "Matilda (Multilingual - נשי)",
        "id": "XrExE9yKIg1WjnnlVkGX",
        "description": "קול נשי טבעי מאוד, מומלץ ביותר"
    },
    "2": {
        "name": "Daniel (גברי עברי)",
        "id": "onwK4e9ZLuTAKqWW03F9",
        "description": "קול גברי ישראלי אותנטי"
    },
    "3": {
        "name": "Nicole (Multilingual - נשי)",
        "id": "piTKgcLEGmPE4e6mEKli",
        "description": "קול נשי חם ומעורב"
    },
    "4": {
        "name": "Callum (Multilingual - גברי)",
        "id": "N2lVS1w4EtoT3dr4eOWO",
        "description": "קול גברי צעיר ואנרגטי"
    }
}

TEST_TEXT = "שלום מאור, אני נוג. אני כאן כדי לעזור לך בכל דבר שאתה צריך. איך אתה מרגיש היום?"

print("🎤 בדיקת קולות ElevenLabs לעברית\n")
print("=" * 60)

for num, voice in VOICES.items():
    print(f"\n{num}. {voice['name']}")
    print(f"   {voice['description']}")

print("\n" + "=" * 60)
choice = input("\nבחר מספר קול לבדיקה (1-4): ").strip()

if choice not in VOICES:
    print("❌ בחירה לא תקינה")
    exit(1)

selected_voice = VOICES[choice]
print(f"\n🔊 מפיק קול: {selected_voice['name']}...")

try:
    audio_generator = client.text_to_speech.convert(
        voice_id=selected_voice["id"],
        optimize_streaming_latency="0",
        output_format="mp3_44100_128",
        text=TEST_TEXT,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
        )
    )
    
    output_file = os.path.join(BASE_DIR, f"test_voice_{choice}.mp3")
    
    with open(output_file, "wb") as f:
        for chunk in audio_generator:
            if chunk:
                f.write(chunk)
    
    print(f"✅ הקובץ נשמר: {output_file}")
    print("🎧 מנגן עכשיו...")
    
    # נגן את הקובץ
    os.system(f"afplay {output_file}")
    
    print("\n" + "=" * 60)
    satisfied = input("\nהקול הזה טוב? (y/n): ").strip().lower()
    
    if satisfied == 'y':
        print(f"\n✅ מעולה! Voice ID לשימוש:")
        print(f"   {selected_voice['id']}")
        print("\nהעתק את ה-ID הזה ותשתמש בו ב-wake_chat.py")
    else:
        print("\n🔄 הרץ את הסקריפט שוב לבדיקת קול אחר")
        
except Exception as e:
    print(f"❌ שגיאה: {e}")
