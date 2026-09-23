from __future__ import annotations
import csv, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data/real"; EVIDENCE=ROOT/"evidence/real_data_ci.json"; MIN_ROWS=400
SOURCES=[
 ("Kraken public REST API","https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1440"),
 ("Coinbase Exchange public REST API","https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400"),
 ("Binance public spot REST API","https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=1000"),
]
def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def fetch(source,url):
    with urlopen(Request(url,headers={"User-Agent":"ASTRA-REAL-DATA/1.1","Accept":"application/json"}),timeout=30) as resp:
        if getattr(resp,"status",None)!=200: raise RuntimeError(f"HTTP status {getattr(resp,'status',None)}")
        payload=json.loads(resp.read())
    rows=[]
    if "Kraken" in source:
        if payload.get("error"): raise RuntimeError(f"provider error: {payload['error']}")
        result=payload.get("result",{}); key=next((k for k in result if k!="last"),None)
        if not key: raise RuntimeError("Kraken returned no OHLC series")
        for x in result[key]:
            rows.append([int(float(x[0]))*1000,str(x[1]),str(x[2]),str(x[3]),str(x[4]),str(x[6])])
    elif "Coinbase" in source:
        for x in payload: rows.append([int(x[0])*1000,str(x[3]),str(x[2]),str(x[1]),str(x[4]),str(x[5])])
    else:
        rows=payload
    return rows
def main():
    retrieved=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"); OUT.mkdir(parents=True,exist_ok=True); EVIDENCE.parent.mkdir(parents=True,exist_ok=True)
    errors=[]
    for source,url in SOURCES:
        try:
            rows=fetch(source,url)
            if len(rows)<MIN_ROWS: raise RuntimeError(f"research scale not met: {len(rows)} < {MIN_ROWS}")
            raw_path=OUT/f"{source.split()[0].lower()}_BTCUSD_1d.json"; csv_path=OUT/f"{source.split()[0].lower()}_BTCUSD_1d.csv"
            raw_path.write_text(json.dumps(rows,separators=(",",":")),encoding="utf-8")
            with csv_path.open("w",newline="",encoding="utf-8") as f:
                w=csv.writer(f); w.writerow(["timestamp","open","high","low","close","volume"])
                for x in sorted(rows,key=lambda z:int(z[0])):
                    ts=datetime.fromtimestamp(int(x[0])/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"); w.writerow([ts,x[1],x[2],x[3],x[4],x[5]])
            with csv_path.open(encoding="utf-8") as f: parsed=list(csv.DictReader(f))
            ts=[r["timestamp"] for r in parsed]
            if ts!=sorted(ts) or len(set(ts))!=len(ts): raise RuntimeError("timestamp integrity failure")
            for r in parsed:
                o,h,l,c,v=map(float,(r["open"],r["high"],r["low"],r["close"],r["volume"]))
                if not (l<=min(o,c)<=max(o,c)<=h) or v<0: raise RuntimeError("OHLCV integrity failure")
            ev={"status":"PROVEN","source":source,"source_url":url,"retrieved_at":retrieved,"symbol":"BTC/USD","timeframe":"1d","rows":len(parsed),"start":ts[0],"end":ts[-1],"raw_sha256":sha256(raw_path),"dataset_sha256":sha256(csv_path),"source_access":True,"successful_retrieval":True,"source_verified":True,"non_empty":True,"research_scale":True,"provenance":True,"local_validation":True,"persisted_evidence":True,"synthetic":False,"mock":False,"fixture":False,"fallback_attempts":errors,"profitability":"UNVERIFIED","live_money_execution":False}
            EVIDENCE.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(ev,indent=2)); return
        except Exception as exc:
            errors.append({"source":source,"url":url,"error":f"{type(exc).__name__}: {exc}"})
    ev={"status":"BLOCKED","sources":errors,"retrieved_at":retrieved,"real_data":False,"profitability":"UNVERIFIED","live_money_execution":False}
    EVIDENCE.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(ev,indent=2)); sys.exit(1)
if __name__=="__main__": main()
