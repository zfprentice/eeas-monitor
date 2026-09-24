import re
import requests
from bs4 import BeautifulSoup

headers_ua = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("=== ec.europa.eu/newsroom/ structure ===")
r = requests.get("https://ec.europa.eu/newsroom/", headers=headers_ua, timeout=15)
print("status:", r.status_code, "len:", len(r.text))
soup = BeautifulSoup(r.text, "html.parser")
print("title:", soup.title.get_text(strip=True) if soup.title else None)

# look for API hints in scripts / data attributes
api_hints = set(re.findall(r'https?://[^\s"\'<>]*newsroom[^\s"\'<>]*', r.text, re.I))
print("newsroom-related URLs in page:", list(api_hints)[:20])

api_hints2 = set(re.findall(r'(/newsroom/api/[^\s"\'<>]*)', r.text))
print("relative /newsroom/api/ paths:", list(api_hints2)[:20])

# look for meta/og and nav links about "council" or "European Council"
for a in soup.find_all("a", href=True):
    txt = a.get_text(strip=True)
    if "council" in txt.lower() or "council" in a["href"].lower():
        print("council-related link:", a["href"][:100], "|", txt[:80])

print()
print("=== does newsroom cover multiple EU bodies? search body text ===")
body_lower = r.text.lower()
for term in ["european council", "council of the eu", "consilium", "costa", "von der leyen"]:
    print(term, "-> count:", body_lower.count(term))

print()
print("=== try known EU newsroom API pattern ===")
for url in [
    "https://ec.europa.eu/newsroom/api/documents",
    "https://ec.europa.eu/newsroom/api/services",
]:
    try:
        rr = requests.get(url, headers=headers_ua, timeout=15)
        print(url, "->", rr.status_code, rr.text[:300])
    except Exception as e:
        print(url, "error:", e)
