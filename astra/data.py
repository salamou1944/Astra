from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
import csv
from typing import Iterable

@dataclass(frozen=True)
class OHLCV:
    t: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

@dataclass(frozen=True)
class DataAudit:
    bars: int
    start: str
    end: str
    duplicates: int
    non_monotonic: int
    invalid_ohlc: int
    negative_volume: int
    naive_timestamps: int
    status: str

def _parse_ts(value: str) -> datetime:
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError("timestamps must include timezone information")
    return dt.astimezone(timezone.utc)

def validate_bars(bars: Iterable[OHLCV]) -> list[OHLCV]:
    out = list(bars)
    if len(out) < 2:
        raise ValueError("at least 2 bars required")
    prev = None
    for b in out:
        if any(x != x for x in (b.open, b.high, b.low, b.close, b.volume)):
            raise ValueError("NaN values are not allowed")
        if b.high < max(b.open, b.close) or b.low > min(b.open, b.close):
            raise ValueError("invalid OHLC relationship")
        if b.high < b.low or b.volume < 0:
            raise ValueError("invalid OHLCV values")
        current = _parse_ts(b.t)
        if prev is not None and current <= prev:
            raise ValueError("timestamps must be strictly increasing")
        prev = current
    return out

def audit_bars(bars: Iterable[OHLCV]) -> DataAudit:
    raw = list(bars)
    if not raw:
        return DataAudit(0, "", "", 0, 0, 0, 0, 0, "FAILED")
    seen = set(); duplicates = 0; non_monotonic = 0; invalid = 0; neg = 0; naive = 0
    previous = None
    for b in raw:
        try: dt = _parse_ts(b.t)
        except ValueError:
            naive += 1
            continue
        if b.t in seen: duplicates += 1
        seen.add(b.t)
        if previous is not None and dt <= previous: non_monotonic += 1
        previous = dt
        if b.high < max(b.open, b.close) or b.low > min(b.open, b.close) or b.high < b.low: invalid += 1
        if b.volume < 0: neg += 1
    try:
        start = _parse_ts(raw[0].t).isoformat().replace('+00:00','Z')
        end = _parse_ts(raw[-1].t).isoformat().replace('+00:00','Z')
    except ValueError:
        start = raw[0].t; end = raw[-1].t
    status = "PASS" if not any((duplicates, non_monotonic, invalid, neg, naive)) and len(raw) >= 2 else "FAIL"
    return DataAudit(len(raw), start, end, duplicates, non_monotonic, invalid, neg, naive, status)

def load_csv(path: str | Path) -> list[OHLCV]:
    p = Path(path)
    with p.open(newline="", encoding="utf-8") as f:
        rows = csv.DictReader(f)
        required = {"timestamp", "open", "high", "low", "close"}
        if not required.issubset(set(rows.fieldnames or [])):
            raise ValueError(f"CSV must contain {sorted(required)}")
        bars = [OHLCV(r["timestamp"], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), float(r.get("volume") or 0.0)) for r in rows]
    return validate_bars(bars)

def to_close_bars(bars: Iterable[OHLCV]):
    from .core import Bar
    return [Bar(i, b.close) for i, b in enumerate(bars)]
