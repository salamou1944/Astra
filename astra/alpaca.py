from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://data.alpaca.markets/v1beta3/crypto/us/bars"

@dataclass(frozen=True)
class MarketFetch:
    symbol: str
    timeframe: str
    start: str
    end: str | None
    bars: list[dict]
    source: str = BASE_URL
    pages: int = 1
    request_ids: tuple[str, ...] = ()

def _iso(value: str | datetime) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
    return value

def fetch_crypto_bars(symbol: str = "BTC/USD", timeframe: str = "1Day", start: str | datetime | None = None,
                      end: str | datetime | None = None, limit: int = 1000, timeout: float = 15.0,
                      max_pages: int = 20) -> MarketFetch:
    if not symbol or "/" not in symbol:
        raise ValueError("symbol must look like BTC/USD")
    if limit < 1 or limit > 10000:
        raise ValueError("limit must be between 1 and 10000")
    if max_pages < 1:
        raise ValueError("max_pages must be positive")
    params = {"symbols": symbol, "timeframe": timeframe, "limit": limit, "sort": "asc"}
    if start is not None: params["start"] = _iso(start)
    if end is not None: params["end"] = _iso(end)
    bars: list[dict] = []
    request_ids: list[str] = []
    page_token = None
    pages = 0
    while pages < max_pages:
        query = dict(params)
        if page_token:
            query["page_token"] = page_token
        url = BASE_URL + "?" + urlencode(query)
        req = Request(url, headers={"User-Agent": "AstraQuantLab/0.5"})
        with urlopen(req, timeout=timeout) as response:
            request_id = response.headers.get("X-Request-ID")
            if request_id: request_ids.append(request_id)
            payload = json.load(response)
        rows = payload.get("bars", {}).get(symbol, [])
        bars.extend(rows)
        pages += 1
        page_token = payload.get("next_page_token")
        if not page_token:
            break
    if not bars:
        raise ValueError(f"no bars returned for {symbol}")
    return MarketFetch(symbol, timeframe, params.get("start", ""), params.get("end"), bars, pages=pages, request_ids=tuple(request_ids))

def to_ohlcv(fetch: MarketFetch):
    from .data import OHLCV, validate_bars
    bars = [OHLCV(r["t"], float(r["o"]), float(r["h"]), float(r["l"]), float(r["c"]), float(r.get("v", 0.0))) for r in fetch.bars]
    return validate_bars(bars)
