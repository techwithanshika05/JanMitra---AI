import httpx

try:
    r = httpx.get("https://api.sarvam.ai", timeout=10)
    print("Status:", r.status_code)
    print(r.text[:200])
except Exception as e:
    print(type(e).__name__, e)