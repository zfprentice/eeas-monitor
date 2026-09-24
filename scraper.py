import json
import os
import sys
import time

from sources import SOURCES

DATA_PATH = "data/statements.json"

# Politeness delay between hitting different sources' servers.
_SOURCE_DELAY_SECONDS = 2

# Store up to this many historical statements.
_MAX_STORED = 1000


def merge_items(existing, new_items):
    """Dedup new_items by id against existing, sort newest-first, cap at _MAX_STORED.

    Returns (merged_list, added_count). Pure function, no I/O, so it's unit-testable.
    """
    seen_ids = {x["id"] for x in existing if "id" in x}
    merged = list(existing)
    added = 0
    for item in new_items:
        if item["id"] not in seen_ids and item["title"]:
            merged.append(item)
            seen_ids.add(item["id"])
            added += 1

    merged.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return merged[:_MAX_STORED], added


def collect_from_all_sources():
    """Fetch every registered source, returning (all_items, any_source_succeeded)."""
    all_items = []
    any_source_succeeded = False
    for i, source in enumerate(SOURCES):
        if i > 0:
            time.sleep(_SOURCE_DELAY_SECONDS)
        items = source.fetch()
        print(f"[{source.SOURCE_NAME}] collected {len(items)} items")
        if items:
            any_source_succeeded = True
        else:
            print(f"WARNING: {source.SOURCE_NAME} returned 0 items this run (source may be broken).")
        all_items.extend(items)
    return all_items, any_source_succeeded


def main():
    os.makedirs("data", exist_ok=True)
    existing = []
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    new_items, any_source_succeeded = collect_from_all_sources()

    if not any_source_succeeded and not existing:
        print("ERROR: every source returned zero items and there is no existing data. "
              "This likely means a source has changed its API/markup. Failing the run "
              "instead of writing an empty dataset.")
        sys.exit(1)

    merged, added = merge_items(existing, new_items)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved {len(merged)} statements to {DATA_PATH} ({added} new).")


if __name__ == "__main__":
    main()
