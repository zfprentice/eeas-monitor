"""Registry of statement sources.

To add a new source (e.g. European Parliament / MEPs, or a Twitter/X feed):

1. Create sources/<name>.py exposing:
   - SOURCE_NAME: str, used as the "source" field on every item it produces
   - fetch() -> list[dict]: does the network call(s) and returns normalized items
   - a pure parse_*(raw) -> list[dict] function factored out of fetch(), so it can
     be unit tested against a saved fixture without hitting the network (see
     tests/ for the pattern used by presscorner.py and eeas_portal.py)

   Every item dict must have these keys: id, title, link, date (YYYY-MM-DD),
   type, speaker, source, regions (list[str]), summary.

   If the source needs credentials (e.g. a Twitter/X API bearer token), read them
   from os.environ inside the module and add the corresponding secret to the repo's
   Actions secrets + this workflow's `env:` block — never hardcode a credential.

2. Import the module below and add it to SOURCES.

That's it — scraper.py's main() loop, dedup, and data/statements.json writing are
generic across all registered sources.
"""

from sources import eeas_portal, presscorner

SOURCES = [presscorner, eeas_portal]
