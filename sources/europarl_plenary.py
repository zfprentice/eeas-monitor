"""European Parliament plenary documents (reports, recommendations), scoped to
the committees of interest: AFET (Foreign Affairs) and DEVE (Development).

The API (https://data.europarl.europa.eu/api/v2/) has no committee-level filter
on /plenary-documents -- a guessed `committee=` param is silently ignored
(verified live: identical results with and without it). The authoring
committee isn't a field on the document itself either; it's encoded as a
prefix on the underlying draft-report id referenced via `adopts`, e.g.
"eli/dl/doc/AFET-PR-770055" -> committee AFET. That's the only reliable signal
found, so filtering happens after a per-document detail fetch.

Documents are numbered ascending within a year (A-10-<year>-0001, 0002, ...),
and the API gives no total-count field, so there's no cheap way to jump straight
to "the newest N". To avoid running an expensive detail-fetch against every
document just to find the handful that are AFET/DEVE, this module first pages
through the *list* endpoint (cheap, no committee info) to collect every
identifier for the target year(s), takes the numerically-highest
_MAX_DETAIL_FETCHES of them, and only runs the detail fetch (which is what
reveals committee + title + date) against that bounded recent window.
"""

import datetime
import re
import time

import requests

from regions import detect_regions

SOURCE_NAME = "European Parliament (AFET/DEVE)"

_API_BASE = "https://data.europarl.europa.eu/api/v2"
_HEADERS = {"Accept": "application/ld+json", "User-Agent": "EEAS-Monitor-Pipeline/1.0"}

COMMITTEES_OF_INTEREST = {"AFET", "DEVE"}

# Cap on how many of the most-recent documents (across all committees) get a
# detail fetch each run. Bounds request volume regardless of how many plenary
# documents exist for the year; wide enough that AFET/DEVE items reliably fall
# within the window given normal EP output volume.
# Live testing showed /plenary-documents?year=...&limit=100 repeatedly timing
# out at 30s even with a retry (confirmed twice), while smaller pages and the
# single-document detail endpoint responded quickly -- this API's response
# time appears to scale badly with page size. Trading more, lighter requests
# for fewer heavy ones.
_MAX_DETAIL_FETCHES = 60
_LIST_PAGE_SIZE = 25

_DOC_TYPE_LABELS = {
    "REPORT_PLENARY": "Report",
    "RECOMMENDATION": "Recommendation",
    "MOTION_RESOLUTION": "Motion for Resolution",
}

_RAPPORTEUR_RE = re.compile(r"Rapporteur:\s*(.+)$")


def _get_with_retry(url, params=None, timeout=20, retries=1):
    """The API is occasionally slow enough to exceed a 20s timeout, confirmed
    live (a request that timed out succeeded immediately on a plain retry
    seconds later), so a single retry meaningfully improves reliability."""
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return requests.get(url, params=params, headers=_HEADERS, timeout=timeout)
        except requests.exceptions.RequestException as e:
            last_exc = e
            if attempt < retries:
                time.sleep(1)
    raise last_exc


def _committee_from_adopts(adopts):
    for ref in adopts or []:
        tail = ref.rsplit("/", 1)[-1]  # e.g. "AFET-PR-770055"
        code = tail.split("-", 1)[0]
        if code in COMMITTEES_OF_INTEREST:
            return code
    return None


def _doc_number(identifier):
    """A-10-2026-0003 -> 3, for sorting newest-first within a year."""
    try:
        return int(identifier.rsplit("-", 1)[-1])
    except (ValueError, AttributeError):
        return -1


def parse_detail(doc):
    """Pure parsing of one /plenary-documents/{id} detail record (the first
    element of its 'data' array) into a normalized item, or None if it isn't
    authored by a committee of interest or lacks the fields we need."""
    committee = _committee_from_adopts(doc.get("adopts"))
    if not committee:
        return None

    identifier = doc.get("identifier") or doc.get("id", "").rsplit("/", 1)[-1]
    if not identifier:
        return None

    en_expr = next(
        (e for e in doc.get("is_realized_by", []) if e.get("id", "").endswith("/en")),
        None,
    )
    if not en_expr:
        return None

    title = (en_expr.get("title") or {}).get("en", "").strip()
    title_alt = (en_expr.get("title_alternative") or {}).get("en", "").strip()
    if not title:
        title = title_alt.split(" - ")[0].strip()
    if not title:
        return None

    rapporteur_match = _RAPPORTEUR_RE.search(title_alt)
    speaker = rapporteur_match.group(1).strip() if rapporteur_match else f"European Parliament ({committee})"

    work_type = (doc.get("work_type") or "").rsplit("/", 1)[-1]
    doc_type = _DOC_TYPE_LABELS.get(work_type, work_type.replace("_", " ").title() or "Plenary Document")

    corpus = f"{title} {title_alt}"

    return {
        "id": identifier,
        "title": title,
        # Best-informed guess at EP's public document-viewer URL convention.
        # Couldn't fully auto-verify: the site returns 202 with an empty body
        # to non-browser requests (likely bot mitigation), for both plausible
        # and implausible paths alike, so a live fetch can't distinguish a
        # correct URL from a wrong one. Spot-check a few links after this
        # source has run for real.
        "link": f"https://www.europarl.europa.eu/doceo/document/{identifier}_EN.html",
        "date": (doc.get("document_date") or datetime.datetime.utcnow().strftime("%Y-%m-%d"))[:10],
        "type": doc_type,
        "speaker": speaker,
        "source": SOURCE_NAME,
        "regions": detect_regions(corpus),
        "summary": title_alt[:240],
    }


def _list_identifiers_for_year(year):
    identifiers = []
    offset = 0
    while True:
        try:
            r = _get_with_retry(
                f"{_API_BASE}/plenary-documents",
                params={"year": year, "limit": _LIST_PAGE_SIZE, "offset": offset},
                timeout=20,
                retries=2,
            )
            if r.status_code != 200:
                print(f"[europarl-plenary] list year={year} offset={offset}: HTTP {r.status_code}")
                break
            stubs = r.json().get("data", [])
        except Exception as e:
            print(f"[europarl-plenary] error listing year={year} offset={offset}: {e}")
            break

        if not stubs:
            break
        identifiers.extend(s["identifier"] for s in stubs if s.get("identifier"))
        if len(stubs) < _LIST_PAGE_SIZE:
            break
        offset += _LIST_PAGE_SIZE

    return identifiers


def fetch(years=None):
    """years defaults to the current year; pass a list for manual backfill."""
    if years is None:
        years = [datetime.datetime.utcnow().year]

    all_identifiers = []
    for year in years:
        all_identifiers.extend(_list_identifiers_for_year(year))
    print(f"[europarl-plenary] listed {len(all_identifiers)} document(s) across year(s) {years}")

    all_identifiers.sort(key=_doc_number, reverse=True)
    candidates = all_identifiers[:_MAX_DETAIL_FETCHES]

    items = []
    detail_failures = 0
    for identifier in candidates:
        try:
            r = _get_with_retry(f"{_API_BASE}/plenary-documents/{identifier}", timeout=20)
            if r.status_code != 200:
                detail_failures += 1
                continue
            detail = r.json().get("data", [])
            if not detail:
                detail_failures += 1
                continue
            item = parse_detail(detail[0])
            if item:
                items.append(item)
        except Exception as e:
            detail_failures += 1
            print(f"[europarl-plenary] error fetching detail {identifier}: {e}")
        time.sleep(0.3)

    if detail_failures:
        print(f"[europarl-plenary] {detail_failures}/{len(candidates)} detail fetch(es) failed or were empty")

    return items
