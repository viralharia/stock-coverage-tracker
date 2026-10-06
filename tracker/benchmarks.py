"""Market-cap segment -> benchmark index mapping.

Yahoo Finance symbols verified 2026-10-05:
  Nifty 50          -> ^NSEI
  Nifty Next 50     -> ^NSMIDCP
  Nifty Midcap 150  -> NIFTYMIDCAP150.NS
  Nifty Smallcap 250-> NIFTYSMLCAP250.NS
"""
INDEXES = {
    "large": {"label": "Nifty 50", "symbol": "^NSEI"},
    "mid": {"label": "Nifty Midcap 150", "symbol": "NIFTYMIDCAP150.NS"},
    "small": {"label": "Nifty Smallcap 250", "symbol": "NIFTYSMLCAP250.NS"},
    # available as an explicit override only (auto-classify never picks this)
    "next50": {"label": "Nifty Next 50", "symbol": "^NSMIDCP"},
}

# Approximate SEBI-style cutoffs by market cap (INR crores).
# SEBI defines segments by rank, which drifts; these value bands are a proxy.
# Override per ticker via add_ticker(..., segment="mid") when known.
LARGE_CAP_MIN_CR = 80000
MID_CAP_MIN_CR = 22000


def classify(market_cap_cr):
    if market_cap_cr >= LARGE_CAP_MIN_CR:
        return "large"
    if market_cap_cr >= MID_CAP_MIN_CR:
        return "mid"
    return "small"
