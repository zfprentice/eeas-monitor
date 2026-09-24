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
                print(json.dumps(data, indent=2, ensure_ascii=False)[:3500])
            except Exception:
                print(r.text[:1000])
        else:
            print(r.text[:500])
    except Exception as e:
        print("error:", e)
    print()


# 1. Find AFET / DEVE committee org ids by paging corporate-bodies and filtering client-side.
print("=== Searching corporate-bodies for AFET / DEVE ===")
found = {}
offset = 0
while offset < 400 and len(found) < 2:
    r = requests.get(f"{base}/corporate-bodies", params={"limit": 100, "offset": offset}, headers=headers, timeout=20)
    if r.status_code != 200:
        print("status", r.status_code, r.text[:300])
        break
    items = r.json().get("data", [])
    if not items:
        break
    for it in items:
        label = (it.get("label") or "")
        if label in ("AFET", "DEVE") and label not in found:
            found[label] = it
    offset += 100
print("found:", json.dumps(found, indent=2, ensure_ascii=False))
print()

# 2. Try single-document detail fetch patterns.
show("Detail via identifier only", f"{base}/plenary-documents/A-10-2024-0001")
show("Detail via full eli path", f"{base}/plenary-documents/eli/dl/doc/A-10-2024-0001")

# 3. Try a 'year' filter to see if it changes/limits results (recency control).
show("Plenary docs filtered by year=2026", f"{base}/plenary-documents", {"year": 2026, "limit": 5})

# 4. Try guessed committee filter params.
show("Plenary docs with committee=AFET guess", f"{base}/plenary-documents", {"committee": "AFET", "limit": 5})

# 5. Try parliamentary-questions detail + date range.
show("Question detail via identifier", f"{base}/parliamentary-questions/E-10-2024-001357")
show("Questions filtered by date range", f"{base}/parliamentary-questions", {"date-from": "2026-09-01", "date-to": "2026-09-24", "limit": 5})
