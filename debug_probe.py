import json
import requests

headers = {"Accept": "application/ld+json", "User-Agent": "EEAS-Monitor-Research/1.0"}
base = "https://data.europarl.europa.eu/api/v2"

def show(label, url, params=None):
    print(f"=== {label} ===")
    print("url:", url, "params:", params)
    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        print("status:", r.status_code, "content-type:", r.headers.get("Content-Type"))
        if r.status_code == 200:
            try:
                data = r.json()
                print(json.dumps(data, indent=2, ensure_ascii=False)[:2500])
            except Exception:
                print(r.text[:1000])
        else:
            print(r.text[:500])
    except Exception as e:
        print("error:", e)
    print()

show("MEPs - current list (small page)", f"{base}/meps", {"parliamentary-term": 10, "offset": 0, "limit": 3})
show("Parliamentary questions - recent", f"{base}/parliamentary-questions", {"limit": 3})
show("Plenary documents - recent", f"{base}/plenary-documents", {"limit": 3})
show("Corporate bodies", f"{base}/corporate-bodies", {"limit": 3})
