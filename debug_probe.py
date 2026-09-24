import requests

print("=== PressCorner: try POST with JSON body for pagination ===")
url = "https://ec.europa.eu/commission/presscorner/api/search"
headers = {"User-Agent": "EEAS-Monitor-Pipeline/1.0", "Accept": "application/json", "Content-Type": "application/json"}
for page in [0, 1]:
    body = {"text": "", "docType": "STATEMENT", "pagesize": 50, "pageNumber": page, "language": "en"}
    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
        print(f"POST page={page}: status={r.status_code}")
        if r.status_code == 200:
            data = r.json()
            docs = data.get("docuLanguageListResources", [])
            print("  first 3:", [d.get("refCode") for d in docs[:3]])
    except Exception as e:
        print("error:", e)

print()
print("=== EEAS: try Drupal AJAX views endpoint for real pagination ===")
# Drupal views often expose /views/ajax for AJAX-paged views
url2 = "https://www.eeas.europa.eu/views/ajax"
try:
    r2 = requests.get(url2, params={
        "view_name": "pressmaterial_filterpage",
        "view_display_id": "pm_search_page",
        "page": 1,
    }, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    print("views/ajax GET ->", r2.status_code, r2.text[:300])
except Exception as e:
    print("error:", e)

print()
print("=== EEAS: try &page=1 vs ?page=1 as only param (no leading page=0 in URL construction) ===")
for p in ["page=1", "page=2"]:
    url3 = f"https://www.eeas.europa.eu/eeas/mat%C3%A9riel-de-presse_fr?{p}"
    r3 = requests.get(url3, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    # crude check: does it contain a distinctive later-page title vs page 0's known first title?
    known_first_title = "L’UE et l’Algérie lancent un jumelage"
    print(p, "-> status", r3.status_code, "contains page0 first title:", known_first_title in r3.text)
