# EEAS Diplomatic Statements Monitor

A small pipeline that tracks EU diplomatic statements, declarations and speeches, and
renders them as a searchable/filterable feed. It's the starting point for a broader EU
monitoring tool — see [Roadmap](#roadmap) for what's planned next (MEPs, Twitter/X, etc).

**Live site:** `index.html`, served via GitHub Pages, reads `data/statements.json`.

## How it works

```
GitHub Actions (hourly cron)
  -> scraper.py
       -> sources/presscorner.py       (European Commission press releases/speeches/statements)
       -> sources/eeas_portal.py       (EEAS press material portal)
       -> sources/europarl_plenary.py  (EP plenary reports/recommendations, AFET + DEVE only)
  -> data/statements.json (deduped, sorted newest-first, capped at 1000)
  -> index.html reads that JSON client-side and renders the feed
```

`.github/workflows/update.yml` runs `scraper.py` once an hour and commits any new
statements back to `data/statements.json`. `.github/workflows/test.yml` runs the test
suite on every push/PR to `main`.

## Data schema

Every statement is a dict with these fields:

| field     | meaning                                                              |
|-----------|-----------------------------------------------------------------------|
| `id`      | stable unique id for the item (source-specific — e.g. PressCorner's `refCode`, or an md5 hash of the URL for sources without a native id) |
| `title`   | statement/speech title                                                |
| `link`    | canonical URL                                                         |
| `date`    | `YYYY-MM-DD`                                                          |
| `type`    | e.g. "Speech", "Statement", "Press release", "Déclaration"            |
| `speaker` | named speaker if extractable, else a generic org name                 |
| `source`  | which source produced it (matches that source module's `SOURCE_NAME`) |
| `regions` | list of region tags, keyword-detected from the title/body (see `regions.py`) |
| `summary` | short blurb, may be empty if the source doesn't provide one           |

## Adding a new source

This is the main extension point — see the docstring at the top of `sources/__init__.py`
for the exact contract. In short: each source is a module in `sources/` exposing
`SOURCE_NAME`, a `fetch()` that hits the network and returns normalized item dicts, and
a pure `parse_*()` function factored out of `fetch()` so it's unit-testable against a
saved fixture. Register it in `sources/__init__.py`'s `SOURCES` list and it's picked up
automatically — `scraper.py`'s dedup/merge/write logic doesn't need to change.

If a new source needs credentials (e.g. a Twitter/X API bearer token), read them from
`os.environ` inside the module and add the secret to the repo's Actions secrets plus
this workflow's `env:` block. Never hardcode a credential.

## Roadmap

- **European Parliament plenary reports (AFET/DEVE)** — done, see `sources/europarl_plenary.py`.
  MEPs-as-a-source (individual speeches/questions) beyond this is still open — see
  "Known limitations" below for why parliamentary questions specifically were passed
  over for now.
- **Twitter/X feeds** (e.g. official EU institution accounts) — planned as
  `sources/twitter_x.py`, will need an API credential (see above).
- **European Council / Council of the EU statements** (`consilium.europa.eu`) —
  investigated and currently blocked: the site sits behind a Cloudflare bot-protection
  challenge that rejects plain HTTP requests regardless of headers. Getting this source
  would require a headless browser (e.g. Playwright) in the Action, which is a bigger
  lift than the current requests-based sources. Not started yet.

## Known limitations

- **Pagination isn't real for either current source.** Both the PressCorner API's
  `pageNumber` param and the EEAS portal's `page` param are silently ignored
  server-side (verified: requesting page 0/1/2 returns identical results either way).
  So each source only fetches its single newest batch (~50 PressCorner items, ~36 EEAS
  items) per run. This is fine for the hourly-monitoring use case — dedup means we only
  ever add genuinely new items — but it means there's no way to backfill deep history
  through these endpoints as currently reachable.
- **PressCorner's `docType=STATEMENT` filter isn't actually respected server-side** —
  the API returns a mix of statements, speeches, press releases and daily news
  regardless of that parameter. Harmless (more content, still deduped/typed correctly
  from the response), but worth knowing if you're relying on it to *exclude* types.
- Region detection (`regions.py`) is keyword/word-boundary matching, not NLP — good
  enough for a first pass, but it can miss or misattribute edge cases.
- **`europarl_plenary`'s document link is an unverified best-guess.** It follows EP's
  well-known `doceo/document/{id}_EN.html` convention, but `www.europarl.europa.eu`
  returns HTTP 202 with an empty body to plain (non-browser) requests — for both
  plausible and deliberately-wrong paths alike — so a live fetch can't actually confirm
  the pattern is correct. Spot-check a few generated links after this source has run.
- **`europarl_plenary` only covers formal plenary reports/recommendations**, not MEPs'
  individual speeches or written questions. The EP Open Data API's
  `/parliamentary-questions` endpoint was investigated and rejected for now: its
  `date-from`/`date-to` params are silently ignored (same class of bug as the
  pagination issue above), there's no committee filter either, and the volume is very
  high (thousands/year, mostly unrelated to foreign affairs) — it would need real
  filtering work to be useful rather than noise. Verbatim plenary debate speeches were
  not investigated at all yet and remain the most promising untried EP source.
- **`europarl_plenary` has no committee-level API filter**, so it can't cheaply ask
  "give me only AFET/DEVE documents." It works around this by listing all document
  stubs for the year (cheap) and only running the expensive per-document detail fetch
  (which is what reveals the committee) against the `_MAX_DETAIL_FETCHES` (60)
  numerically-newest ones. If EP's output volume grows enough that AFET/DEVE documents
  fall outside that window between hourly runs, some could be missed — worth revisiting
  if that cap ever needs raising.

## Local development

```
pip install -r requirements.txt pytest
pytest tests/ -v          # unit tests, no network required
python scraper.py         # runs the real scrape against live sources
```
