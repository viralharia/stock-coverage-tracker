# stock-coverage-tracker

Tracks broker **initiating-coverage** stock picks: initiation date, % return
to today, and — keyed off market cap — the matching benchmark index
(Nifty 50 / Nifty Midcap 150 / Nifty Smallcap 250) with that index's return over
the same window. Excess return = stock return − index return.

Multi-broker by design: every pick carries a `source` (broker) field, shown as
the Broker column on the dashboard. Add picks from any broker via the same API.

The dashboard is `index.html` (served via GitHub Pages), reading `data/picks.json`.

## Layout

- `tracker/` — the modular library. The **API**:
  - `add_ticker(symbol, initiation_date, source="Motilal Oswal", target=None, rating=None, segment=None, note="")`
    adds a ticker **and runs the full calculation** (initiation close, latest close,
    market cap → segment → benchmark index, index returns, excess).
  - `remove_ticker(symbol)` — stop tracking a ticker.
  - `refresh_all()` — EOD refresh of latest prices for every pick.
  - `list_picks()` — all tracked picks.
- `cli.py` — command-line wrapper: `add | remove | refresh | list`.
- `data/picks.json` — the data the dashboard renders.
- `index.html` — the portal (static, no build step).

No pip dependencies — everything is stdlib + Yahoo Finance.

## Methodology notes

- Prices: Yahoo Finance NSE closes. Initiation price = close on the initiation
  date, or the nearest prior trading day (recorded as `initiation_price_date`).
- Segment: by market cap — large ≥ ₹80,000 cr, mid ≥ ₹22,000 cr, else small.
  SEBI defines segments by rank, which drifts, so these bands are an
  approximation; override per ticker with `segment=` when known.
- Benchmarks (Yahoo symbols verified 2026-10-05): large → Nifty 50 (`^NSEI`),
  mid → Nifty Midcap 150 (`NIFTYMIDCAP150.NS`), small → Nifty Smallcap 250
  (`NIFTYSMLCAP250.NS`). Nifty Next 50 (`^NSMIDCP`) available as an override.
- Educational tracking only — not investment advice.

## Automation (lives OUTSIDE this repo)

The mail watcher + daily refresher are deliberately not part of this repo (they
need mailbox access). They live on the operator's machine, import `tracker` as a
library, and push updated `data/picks.json` back here:

- **On new initiating-coverage mail** → extract ticker/date/target/rating →
  `tracker.add_ticker(...)` → commit + push.
- **Daily EOD** (after NSE close) → `tracker.refresh_all()` → commit + push.
  Pages redeploys the portal automatically.
