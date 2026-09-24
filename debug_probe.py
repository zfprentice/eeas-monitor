import requests
from bs4 import BeautifulSoup

headers_ua = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("=== PressCorner: compare pageNumber=0 vs pageNumber=1 ===")
base_url = "https://ec.europa.eu/commission/presscorner/api/search"
ids_by_page = {}
for page in [0, 1, 2]:
    params = {"text": "", "docType": "STATEMENT", "pagesize": 50, "pageNumber": page, "language": "en"}
    r = requests.get(base_url, params=params, headers={"User-Agent": "EEAS-Monitor-Pipeline/1.0", "Accept": "application/json"}, timeout=15)
    data = r.json()
    docs = data.get("docuLanguageListResources", [])
    ids = [d.get("refCode") for d in docs]
    ids_by_page[page] = ids
    print(f"page {page}: {len(ids)} items, first 3: {ids[:3]}, last 3: {ids[-3:] if len(ids)>=3 else ids}")

print("page0 == page1 ?", ids_by_page[0] == ids_by_page[1])
print("page1 == page2 ?", ids_by_page[1] == ids_by_page[2])
print("overlap page0/page1:", len(set(ids_by_page[0]) & set(ids_by_page[1])))

print()
print("=== PressCorner: try 'page' param name instead of 'pageNumber' ===")
for page in [0, 1]:
    params = {"text": "", "docType": "STATEMENT", "pagesize": 50, "page": page, "language": "en"}
    r = requests.get(base_url, params=params, headers={"User-Agent": "EEAS-Monitor-Pipeline/1.0", "Accept": "application/json"}, timeout=15)
    data = r.json()
    docs = data.get("docuLanguageListResources", [])
    ids = [d.get("refCode") for d in docs]
    print(f"'page' param, page={page}: first 3: {ids[:3]}")

print()
print("=== EEAS: compare page=0 vs page=1 card titles ===")
base_eeas = "https://www.eeas.europa.eu"
titles_by_page = {}
for page in [0, 1, 2]:
    url = f"{base_eeas}/eeas/mat%C3%A9riel-de-presse_fr?page={page}"
    r = requests.get(url, headers=headers_ua, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    cards = [c for c in soup.select(".card") if c.select_one(".card-title a")]
    titles = [c.select_one(".card-title a").get_text(strip=True)[:50] for c in cards]
    titles_by_page[page] = titles
    print(f"page {page}: {len(titles)} cards, first 2: {titles[:2]}")

print("eeas page0 == page1 ?", titles_by_page[0] == titles_by_page[1])
print("eeas overlap page0/page1:", len(set(titles_by_page[0]) & set(titles_by_page[1])))
