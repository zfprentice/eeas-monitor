"""EEAS press material portal (statements, declarations, communiqués)."""

import datetime
import hashlib
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from regions import detect_regions

SOURCE_NAME = "EEAS Direct Portal"

_BASE_URL = "https://www.eeas.europa.eu"
_LISTING_URL = f"{_BASE_URL}/eeas/mat%C3%A9riel-de-presse_fr"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# The listing's ?page=N parameter is ignored server-side (verified: page=0/1/2 all
# return the identical latest batch; the site's pager is Drupal-AJAX-driven and
# isn't reachable with a plain GET). So we only fetch the single newest listing page;
# the hourly cron cadence combined with id-based dedup accumulates history over time.


def parse_eeas_date(raw):
    """EEAS portal dates are rendered as DD.MM.YYYY."""
    raw = (raw or "").strip()
    try:
        return datetime.datetime.strptime(raw, "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def parse_listing(html):
    """Pure parsing of the EEAS listing page HTML into normalized items."""
    items = []
    soup = BeautifulSoup(html, "html.parser")
    cards = [c for c in soup.select(".card") if c.select_one(".card-title a")]

    for c in cards:
        a_tag = c.select_one(".card-title a")
        if not a_tag or not a_tag.get("href"):
            continue

        title = a_tag.get_text(strip=True)
        link = urljoin(_BASE_URL, a_tag["href"])
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
                "source": SOURCE_NAME,
                "regions": detect_regions(corpus),
                "summary": title,
            }
        )
    return items


def fetch():
    try:
        r = requests.get(_LISTING_URL, headers=_HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"[eeas] HTTP {r.status_code}")
            return []
        return parse_listing(r.text)
    except Exception as e:
        print(f"[eeas] error: {e}")
        return []
