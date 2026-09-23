from __future__ import annotations
import json
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from datetime import datetime, timezone

BASE_URL = "https://api.binance.com/api/v3/klines"

@dataclass(frozen=True)
class BinanceFetch:
    symbol: str
    interval: str
    bars: list[list]
    pages: int = 1

_INTERVALS = {"1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d","3d","1w","1M"}

def fetch_klines(symbol="BTCUSDT", interval="1d", start_ms=None, end_ms=None, limit=1000, timeout=15.0, max_pages=20):
    if not symbol or "/" in symbol: raise ValueError("Binance symbol must look like BTCUSDT")
    if interval not in _INTERVALS: raise ValueError("unsupported Binance interval")
    if not 1 <= limit <= 1000: raise ValueError("limit must be between 1 and 1000")
    bars=[]; cursor=start_ms; pages=0
    while pages < max_pages:
        q={"symbol":symbol,"interval":interval,"limit":limit}
        if cursor is not None: q["startTime"]=int(cursor)
        if end_ms is not None: q["endTime"]=int(end_ms)
        req=Request(BASE_URL+"?"+urlencode(q),headers={"User-Agent":"AstraQuantLab/0.8"})
        with urlopen(req,timeout=timeout) as response: rows=json.load(response)
        if not rows: break
        bars.extend(rows); pages += 1
        if len(rows) < limit: break
        next_cursor=int(rows[-1][0])+1
        if cursor is not None and next_cursor <= int(cursor): raise RuntimeError("non-advancing Binance pagination")
        cursor=next_cursor
        if end_ms is not None and cursor > int(end_ms): break
    if not bars: raise ValueError(f"no bars returned for {symbol}")
    return BinanceFetch(symbol, interval, bars, pages)

def to_ohlcv(fetch: BinanceFetch):
    from .data import OHLCV, validate_bars
    bars=[OHLCV(datetime.fromtimestamp(r[0]/1000, tz=timezone.utc).isoformat().replace("+00:00","Z"),float(r[1]),float(r[2]),float(r[3]),float(r[4]),float(r[5])) for r in fetch.bars]
    return validate_bars(bars)
