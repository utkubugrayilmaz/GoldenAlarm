import requests

url = "https://finans.truncgil.com/v4/today.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
}

print("Test 1: Header ile...")
try:
    r = requests.get(url, headers=headers, timeout=15)
    print(f"✅ Status: {r.status_code}, Length: {len(r.text)}")
except Exception as e:
    print(f"❌ Hata: {e}")

print("\nTest 2: SSL verify=False ile...")
try:
    r = requests.get(url, headers=headers, timeout=15, verify=False)
    print(f"✅ Status: {r.status_code}, Length: {len(r.text)}")
except Exception as e:
    print(f"❌ Hata: {e}")