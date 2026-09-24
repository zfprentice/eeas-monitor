import json
import re
import requests
from bs4 import BeautifulSoup

headers_ua = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("=== PressCorner /api/search full item ===")
r = requests.get(
    "https://ec.europa.eu/commission/presscorner/api/search",
    params={"text": "", "docType": "STATEMENT", "pagesize": 3, "pageNumber": 0, "language": "en"},
    headers={"User-Agent": "EEAS-Monitor-Pipeline/1.0", "Accept": "application/json"},
    timeout=15,
)
print("status", r.status_code, r.url)
try:
    data = r.json()
    print("top-level keys:", list(data.keys()))
    docs = data.get("docuLanguageListResources", [])
    print("doc count:", len(docs))
    if docs:
        print(json.dumps(docs[0], indent=2, ensure_ascii=False))
except Exception as e:
    print("parse error:", e, r.text[:500])

print()
print("=== PressCorner: does docType=STATEMENT actually filter? try without filter ===")
r2 = requests.get(
    "https://ec.europa.eu/commission/presscorner/api/search",
    params={"pagesize": 3, "pageNumber": 0, "language": "en"},
    headers={"User-Agent": "EEAS-Monitor-Pipeline/1.0", "Accept": "application/json"},
    timeout=15,
)
print("status", r2.status_code)
try:
    d2 = r2.json()
    print("totalNumber:", d2.get("totalNumber"))
    print("types seen:", [x.get("docutype", {}).get("code") for x in d2.get("docuLanguageListResources", [])])
except Exception as e:
    print("err", e)

print()
print("=== EEAS: dump non-filter .card items ===")
url = "https://www.eeas.europa.eu/eeas/mat%C3%A9riel-de-presse_fr?page=0"
r = requests.get(url, headers=headers_ua, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")
cards = soup.select(".card")
print(f"total .card={len(cards)}")
for i, c in enumerate(cards[1:4], start=1):
    print(f"--- card {i} ---")
    print(str(c)[:1500])
    print()

print("=== EEAS: publication_type facet options (looking for Statement value) ===")
# Drupal facets are usually rendered as <a href="...f[0]=publication_type:VALUE">Label (count)</a>
for a in soup.find_all("a", href=True):
    if "publication_type" in a["href"]:
        print(a["href"][:120], "|", a.get_text(strip=True))
