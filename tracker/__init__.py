"""Motilal Oswal initiating-coverage tracker — modular API.

Public API:
    add_ticker(symbol, initiation_date, ...)  -> add a pick and run the full calculation
    remove_ticker(symbol)                     -> drop a pick
    refresh_all()                             -> EOD refresh of prices for every pick
    list_picks()                              -> all tracked picks
"""
from .api import add_ticker, remove_ticker, refresh_all, list_picks

__all__ = ["add_ticker", "remove_ticker", "refresh_all", "list_picks"]
