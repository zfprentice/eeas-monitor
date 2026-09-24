import json
import os

from sources.europarl_plenary import _committee_from_adopts, _doc_number, parse_detail

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load(name):
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as f:
        return json.load(f)["data"][0]


def test_parse_detail_extracts_afet_document():
    item = parse_detail(load("europarl_plenary_afet.json"))
    assert item is not None
    assert item["id"] == "A-10-2026-0003"
    assert item["title"] == "Interim report on the EU-Principality association agreement"
    assert item["link"] == "https://www.europarl.europa.eu/doceo/document/A-10-2026-0003_EN.html"
    assert item["date"] == "2026-09-10"
    assert item["type"] == "Report"
    assert item["source"] == "European Parliament (AFET/DEVE)"


def test_parse_detail_extracts_deve_document():
    item = parse_detail(load("europarl_plenary_deve.json"))
    assert item is not None
    assert item["id"] == "A-10-2026-0042"
    assert item["type"] == "Recommendation"


def test_parse_detail_extracts_rapporteur_as_speaker():
    item = parse_detail(load("europarl_plenary_afet.json"))
    assert item["speaker"] == "Anna Fotyga"


def test_parse_detail_falls_back_to_committee_label_without_rapporteur():
    doc = load("europarl_plenary_afet.json")
    doc["is_realized_by"][0]["title_alternative"]["en"] = "INTERIM REPORT - no rapporteur line here"
    item = parse_detail(doc)
    assert item["speaker"] == "European Parliament (AFET)"


def test_parse_detail_rejects_non_committee_of_interest():
    item = parse_detail(load("europarl_plenary_other_committee.json"))
    assert item is None


def test_parse_detail_rejects_missing_adopts():
    doc = load("europarl_plenary_afet.json")
    doc["adopts"] = []
    assert parse_detail(doc) is None


def test_parse_detail_rejects_missing_english_expression():
    doc = load("europarl_plenary_afet.json")
    doc["is_realized_by"] = [e for e in doc["is_realized_by"] if not e["id"].endswith("/en")]
    assert parse_detail(doc) is None


def test_parse_detail_detects_region_from_title():
    item = parse_detail(load("europarl_plenary_deve.json"))
    assert "Sub-Saharan Africa" in item["regions"]


def test_committee_from_adopts_matches_known_prefix():
    assert _committee_from_adopts(["eli/dl/doc/AFET-PR-770055"]) == "AFET"
    assert _committee_from_adopts(["eli/dl/doc/DEVE-PR-771200"]) == "DEVE"


def test_committee_from_adopts_ignores_other_committees():
    assert _committee_from_adopts(["eli/dl/doc/ECON-PR-778306"]) is None


def test_committee_from_adopts_handles_empty():
    assert _committee_from_adopts([]) is None
    assert _committee_from_adopts(None) is None


def test_doc_number_sorts_newest_first():
    identifiers = ["A-10-2026-0003", "A-10-2026-0042", "A-10-2026-0001"]
    identifiers.sort(key=_doc_number, reverse=True)
    assert identifiers == ["A-10-2026-0042", "A-10-2026-0003", "A-10-2026-0001"]


def test_doc_number_handles_malformed_identifier():
    assert _doc_number("not-a-real-id") == -1
