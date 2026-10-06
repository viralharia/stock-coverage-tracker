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

## Automation

**Daily EOD refresh** runs inside this repo via GitHub Actions
(`.github/workflows/refresh.yml`): every Mon–Fri at 11:15 UTC (4:45 PM IST,
after the NSE close) it runs `python cli.py refresh`, commits the updated
`data/picks.json`, and Pages redeploys the portal. Fully automatic — no
approvals, no tokens. `workflow_dispatch` allows a manual run from the
Actions tab.

**Mail watcher (outside this repo):** when a new initiating-coverage mail
arrives, the operator's automation extracts ticker/date/target/rating and
calls `tracker.add_ticker(...)` — adding a ticker runs the full calculation —
then pushes the updated `data/picks.json` here. Kept separate because it
needs mailbox access, which doesn't belong in the repo.
