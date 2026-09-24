from scraper import merge_items, _MAX_STORED


def make_item(id_, date, title="Title"):
    return {"id": id_, "title": title, "date": date, "source": "test"}


def test_merge_items_dedupes_by_id():
    existing = [make_item("a", "2026-01-01")]
    new_items = [make_item("a", "2026-01-01"), make_item("b", "2026-01-02")]
    merged, added = merge_items(existing, new_items)
    assert added == 1
    assert {i["id"] for i in merged} == {"a", "b"}


def test_merge_items_dedupes_within_new_batch():
    existing = []
    new_items = [make_item("a", "2026-01-01"), make_item("a", "2026-01-01")]
    merged, added = merge_items(existing, new_items)
    assert added == 1
    assert len(merged) == 1


def test_merge_items_sorts_newest_first():
    existing = [make_item("old", "2020-01-01")]
    new_items = [make_item("new", "2026-01-01"), make_item("mid", "2023-01-01")]
    merged, _ = merge_items(existing, new_items)
    assert [i["id"] for i in merged] == ["new", "mid", "old"]


def test_merge_items_skips_empty_title():
    existing = []
    new_items = [make_item("a", "2026-01-01", title="")]
    merged, added = merge_items(existing, new_items)
    assert added == 0
    assert merged == []


def test_merge_items_caps_at_max_stored():
    existing = [make_item(str(i), f"2020-01-{i:02d}") for i in range(1, 10)]
    new_items = [make_item(f"new{i}", "2026-01-01") for i in range(_MAX_STORED)]
    merged, _ = merge_items(existing, new_items)
    assert len(merged) == _MAX_STORED
