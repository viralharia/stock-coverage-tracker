"""Public API for the coverage tracker.

Price fetching is pluggable: pass a PriceProvider, or pass pre-fetched prices
(a fetch_bundle() dict) to skip network access entirely — the calculation
itself is pure math.
"""
import datetime

from . import benchmarks, prices as prices_mod, store


def _normalize(symbol):
    s = symbol.strip().upper()
    if "." not in s:
        s += ".NS"  # default to NSE
    return s


def _pct(new, old):
    return round((new - old) / old * 100, 2) if old else None


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def add_ticker(symbol, initiation_date, source="Motilal Oswal", target=None,
               rating=None, segment=None, note="", prices=None, provider=None):
    """Add a ticker and run the full calculation.

    Fetches the initiation-day close, latest close, market cap -> segment ->
    benchmark index, and index returns over the same window; stores stock /
    index / excess returns. Returns the stored record.

    Pass `prices=` (a prices.fetch_bundle() dict) to skip network fetching,
    e.g. when prices were verified through another channel.
    """
    sym = _normalize(symbol)
    data = store.load()
    if any(p["symbol"] == sym for p in data["picks"]):
        raise ValueError(f"{sym} is already tracked")

    if prices is None:
        prov = provider or prices_mod.YahooProvider()
        prices = prices_mod.fetch_bundle(prov, sym, initiation_date,
                                         segment_override=segment)
    seg = prices["segment"]
    (init_day, init_price) = prices["init"]
    (latest_day, latest_price) = prices["latest"]
    (b_init_day, b_init) = prices["bench_init"]
    (b_latest_day, b_latest) = prices["bench_latest"]

    stock_ret = _pct(latest_price, init_price)
    index_ret = _pct(b_latest, b_init)

    record = {
        "symbol": sym,
        "name": prices["name"],
        "source": source,
        "initiation_date": initiation_date,
        "initiation_price": init_price,
        "initiation_price_date": init_day,
        "target": target,
        "rating": rating,
        "note": note,
        "market_cap_cr": prices["mcap_cr"],
        "segment": seg,
        "benchmark": prices["benchmark"],
        "benchmark_symbol": prices["benchmark_symbol"],
        "benchmark_init": b_init,
        "benchmark_init_date": b_init_day,
        "latest_price": latest_price,
        "latest_date": latest_day,
        "benchmark_latest": b_latest,
        "benchmark_latest_date": b_latest_day,
        "stock_return_pct": stock_ret,
        "index_return_pct": index_ret,
        "excess_pct": round(stock_ret - index_ret, 2),
        "updated_at": _now(),
    }
    data["picks"].append(record)
    data["picks"].sort(key=lambda p: p["initiation_date"], reverse=True)
    store.save(data)
    return record


def remove_ticker(symbol):
    """Stop tracking a ticker. Returns the removed symbol."""
    sym = _normalize(symbol)
    data = store.load()
    before = len(data["picks"])
    data["picks"] = [p for p in data["picks"] if p["symbol"] != sym]
    if len(data["picks"]) == before:
        raise ValueError(f"{sym} is not tracked")
    store.save(data)
    return sym


def refresh_all(provider=None, bundles=None):
    """EOD refresh: update latest prices + benchmark levels for every pick.

    Pass `bundles=` {symbol: {"latest": (date, close),
    "bench_latest": (date, close)}} to skip network fetching.
    Returns the number of picks refreshed.
    """
    data = store.load()
    prov = provider or prices_mod.YahooProvider()
    for p in data["picks"]:
        if bundles and p["symbol"] in bundles:
            b = bundles[p["symbol"]]
            latest_day, latest_price = b["latest"]
            b_day, b_latest = b["bench_latest"]
            # Bundle callers must pass benchmark levels on the same scale as
            # p["benchmark_init"] (raw index levels, not rebased).
            b_init_day, b_init = b.get("bench_init", (p["benchmark_init_date"],
                                                      p["benchmark_init"]))
        else:
            latest_day, latest_price = prov.latest_close(p["symbol"])
            # Always re-derive the raw index level at initiation: stored
            # benchmark_init values may predate the raw-level migration
            # (early seeds were rebased to 100), and comparing a raw latest
            # level against a rebased init is what produced the 68000% bug.
            b_init_day, b_init = prov.close_on_or_before(
                p["benchmark_symbol"], p["initiation_date"])
            b_day, b_latest = prov.latest_close(p["benchmark_symbol"])
        p["latest_price"] = latest_price
        p["latest_date"] = latest_day
        p["benchmark_init"] = b_init
        p["benchmark_init_date"] = b_init_day
        p["benchmark_latest"] = b_latest
        p["benchmark_latest_date"] = b_day
        p["stock_return_pct"] = _pct(latest_price, p["initiation_price"])
        p["index_return_pct"] = _pct(b_latest, b_init)
        p["excess_pct"] = round(p["stock_return_pct"] - p["index_return_pct"], 2)
        p["updated_at"] = _now()
    store.save(data)
    return len(data["picks"])


def list_picks():
    return store.load()["picks"]
