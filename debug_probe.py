import re
import requests
from bs4 import BeautifulSoup

headers_ua = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("=== PressCorner: try commission.europa.eu domain ===")
for base in [
    "https://commission.europa.eu/presscorner/api/documents",
    "https://ec.europa.eu/commission/presscorner/api/search",
]:
    try:
        r = requests.get(base, params={"pagesize": 5, "pageNumber": 0, "language": "en"}, headers={"User-Agent": "EEAS-Monitor-Pipeline/1.0", "Accept": "application/json"}, timeout=15)
        print(f"{base} -> status={r.status_code}")
        print(f"  body[:400]={r.text[:400]!r}")
    except Exception as e:
        print(f"{base} error: {e}")

print()
print("=== EEAS: inspect .card elements ===")
url = "https://www.eeas.europa.eu/eeas/mat%C3%A9riel-de-presse_fr?page=0"
r = requests.get(url, headers=headers_ua, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")
cards = soup.select(".card")
print(f".card count={len(cards)}")
if cards:
    c = cards[0]
    print("first card html[:2000]:")
    print(str(c)[:2000])

print()
print("=== EEAS: facet filters available (looking for doc-type facet) ===")
for m in re.finditer(r'f%5B0%5D=([a-zA-Z_]+)%3A', r.text):
    pass
facet_keys = set(re.findall(r'f\[0\]=([a-zA-Z_]+)%3A|f%5B0%5D=([a-zA-Z_]+)%3A', r.text))
print("facet key patterns found:", facet_keys)
# search for any select/input with name mentioning type
for tag in soup.find_all(["select", "input"]):
    name = tag.get("name", "")
    if "type" in name.lower() or "pm_" in name.lower():
        print("form field:", tag.name, tag.attrs)
