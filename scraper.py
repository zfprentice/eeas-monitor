import datetime
import hashlib
import json
import os
import re
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

DATA_PATH = "data/statements.json"

REGION_KEYWORDS = {
    "Eastern Europe & Caucasus": [
        "ukraine",
        "russia",
        "belarus",
        "moldova",
        "georgia",
        "armenia",
        "azerbaijan",
        "caucasus",
    ],
    "Middle East & North Africa": [
        "israel",
        "gaza",
        "palestine",
        "lebanon",
        "syria",
        "iran",
        "yemen",
        "iraq",
        "libya",
        "egypt",
    ],
    "Western Balkans": [
        "kosovo",
        "serbia",
        "bosnia",
        "herzegovina",
        "montenegro",
        "albania",
        "north macedonia",
    ],
    "Indo-Pacific & Asia": [
        "china",
        "taiwan",
        "myanmar",
        "india",
        "pakistan",
        "afghanistan",
        "indo-pacific",
    ],
    "Sub-Saharan Africa": ["sudan", "sahel", "mali", "niger", "drc", "somalia", "ethiopia"],
    "Americas": ["venezuela", "cuba", "haiti", "latin america"],
}


def detect_regions(text):
    text_lower = text.lower()
    matched = []
    for region, keywords in REGION_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(k)}\b", text_lower) for k in keywords):
            matched.append(region)
    return matched if matched else ["Global / Multilateral"]


def parse_eeas_date(raw):
    """EEAS portal dates are rendered as DD.MM.YYYY."""
    raw = raw.strip()
    try:
        return datetime.datetime.strptime(raw, "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def fetch_presscorner(pages=5):
    """Pulls recent and historical statements from the EC Press Corner API."""
    items = []
    base_url = "https://ec.europa.eu/commission/presscorner/api/search"
    headers = {"User-Agent": "EEAS-Monitor-Pipeline/1.0", "Accept": "application/json"}

    for page in range(pages):
        params = {
            "text": "",
            "docType": "STATEMENT",
            "pagesize": 50,
            "pageNumber": page,
            "language": "en",
        }
        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"[presscorner] page {page}: HTTP {r.status_code}, stopping")
                break
            data = r.json()
            docs = data.get("docuLanguageListResources", [])
            if not docs:
                break

            for doc in docs:
                ref_code = doc.get("refCode", "")
                title = (doc.get("title") or "").strip()
                if not title:
                    continue
                doc_type = (doc.get("docutype") or {}).get("description", "Statement")
                corpus = f"{title} {doc.get('leadText') or ''}"
                slug = ref_code.lower().replace("/", "_") if ref_code else ""

                items.append(
                    {
                        "id": ref_code or f"presscorner-{doc.get('ky')}",
                        "title": title,
                        "link": f"https://ec.europa.eu/commission/presscorner/detail/en/{slug}"
                        if slug
                        else "https://ec.europa.eu/commission/presscorner/home/en",
                        "date": (doc.get("eventDate") or datetime.datetime.utcnow().strftime("%Y-%m-%d"))[:10],
                        "type": doc_type,
                        "speaker": "European Commission",
                        "source": "Commission PressCorner (HQ)",
                        "regions": detect_regions(corpus),
                        "summary": (doc.get("leadText") or "").strip()[:240],
                    }
                )
        except Exception as e:
            print(f"Error querying PressCorner page {page}: {e}")
            break
    print(f"[presscorner] collected {len(items)} items")
    return items


def fetch_eeas_portal(pages=3):
    """Paginates through statements on the EEAS French press portal."""
    items = []
    base_url = "https://www.eeas.europa.eu"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for page in range(pages):
        url = f"{base_url}/eeas/mat%C3%A9riel-de-presse_fr?page={page}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"[eeas] page {page}: HTTP {r.status_code}, stopping")
                break
            soup = BeautifulSoup(r.text, "html.parser")
            cards = [c for c in soup.select(".card") if c.select_one(".card-title a")]
            if not cards:
                break

            for c in cards:
                a_tag = c.select_one(".card-title a")
                if not a_tag or not a_tag.get("href"):
                    continue

                title = a_tag.get_text(strip=True)
                link = urljoin(base_url, a_tag["href"])
                doc_id = hashlib.md5(link.encode("utf-8")).hexdigest()[:12]

                category_tag = c.select_one(".card-subtitle")
                category = category_tag.get_text(strip=True) if category_tag else "Press Material"

                footer_tag = c.select_one(".card-footer")
                date_str = parse_eeas_date(footer_tag.get_text(strip=True)) if footer_tag else datetime.datetime.utcnow().strftime("%Y-%m-%d")

                corpus = f"{title} {c.get_text()}"
                items.append(
                    {
                        "id": doc_id,
                        "title": title,
                        "link": link,
                        "date": date_str,
                        "type": category,
                        "speaker": "EEAS / EU Delegation",
                        "source": "EEAS Direct Portal",
                        "regions": detect_regions(corpus),
                        "summary": title,
                    }
                )
        except Exception as e:
            print(f"Error querying EEAS Portal page {page}: {e}")
            break
    print(f"[eeas] collected {len(items)} items")
    return items


def main():
    os.makedirs("data", exist_ok=True)
    existing = []
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    seen_ids = {x["id"] for x in existing if "id" in x}
    presscorner_items = fetch_presscorner(pages=5)
    eeas_items = fetch_eeas_portal(pages=3)
    new_items = presscorner_items + eeas_items

    if not new_items and not existing:
        print("ERROR: both sources returned zero items and there is no existing data. "
              "This likely means a source has changed its API/markup. Failing the run "
              "instead of writing an empty dataset.")
        sys.exit(1)

    if not presscorner_items:
        print("WARNING: PressCorner returned 0 items this run (source may be broken).")
    if not eeas_items:
        print("WARNING: EEAS portal returned 0 items this run (source may be broken).")

    added = 0
    for item in new_items:
        if item["id"] not in seen_ids and item["title"]:
            existing.append(item)
            seen_ids.add(item["id"])
            added += 1

    # Sort newest to oldest by date
    existing.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    existing = existing[:1000]  # Store up to 1,000 historical statements

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved {len(existing)} statements to {DATA_PATH} ({added} new).")


if __name__ == "__main__":
    main()
