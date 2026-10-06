"""Price providers. Stdlib only.

The default provider is Yahoo Finance, which works on normal networks
(your laptop, GitHub Actions). On restricted networks, skip fetching and pass
pre-fetched prices into the API instead — see README and api.add_ticker().
"""
import datetime
import json
import urllib.request

_UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
_TIMEOUT = 25


def _fetch_json(url):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.load(resp)


class PriceProvider:
    """Interface: closes(), close_on_or_before(), latest_close(), quote()."""

    def closes(self, symbol, from_date, to_date):
        raise NotImplementedError

    def close_on_or_before(self, symbol, date_str):
        d = datetime.date.fromisoformat(date_str)
        frm = (d - datetime.timedelta(days=15)).isoformat()
        rows = self.closes(symbol, frm, date_str)
        if not rows:
            raise ValueError(f"no price for {symbol} on or before {date_str}")
        return rows[-1]

    def latest_close(self, symbol):
        today = datetime.date.today()
        frm = (today - datetime.timedelta(days=10)).isoformat()
        rows = self.closes(symbol, frm, today.isoformat())
        if not rows:
            raise ValueError(f"no recent price for {symbol}")
        return rows[-1]

    def quote(self, symbol):
        """Returns (market_cap_inr_crores, company_name)."""
        raise NotImplementedError


class YahooProvider(PriceProvider):
    def closes(self, symbol, from_date, to_date):
        def ts(date_str):
            d = datetime.date.fromisoformat(date_str)
            return int(datetime.datetime(d.year, d.month, d.day,
                                          tzinfo=datetime.timezone.utc).timestamp())

        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
               f"?period1={ts(from_date) - 3 * 86400}&period2={ts(to_date) + 2 * 86400}"
               f"&interval=1d")
        data = _fetch_json(url)
        result = (data.get("chart") or {}).get("result")
        if not result:
            raise ValueError(f"no chart data for {symbol}")
        bar = result[0]
        ts_list = bar.get("timestamp") or []
        raw = (bar.get("indicators") or {}).get("quote", [{}])[0].get("close") or []
        out = []
        for t, c in zip(ts_list, raw):
            if c is None:
                continue
            day = datetime.datetime.fromtimestamp(
                t, tz=datetime.timezone.utc).date().isoformat()
            if from_date <= day <= to_date:
                out.append((day, round(float(c), 2)))
        return out

    def quote(self, symbol):
        url = ("https://query1.finance.yahoo.com/v7/finance/quote"
               f"?symbols={symbol}&fields=marketCap,longName,shortName")
        data = _fetch_json(url)
        results = (data.get("quoteResponse") or {}).get("result") or []
        if not results:
            raise ValueError(f"no quote for {symbol}")
        q = results[0]
        mcap = q.get("marketCap")
        if not mcap:
            raise ValueError(f"no market cap for {symbol}")
        name = q.get("longName") or q.get("shortName") or symbol
        return round(mcap / 1e7, 1), name  # INR -> crores


def fetch_bundle(provider, symbol, initiation_date, segment_override=None):
    """Fetch everything add_ticker needs. Returns a dict (same shape the API
    accepts as `prices=` to skip network fetching)."""
    from . import benchmarks

    init_day, init_price = provider.close_on_or_before(symbol, initiation_date)
    latest_day, latest_price = provider.latest_close(symbol)
    mcap_cr, name = provider.quote(symbol)
    seg = (segment_override or benchmarks.classify(mcap_cr)).lower()
    if seg not in benchmarks.INDEXES:
        raise ValueError(f"unknown segment {segment_override!r}")
    bench = benchmarks.INDEXES[seg]
    b_init_day, b_init = provider.close_on_or_before(bench["symbol"], initiation_date)
    b_latest_day, b_latest = provider.latest_close(bench["symbol"])
    return {
        "name": name,
        "init": (init_day, init_price),
        "latest": (latest_day, latest_price),
        "mcap_cr": mcap_cr,
        "segment": seg,
        "benchmark": bench["label"],
        "benchmark_symbol": bench["symbol"],
        "bench_init": (b_init_day, b_init),
        "bench_latest": (b_latest_day, b_latest),
    }
