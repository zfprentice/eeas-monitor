import re
import requests
from bs4 import BeautifulSoup

headers_ua = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("=== PressCorner API variations ===")
variants = [
    {"docType": "STATEMENT", "pagesize": 5, "pageNumber": 0, "language": "en"},
    {"pagesize": 5, "pageNumber": 0, "language": "en"},
    {"pageSize": 5, "pageNumber": 0, "language": "en"},
    {"pagesize": 5, "page": 0, "language": "en"},
]
base_url = "https://ec.europa.eu/commission/presscorner/api/documents"
for i, params in enumerate(variants):
    try:
        r = requests.get(base_url, params=params, headers={"User-Agent": "EEAS-Monitor-Pipeline/1.0", "Accept": "application/json"}, timeout=15)
        print(f"variant {i} params={params} -> status={r.status_code} url={r.url}")
        print(f"  body[:300]={r.text[:300]!r}")
    except Exception as e:
        print(f"variant {i} error: {e}")

print()
print("=== EEAS portal HTML structure ===")
url = "https://www.eeas.europa.eu/eeas/mat%C3%A9riel-de-presse_fr?f[0]=pm_type:Statement&page=0"
r = requests.get(url, headers=headers_ua, timeout=15)
print(f"status={r.status_code} len={len(r.text)}")
soup = BeautifulSoup(r.text, "html.parser")

for pattern in ["views-row", "ecl-card", "ecl", "teaser", "node--type", "press", "listing"]:
    matches = soup.select(f'[class*="{pattern}"]')
    print(f"selector [class*={pattern}] count={len(matches)}")

# find <main> content and print classes of its direct children/descendants with hrefs
main = soup.find("main") or soup.find(id="main-content") or soup.find(attrs={"role": "main"})
print("main found:", bool(main))
if main:
    links = main.find_all("a", href=True)
    print(f"links in main: {len(links)}")
    for a in links[:15]:
        print("  ", a.get("class"), a["href"][:80], "|", a.get_text(strip=True)[:60])

# also dump all distinct class names containing 'card' or 'item' or 'result'
classes = set()
for tag in soup.find_all(class_=True):
    for c in tag.get("class", []):
        if any(k in c.lower() for k in ["card", "item", "result", "row", "teaser", "list"]):
            classes.add(c)
print("candidate classes:", sorted(classes)[:60])
