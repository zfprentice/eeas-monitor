import requests

headers_ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

candidates = [
    "https://www.europarl.europa.eu/doceo/document/A-10-2026-0003_EN.html",
    "https://www.europarl.europa.eu/doceo/document/A-10-2024-0001_EN.html",
    "https://www.europarl.europa.eu/doceo/document/A10-0003-2026_EN.html",
]

for url in candidates:
    try:
        r = requests.get(url, headers=headers_ua, timeout=15, allow_redirects=True)
        print(url, "->", r.status_code, "final_url:", r.url, "len:", len(r.text))
        if r.status_code == 200:
            # sanity check the page actually mentions the doc / looks real, not a generic error page
            print("  contains 'not found' (case-insens):", "not found" in r.text.lower())
            print("  title tag snippet:", r.text[r.text.lower().find("<title"): r.text.lower().find("<title") + 150])
    except Exception as e:
        print(url, "error:", e)
    print()

# Also test the raw distribution path from is_exemplified_by directly under the base host.
dist_candidates = [
    "https://data.europarl.europa.eu/distribution/reds_iPlRp/A-10-2024-0001/A-10-2024-0001_en.pdf",
    "https://www.europarl.europa.eu/distribution/reds_iPlRp/A-10-2024-0001/A-10-2024-0001_en.pdf",
]
for url in dist_candidates:
    try:
        r = requests.head(url, headers=headers_ua, timeout=15, allow_redirects=True)
        print(url, "-> HEAD status", r.status_code, "final:", r.url)
    except Exception as e:
        print(url, "error:", e)
