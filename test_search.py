from duckduckgo_search import DDGS

print("🚀 Testing Search Engine...")
try:
    with DDGS() as ddgs:
        results = list(ddgs.text("Bitcoin price", max_results=1))
        if results:
            print(f"✅ SUCCESS! Found: {results[0]['title']}")
            print(results[0]['body'])
        else:
            print("❌ FAILURE: Zero results found.")
except Exception as e:
    print(f"💥 CRASH: {e}")
