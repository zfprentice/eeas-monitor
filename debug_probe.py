import requests

headers_full = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

print("=== data.consilium.europa.eu (document register subdomain) ===")
for url in [
    "https://data.consilium.europa.eu/",
    "https://data.consilium.europa.eu/doc/document/CM-1570-2026-INIT/en/pdf",
]:
    try:
        r = requests.get(url, headers=headers_full, timeout=15)
        print(url, "->", r.status_code, "server:", r.headers.get("Server"))
    except Exception as e:
        print(url, "error:", e)

print()
print("=== europa.eu unified newsroom ===")
for url in [
    "https://european-union.europa.eu/news-and-events/news_en",
    "https://ec.europa.eu/newsroom/",
]:
    try:
        r = requests.get(url, headers=headers_full, timeout=15)
        print(url, "->", r.status_code, "len:", len(r.text), "server:", r.headers.get("Server"))
    except Exception as e:
        print(url, "error:", e)

print()
print("=== consilium.europa.eu: does removing cookies / trying HTTP/1.0-style plain fetch change anything ===")
s = requests.Session()
r1 = s.get("https://www.consilium.europa.eu/", headers=headers_full, timeout=15)
print("homepage ->", r1.status_code, "cf-mitigated:", r1.headers.get("Cf-Mitigated"))
