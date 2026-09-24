import json
import requests

headers = {"Accept": "application/ld+json", "User-Agent": "EEAS-Monitor-Research/1.0"}
base = "https://data.europarl.europa.eu/api/v2"


def get(url, params=None):
    r = requests.get(url, params=params, headers=headers, timeout=20)
    if r.status_code != 200:
        return None, r.status_code
    return r.json(), r.status_code


# 1. Confirm offset pagination actually advances results.
print("=== Pagination check: offset=0 vs offset=5 for year=2026 ===")
d0, _ = get(f"{base}/plenary-documents", {"year": 2026, "limit": 5, "offset": 0})
d1, _ = get(f"{base}/plenary-documents", {"year": 2026, "limit": 5, "offset": 5})
ids0 = [x["identifier"] for x in d0["data"]] if d0 else []
ids1 = [x["identifier"] for x in d1["data"]] if d1 else []
print("offset=0:", ids0)
print("offset=5:", ids1)
print("overlap:", set(ids0) & set(ids1))
print()

# 2. Check adopts-prefix + language-expression consistency across several docs.
print("=== adopts-prefix + language coverage across 10 docs ===")
for ident in ids0 + ids1:
    data, status = get(f"{base}/plenary-documents/{ident}")
    if not data or not data.get("data"):
        print(ident, "-> no data, status", status)
        continue
    doc = data["data"][0]
    adopts = doc.get("adopts", [])
    langs = [e.get("id", "").rsplit("/", 1)[-1] for e in doc.get("is_realized_by", [])]
    en_expr = next((e for e in doc.get("is_realized_by", []) if e.get("id", "").endswith("/en")), None)
    title_alt = en_expr.get("title_alternative", {}).get("en", "") if en_expr else "(no English expression)"
    print(f"{ident}: adopts={adopts} langs={langs}")
    print(f"  title_alt(en): {title_alt[:200]}")
print()

# 3. Try fetching the EuroVoc concept label for a sample is_about URI, to see if it's resolvable.
print("=== EuroVoc concept resolution attempt ===")
try:
    r = requests.get("http://eurovoc.europa.eu/6852", headers={"Accept": "application/json"}, timeout=15)
    print("status:", r.status_code, "content-type:", r.headers.get("Content-Type"))
    print(r.text[:500])
except Exception as e:
    print("error:", e)
