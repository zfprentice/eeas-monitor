"""EC Press Corner (statements, speeches, press releases from the European Commission)."""

import datetime
import re

import requests

from regions import detect_regions

SOURCE_NAME = "Commission PressCorner (HQ)"

_API_URL = "https://ec.europa.eu/commission/presscorner/api/search"
_HEADERS = {"User-Agent": "EEAS-Monitor-Pipeline/1.0", "Accept": "application/json"}

# The API's pageNumber parameter is ignored server-side (verified: pageNumber=0/1/2
# all return the identical latest batch, and POST with a JSON body is rejected with
# 405). So we only ever fetch a single page of the newest items; the hourly cron
# cadence combined with id-based dedup is what actually accumulates history over time.
_PAGE_SIZE = 50

# Matches "by <Role> <Name>" in a title, stopping at the next preposition, e.g.
# "Speech by President von der Leyen at the ..." -> "President von der Leyen".
_SPEAKER_RE = re.compile(
    r"\bby\s+((?:President|Vice-President|Executive Vice-President|High Representative"
    r"|Commissioner|Spokesperson)\s+.+?)(?:\s+(?:at|on|in|during|for|to|of)\b|$)",
    re.IGNORECASE,
)


def extract_speaker(title):
    """Best-effort extraction of a named speaker from a PressCorner title."""
    match = _SPEAKER_RE.search(title or "")
    if match:
        return match.group(1).strip()
    return "European Commission"


def parse_response(data):
    """Pure parsing of the PressCorner /api/search JSON response into normalized items."""
    items = []
    docs = data.get("docuLanguageListResources", []) if isinstance(data, dict) else []

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
                "speaker": extract_speaker(title),
                "source": SOURCE_NAME,
                "regions": detect_regions(corpus),
                "summary": (doc.get("leadText") or "").strip()[:240],
            }
        )
    return items


def fetch():
    params = {
        "text": "",
        "docType": "STATEMENT",
        "pagesize": _PAGE_SIZE,
        "pageNumber": 0,
        "language": "en",
    }
    try:
        r = requests.get(_API_URL, params=params, headers=_HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"[presscorner] HTTP {r.status_code}")
            return []
        return parse_response(r.json())
    except Exception as e:
        print(f"[presscorner] error: {e}")
        return []
