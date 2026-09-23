from __future__ import annotations
import csv, hashlib, json, time, urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BINANCE_API = 'https://data-api.binance.vision/api/v3/klines'
BINANCE_ARCHIVE = 'https://data.binance.vision/data/spot/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{day}.zip'

@dataclass(frozen=True)
class FetchResult:
    status: str
    source: str
    symbol: str
    interval: str
    rows: int
    path: str | None
    sha256: str | None
    error: str | None

def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def download_binance_daily_archive(symbol: str, day: str, out_dir: str|Path, timeout: int=20) -> FetchResult:
    symbol=symbol.upper(); interval='1d'; out=Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    url=BINANCE_ARCHIVE.format(symbol=symbol, interval=interval, day=day)
    target=out/f'{symbol}-{interval}-{day}.zip'
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r: data=r.read()
        target.write_bytes(data)
        return FetchResult('SOURCE_FETCHED','binance_public_archive',symbol,interval,0,str(target),_sha256(target),None)
    except Exception as e:
        return FetchResult('BLOCKED','binance_public_archive',symbol,interval,0,None,None,repr(e))

def fetch_binance_klines(symbol: str, start_ms: int, end_ms: int, out_csv: str|Path, timeout: int=20, limit: int=1000) -> FetchResult:
    symbol=symbol.upper(); out=Path(out_csv); out.parent.mkdir(parents=True, exist_ok=True)
    rows=[]; cursor=start_ms
    try:
        while cursor <= end_ms:
            q=f'{BINANCE_API}?symbol={symbol}&interval=1d&startTime={cursor}&endTime={end_ms}&limit={limit}'
            req=urllib.request.Request(q,headers={'User-Agent':'ASTRA-Quant-Lab/1.0'})
            with urllib.request.urlopen(req, timeout=timeout) as r: payload=json.loads(r.read())
            if not payload: break
            rows.extend(payload)
            nxt=int(payload[-1][0])+86400000
            if nxt <= cursor: raise RuntimeError('non-advancing Binance cursor')
            cursor=nxt
            if len(payload)<limit: break
            time.sleep(0.05)
        with out.open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['timestamp','open','high','low','close','volume'])
            for k in rows:
                ts=datetime.fromtimestamp(k[0]/1000,tz=timezone.utc).isoformat().replace('+00:00','Z')
                w.writerow([ts,k[1],k[2],k[3],k[4],k[5]])
        return FetchResult('SOURCE_FETCHED','binance_public_api',symbol,'1d',len(rows),str(out),_sha256(out),None)
    except Exception as e:
        return FetchResult('BLOCKED','binance_public_api',symbol,'1d',len(rows),None,None,repr(e))

KRAKEN_OHLC = 'https://api.kraken.com/0/public/OHLC'

def fetch_kraken_ohlc(pair: str, interval: int, out_csv: str | Path, timeout: int = 20) -> FetchResult:
    pair = pair.upper(); out = Path(out_csv); out.parent.mkdir(parents=True, exist_ok=True)
    try:
        q = f'{KRAKEN_OHLC}?pair={pair}&interval={int(interval)}'
        req = urllib.request.Request(q, headers={'User-Agent': 'ASTRA-Quant-Lab/1.5'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read())
        if payload.get('error'): raise RuntimeError('Kraken API error: ' + '; '.join(payload['error']))
        result = payload.get('result') or {}
        series = [v for k, v in result.items() if k != 'last']
        if not series: raise RuntimeError('Kraken returned no OHLC series')
        rows = series[0]
        with out.open('w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['timestamp','open','high','low','close','volume'])
            for row in rows:
                ts = datetime.fromtimestamp(float(row[0]), tz=timezone.utc).isoformat().replace('+00:00','Z')
                w.writerow([ts, row[1], row[2], row[3], row[4], row[6]])
        return FetchResult('SOURCE_FETCHED', 'kraken_public_ohlc', pair, str(interval), len(rows), str(out), _sha256(out), None)
    except Exception as e:
        return FetchResult('BLOCKED', 'kraken_public_ohlc', pair, str(interval), 0, None, None, repr(e))
