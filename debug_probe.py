import requests
from bs4 import BeautifulSoup

headers_ua = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("=== consilium.europa.eu RSS feeds page ===")
r = requests.get("https://www.consilium.europa.eu/en/about-site/rss/", headers=headers_ua, timeout=15)
print("status", r.status_code)
soup = BeautifulSoup(r.text, "html.parser")
for a in soup.find_all("a", href=True):
    href = a["href"]
    if "rss" in href.lower() or ".xml" in href.lower():
        print(href, "|", a.get_text(strip=True))

print()
print("=== try likely press-releases RSS URL directly ===")
for url in [
    "https://www.consilium.europa.eu/en/rss/latest-press-releases/",
    "https://www.consilium.europa.eu/en/press/press-releases/?rss=true",
    "https://www.consilium.europa.eu/rss/en/press-releases.xml",
]:
    try:
        rr = requests.get(url, headers=headers_ua, timeout=15)
        print(url, "->", rr.status_code, rr.headers.get("Content-Type"), len(rr.text))
        if rr.status_code == 200:
            print(rr.text[:800])
    except Exception as e:
        print(url, "error:", e)

print()
print("=== EC PressCorner RSS ===")
r2 = requests.get("https://ec.europa.eu/commission/presscorner/api/rss", headers=headers_ua, timeout=15)
print("status", r2.status_code, r2.headers.get("Content-Type"))
print(r2.text[:800])
