from __future__ import annotations
import csv, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data/real"; EVIDENCE=ROOT/"evidence/real_data_ci.json"
URL="https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=1000"; MIN_ROWS=400
def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def main():
    retrieved=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"); OUT.mkdir(parents=True,exist_ok=True); EVIDENCE.parent.mkdir(parents=True,exist_ok=True)
    raw_path=OUT/"binance_BTCUSDT_1d.json"; csv_path=OUT/"binance_BTCUSDT_1d.csv"
    try:
        with urlopen(Request(URL,headers={"User-Agent":"ASTRA-REAL-DATA/1.0","Accept":"application/json"}),timeout=30) as resp:
            if getattr(resp,"status",None)!=200: raise RuntimeError(f"HTTP status {getattr(resp,'status',None)}")
            body=resp.read()
        rows=json.loads(body)
        if not isinstance(rows,list) or not rows or not all(isinstance(x,list) and len(x)>=6 for x in rows): raise RuntimeError("unexpected/empty Binance kline response")
        raw_path.write_bytes(body)
        with csv_path.open("w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["timestamp","open","high","low","close","volume"])
            for x in rows:
                ts=datetime.fromtimestamp(int(x[0])/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"); w.writerow([ts,x[1],x[2],x[3],x[4],x[5]])
        with csv_path.open(encoding="utf-8") as f: parsed=list(csv.DictReader(f))
        if len(parsed)<MIN_ROWS: raise RuntimeError(f"research scale not met: {len(parsed)} < {MIN_ROWS}")
        ts=[r["timestamp"] for r in parsed]
        if ts!=sorted(ts) or len(set(ts))!=len(ts): raise RuntimeError("timestamp integrity failure")
        for r in parsed:
            o,h,l,c,v=map(float,(r["open"],r["high"],r["low"],r["close"],r["volume"]))
            if not (l<=min(o,c)<=max(o,c)<=h) or v<0: raise RuntimeError("OHLCV integrity failure")
        ev={"status":"PROVEN","source":"Binance public spot REST API","source_url":URL,"retrieved_at":retrieved,"symbol":"BTCUSDT","timeframe":"1d","rows":len(parsed),"start":ts[0],"end":ts[-1],"raw_sha256":sha256(raw_path),"dataset_sha256":sha256(csv_path),"source_access":True,"successful_retrieval":True,"source_verified":True,"non_empty":True,"research_scale":True,"provenance":True,"local_validation":True,"persisted_evidence":True,"synthetic":False,"mock":False,"fixture":False,"profitability":"UNVERIFIED","live_money_execution":False}
        EVIDENCE.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(ev,indent=2))
    except Exception as exc:
        ev={"status":"BLOCKED","source":"Binance public spot REST API","source_url":URL,"retrieved_at":retrieved,"error":f"{type(exc).__name__}: {exc}","real_data":False,"profitability":"UNVERIFIED","live_money_execution":False}
        EVIDENCE.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(ev,indent=2)); sys.exit(1)
if __name__=="__main__": main()
