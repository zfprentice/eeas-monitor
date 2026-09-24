import datetime
import hashlib
import json
import os
import re
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


def fetch_presscorner(pages=5):
    """Pulls recent and historical statements from the EC Press Corner API."""
    items = []
    base_url = "https://ec.europa.eu/commission/presscorner/api/documents"
    headers = {"User-Agent": "EEAS-Monitor-Pipeline/1.0"}

    for page in range(pages):
        params = {
            "docType": "STATEMENT,SPEECH",
            "pagesize": 50,
            "pageNumber": page,
            "language": "en",
        }
        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=15)
            if r.status_code != 200:
                break
            data = r.json()
            docs = data.get("documents", []) if isinstance(data, dict) else data
            if not docs:
                break

            for doc in docs:
                ref = doc.get("reference") or doc.get("id", "")
                title = doc.get("title", "").strip()
                author = (
                    doc.get("author")
                    or doc.get("speaker")
                    or "High Representative / VP"
                )
                corpus = f"{title} {doc.get('description', '')}"

                items.append(
                    {
                        "id": ref,
                        "title": title,
                        "link": f"https://ec.europa.eu/commission/presscorner/detail/en/{ref}",
                        "date": doc.get(
                            "publicationDate",
                            datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                        )[:10],
                        "type": doc.get("documentType", "STATEMENT"),
                        "speaker": author,
                        "source": "Commission PressCorner (HQ)",
                        "regions": detect_regions(corpus),
                        "summary": doc.get("description", "").strip()[:240],
                    }
                )
        except Exception as e:
            print(f"Error querying PressCorner page {page}: {e}")
            break
    return items


def fetch_eeas_portal(pages=3):
    """Paginates through statements on the EEAS French press portal."""
    items = []
    base_url = "https://www.eeas.europa.eu"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for page in range(pages):
        url = f"{base_url}/eeas/mat%C3%A9riel-de-presse_fr?f[0]=pm_type:Statement&page={page}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("article, .ecl-card, .views-row")
            if not cards:
                break

            for c in cards:
                a_tag = c.select_one("h2 a, h3 a, .ecl-card__title a")
                if not a_tag or not a_tag.get("href"):
                    continue

                title = a_tag.get_text(strip=True)
                link = urljoin(base_url, a_tag["href"])
                doc_id = hashlib.md5(link.encode("utf-8")).hexdigest()[:12]

                date_tag = c.select_one("time, .ecl-card__detail")
                date_str = (
                    date_tag.get_text(strip=True)
                    if date_tag
                    else datetime.datetime.utcnow().strftime("%Y-%m-%d")
                )

                corpus = f"{title} {c.get_text()}"
                items.append(
                    {
                        "id": doc_id,
                        "title": title,
                        "link": link,
                        "date": date_str[:15],
                        "type": "Statement / Communiqué",
                        "speaker": "EEAS / EU Delegation",
                        "source": "EEAS Direct Portal",
                        "regions": detect_regions(corpus),
                        "summary": title,
                    }
                )
        except Exception as e:
            print(f"Error querying EEAS Portal page {page}: {e}")
            break
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
    new_items = fetch_presscorner(pages=5) + fetch_eeas_portal(pages=3)

    for item in new_items:
        if item["id"] not in seen_ids and item["title"]:
            existing.append(item)
            seen_ids.add(item["id"])

    # Sort newest to oldest by date
    existing.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    existing = existing[:1000]  # Store up to 1,000 historical statements

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved {len(existing)} statements to {DATA_PATH}.")


if __name__ == "__main__":
    main()
