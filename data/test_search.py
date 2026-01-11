from ddgs import DDGS
import json

print("🚀 מתחיל בדיקת חיפוש...")

try:
    with DDGS() as ddgs:
        # מנסים חיפוש פשוט
        results = list(ddgs.text("Bitcoin price USD", max_results=3))
        
        if results:
            print(f"✅ הצלחה! נמצאו {len(results)} תוצאות:")
            for r in results:
                print(f"- {r['title']}: {r['body'][:50]}...")
        else:
            print("❌ החיפוש עבד טכנית, אבל חזר ריק (0 תוצאות).")

except Exception as e:
    print(f"💥 שגיאה קריטית: {e}")