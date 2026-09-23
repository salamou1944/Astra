from __future__ import annotations
import csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data/real"; EVIDENCE=ROOT/"evidence/multi_asset_real_data_ci.json"
ASSETS={"BTCUSD":"XBTUSD","ETHUSD":"ETHUSD","SOLUSD":"SOLUSD","LTCUSD":"LTCUSD"}; MIN_ROWS=400
def sha256(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
 return h.hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True); EVIDENCE.parent.mkdir(parents=True,exist_ok=True); retrieved=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"); results=[]; errors=[]
 for symbol,pair in ASSETS.items():
  url=f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=1440"
  try:
   with urlopen(Request(url,headers={"User-Agent":"ASTRA-MULTI-REAL-DATA/1.0","Accept":"application/json"}),timeout=30) as resp:
    if getattr(resp,"status",None)!=200: raise RuntimeError(f"HTTP status {getattr(resp,'status',None)}")
    payload=json.loads(resp.read())
   if payload.get("error"): raise RuntimeError(f"provider error: {payload['error']}")
   result=payload.get("result",{}); key=next((k for k in result if k!="last"),None)
   if not key: raise RuntimeError("Kraken returned no OHLC series")
   rows=result[key]
   if len(rows)<MIN_ROWS: raise RuntimeError(f"scale {len(rows)} < {MIN_ROWS}")
   path=OUT/f"kraken_{symbol}_1d.csv"
   with path.open("w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["timestamp","open","high","low","close","volume"])
    for x in sorted(rows,key=lambda z:int(z[0])):
     ts=datetime.fromtimestamp(int(x[0]),tz=timezone.utc).isoformat().replace("+00:00","Z")
     w.writerow([ts,x[1],x[2],x[3],x[4],x[6]])
   parsed=list(csv.DictReader(path.open(encoding="utf-8"))); ts=[r["timestamp"] for r in parsed]
   if ts!=sorted(ts) or len(set(ts))!=len(ts): raise RuntimeError("timestamp integrity failure")
   for r in parsed:
    o,h,l,c,v=map(float,(r["open"],r["high"],r["low"],r["close"],r["volume"]))
    if not(l<=min(o,c)<=max(o,c)<=h) or v<0: raise RuntimeError("OHLCV integrity failure")
   results.append({"symbol":symbol,"source":"Kraken public REST API","source_url":url,"rows":len(parsed),"start":ts[0],"end":ts[-1],"dataset_sha256":sha256(path),"source_access":True,"successful_retrieval":True,"source_verified":True,"provenance":True,"local_validation":True,"synthetic":False,"mock":False,"fixture":False})
  except Exception as e: errors.append({"symbol":symbol,"source_url":url,"error":f"{type(e).__name__}: {e}"})
 status="PROVEN" if len(results)==len(ASSETS) else "PARTIAL"
 ev={"status":status,"retrieved_at":retrieved,"assets":results,"errors":errors,"asset_count":len(results),"requested_assets":len(ASSETS),"all_assets_verified":len(results)==len(ASSETS),"profitability":"UNVERIFIED","live_money_execution":False}
 EVIDENCE.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(ev,indent=2))
 if len(results)<2: raise SystemExit(1)
if __name__=="__main__": main()
