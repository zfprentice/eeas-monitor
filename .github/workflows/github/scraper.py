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


def fetch_presscorner():
    items = []
    url = "https://ec.europa.eu/commission/presscorner/api/documents"
    params = {"docType": "STATEMENT,SPEECH", "pagesize": 40, "language": "en"}
    headers = {"User-Agent": "EEAS-Monitor-Pipeline/1.0"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=12)
        if r.status_code == 200:
            docs = r.json()
            if isinstance(docs, dict):
                docs = docs.get("documents", [])
            for doc in docs:
                ref = doc.get("reference") or doc.get("id", "")
                title = doc.get("title", "").strip()
                author = doc.get("author") or doc.get("speaker") or "High Representative / VP"

                corpus = f"{title} {doc.get('description', '')}"
                regions = detect_regions(corpus)

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
                        "regions": regions,
                        "summary": doc.get("description", "").strip()[:240],
                    }
                )
    except Exception as e:
        print(f"Error querying PressCorner: {e}")
    return items


def fetch_eeas_portal():
    items = []
    url = "https://www.eeas.europa.eu/eeas/mat%C3%A9riel-de-presse_fr?f[0]=pm_type:Statement"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("article, .ecl-card, .views-row")
            for c in cards:
                a_tag = c.select_one("h2 a, h3 a, .ecl-card__title a")
                if not a_tag or not a_tag.get("href"):
                    continue

                title = a_tag.get_text(strip=True)
                link = urljoin("https://www.eeas.europa.eu", a_tag["href"])
                doc_id = hashlib.md5(link.encode("utf-8")).hexdigest()[:12]

                date_tag = c.select_one("time, .ecl-card__detail")
                date_str = (
                    date_tag.get_text(strip=True)
                    if date_tag
                    else datetime.datetime.utcnow().strftime("%Y-%m-%d")
                )

                corpus = f"{title} {c.get_text()}"
                regions = detect_regions(corpus)

                items.append(
                    {
                        "id": doc_id,
                        "title": title,
                        "link": link,
                        "date": date_str[:15],
                        "type": "Statement / Communiqué",
                        "speaker": "EEAS / EU Delegation",
                        "source": "EEAS Direct Portal",
                        "regions": regions,
                        "summary": title,
                    }
                )
    except Exception as e:
        print(f"Error querying EEAS Portal: {e}")
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
    new_items = fetch_presscorner() + fetch_eeas_portal()

    for item in new_items:
        if item["id"] not in seen_ids and item["title"]:
            existing.append(item)
            seen_ids.add(item["id"])

    # Sort newest to oldest
    existing.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    existing = existing[:250]  # Keep latest 250 items

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(existing)} statements.")


if __name__ == "__main__":
    main()
