import os

from sources.eeas_portal import parse_eeas_date, parse_listing

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "eeas_listing.html")


def load_fixture():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_parse_listing_skips_filter_panel_card():
    items = parse_listing(load_fixture())
    # 4 cards in the fixture, but the first is the search/filter panel, not a result.
    assert len(items) == 3


def test_parse_listing_extracts_title_and_link():
    items = parse_listing(load_fixture())
    declaration = next(i for i in items if "Déclaration de l’Union" in i["title"])
    assert declaration["link"].startswith("https://www.eeas.europa.eu/delegations/vienna-international-organisations/")


def test_parse_listing_parses_date():
    items = parse_listing(load_fixture())
    assert all(i["date"] == "2026-09-23" for i in items if "Algérie" in i["title"] or "Déclaration" in i["title"])


def test_parse_listing_extracts_category_as_type():
    items = parse_listing(load_fixture())
    declaration = next(i for i in items if "Déclaration de l’Union" in i["title"])
    assert declaration["type"] == "Déclaration"


def test_parse_listing_detects_region_from_full_card_text():
    items = parse_listing(load_fixture())
    beach_clean = next(i for i in items if "Beach Clean" in i["title"])
    assert "Middle East & North Africa" in beach_clean["regions"]
    assert "Eastern Europe & Caucasus" in beach_clean["regions"]


def test_parse_listing_handles_no_results():
    assert parse_listing("<html><body><main></main></body></html>") == []


def test_parse_eeas_date_valid():
    assert parse_eeas_date("23.09.2026") == "2026-09-23"


def test_parse_eeas_date_invalid_falls_back_to_today():
    import datetime

    assert parse_eeas_date("not a date") == datetime.datetime.utcnow().strftime("%Y-%m-%d")
