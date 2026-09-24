import requests

print("=== consilium.europa.eu 403 body inspection ===")
headers_full = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}
r = requests.get("https://www.consilium.europa.eu/en/press/press-releases/", headers=headers_full, timeout=15)
print("status:", r.status_code)
print("headers:", dict(r.headers))
print("body[:1500]:", r.text[:1500])

print()
print("=== try without any custom headers (plain requests default) ===")
r2 = requests.get("https://www.consilium.europa.eu/en/press/press-releases/", timeout=15)
print("status:", r2.status_code, "len:", len(r2.text))

print()
print("=== try European Council specific subsite ===")
r3 = requests.get("https://www.consilium.europa.eu/en/press/", headers=headers_full, timeout=15)
print("status:", r3.status_code)
