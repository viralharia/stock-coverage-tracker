#!/usr/bin/env python3
"""CLI for the coverage tracker.

    python cli.py add RELIANCE --date 2026-10-05 --target 1650 --rating Buy
    python cli.py add TCS.NS --date 2026-09-01 --segment large
    python cli.py remove RELIANCE
    python cli.py refresh
    python cli.py list
"""
import argparse
import json

from tracker import add_ticker, list_picks, refresh_all, remove_ticker


def main():
    ap = argparse.ArgumentParser(description="Motilal Oswal coverage tracker")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Add a ticker and run the calculation")
    a.add_argument("symbol")
    a.add_argument("--date", required=True, help="Initiation date YYYY-MM-DD")
    a.add_argument("--source", default="Motilal Oswal")
    a.add_argument("--target", type=float, default=None)
    a.add_argument("--rating", default=None)
    a.add_argument("--segment", default=None, help="large/mid/small/next50 (auto if omitted)")
    a.add_argument("--note", default="")

    r = sub.add_parser("remove", help="Remove a ticker")
    r.add_argument("symbol")

    sub.add_parser("refresh", help="EOD refresh of all picks")
    sub.add_parser("list", help="List tracked picks")

    args = ap.parse_args()
    if args.cmd == "add":
        rec = add_ticker(args.symbol, args.date, source=args.source,
                         target=args.target, rating=args.rating,
                         segment=args.segment, note=args.note)
        print(json.dumps(rec, indent=2))
    elif args.cmd == "remove":
        print("removed", remove_ticker(args.symbol))
    elif args.cmd == "refresh":
        print("refreshed", refresh_all(), "picks")
    elif args.cmd == "list":
        for p in list_picks():
            print(f'{p["symbol"]:22} {p["initiation_date"]}  '
                  f'stock {p["stock_return_pct"]:+.1f}%  '
                  f'{p["benchmark"]} {p["index_return_pct"]:+.1f}%  '
                  f'excess {p["excess_pct"]:+.1f}%')


if __name__ == "__main__":
    main()
