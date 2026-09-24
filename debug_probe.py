import requests

headers = {"Accept": "application/ld+json", "User-Agent": "EEAS-Monitor-Pipeline/1.0"}
base = "https://data.europarl.europa.eu/api/v2"

print("=== Direct re-check: /plenary-documents?year=2026&limit=100&offset=0 ===")
r = requests.get(f"{base}/plenary-documents", params={"year": 2026, "limit": 100, "offset": 0}, headers=headers, timeout=20)
print("status:", r.status_code)
print("headers:", dict(r.headers))
print("body[:1000]:", r.text[:1000])
print()

print("=== Same call again immediately (2nd try) ===")
r2 = requests.get(f"{base}/plenary-documents", params={"year": 2026, "limit": 100, "offset": 0}, headers=headers, timeout=20)
print("status:", r2.status_code)
print("data length:", len(r2.json().get("data", [])) if r2.status_code == 200 else "N/A")
