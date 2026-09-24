import json
import os

from sources.presscorner import extract_speaker, parse_response

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "presscorner_response.json")


def load_fixture():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_parse_response_extracts_all_items():
    items = parse_response(load_fixture())
    assert len(items) == 4


def test_parse_response_builds_correct_detail_link():
    items = parse_response(load_fixture())
    speech = next(i for i in items if i["id"] == "SPEECH/26/1968")
    assert speech["link"] == "https://ec.europa.eu/commission/presscorner/detail/en/speech_26_1968"


def test_parse_response_maps_fields():
    items = parse_response(load_fixture())
    press_release = next(i for i in items if i["id"] == "IP/26/1954")
    assert press_release["type"] == "Press release"
    assert press_release["date"] == "2026-09-23"
    assert press_release["source"] == "Commission PressCorner (HQ)"
    assert "OceanEye" in press_release["summary"]


def test_parse_response_handles_missing_leadtext():
    items = parse_response(load_fixture())
    speech = next(i for i in items if i["id"] == "SPEECH/26/1968")
    assert speech["summary"] == ""


def test_parse_response_skips_empty_title():
    data = load_fixture()
    data["docuLanguageListResources"].append(
        {"refCode": "IP/26/9999", "title": "  ", "eventDate": "2026-09-24", "docutype": {"description": "Press release"}}
    )
    items = parse_response(data)
    assert all(i["id"] != "IP/26/9999" for i in items)


def test_parse_response_handles_empty_payload():
    assert parse_response({"docuLanguageListResources": []}) == []
    assert parse_response({}) == []


def test_extract_speaker_finds_named_role():
    assert extract_speaker("Speech by President von der Leyen at the High-Level meeting") == "President von der Leyen"
    assert extract_speaker("Opening remarks by Commissioner Hansen at the EU AgRI 2040") == "Commissioner Hansen"


def test_extract_speaker_falls_back_when_no_name():
    assert extract_speaker("EU and Canada secure pledges for Global Ocean Observation") == "European Commission"
    assert extract_speaker("Daily News 23 / 09 / 2026") == "European Commission"
