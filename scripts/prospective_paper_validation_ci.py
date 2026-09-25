from __future__ import annotations
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"evidence/prospective_paper_validation_ci.json"
ASSETS=("BTCUSD","ETHUSD","SOLUSD","LTCUSD")
MIN_FORWARD_BARS=30
FEE=.0005
SLIP=.0002
HOLDOUT_END_TIMESTAMP="2026-09-23T00:00:00Z"
HOLDOUT_END_TS=int(datetime.fromisoformat(HOLDOUT_END_TIMESTAMP.replace("Z","+00:00")).timestamp())
WINDOW=30
THRESHOLD=0.0

def fetch(pair):
    # Kraken's OHLC endpoint is bounded to recent candles. Do not use a fixed
    # row index against the current response: that can silently keep the
    # prospective sample at zero forever. Fetch from the fixed holdout boundary
    # and retain WINDOW bars of context before measuring post-holdout bars.
    since=max(0,HOLDOUT_END_TS-WINDOW*86400)
    url=f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=1440&since={since}"
    with urlopen(Request(url,headers={"User-Agent":"ASTRA-PROSPECTIVE-PAPER/1.1","Accept":"application/json"}),timeout=30) as r:
        if getattr(r,"status",None)!=200: raise RuntimeError(f"HTTP {getattr(r,'status',None)}")
        p=json.loads(r.read())
    if p.get("error"): raise RuntimeError(f"Kraken error: {p['error']}")
    result=p.get("result",{})
    key=next((k for k in result if k!="last"),None)
    if not key: raise RuntimeError("no OHLC series")
    return sorted(result[key],key=lambda x:int(float(x[0])))

def sha(rows):
    return hashlib.sha256(json.dumps(rows,separators=(",",":"),sort_keys=False).encode()).hexdigest()

def strategy_returns(rows, start):
    closes=[float(x[4]) for x in rows]
    sig=[]
    for i,p in enumerate(closes):
        if i<WINDOW: sig.append(0); continue
        sig.append(int(p/closes[i-WINDOW]-1>THRESHOLD/100))
    eq=1.0; peak=1.0; dd=0.0; trades=0; prev=0
    for i in range(max(start,WINDOW+1),len(rows)):
        s=sig[i-1]
        if s!=prev: trades+=1; prev=s
        r=closes[i]/closes[i-1]-1
        if s: r-=FEE+SLIP
        eq*=1+r
        peak=max(peak,eq); dd=max(dd,1-eq/peak)
    return {"return_pct":(eq-1)*100,"max_drawdown_pct":dd*100,"trades":trades}

def main():
    retrieved=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    results={}; errors=[]
    for pair in ASSETS:
        try:
            rows=fetch(pair)
            timestamps=[int(float(x[0])) for x in rows]
            forward_indices=[i for i,ts in enumerate(timestamps) if ts>HOLDOUT_END_TS]
            forward=len(forward_indices)
            first_forward=min(forward_indices) if forward else None
            item={
                "rows_retrieved":len(rows),
                "forward_bars_after_holdout":forward,
                "first_forward_timestamp":(
                    datetime.fromtimestamp(timestamps[first_forward],tz=timezone.utc).isoformat().replace("+00:00","Z")
                    if first_forward is not None else None
                ),
                "last_timestamp":(
                    datetime.fromtimestamp(timestamps[-1],tz=timezone.utc).isoformat().replace("+00:00","Z")
                    if timestamps else None
                ),
                "dataset_sha256":sha(rows)
            }
            item["performance"]=strategy_returns(rows,first_forward) if forward else None
            item["sufficient_forward_sample"]=forward>=MIN_FORWARD_BARS
            results[pair]=item
        except Exception as e:
            errors.append({"asset":pair,"error":f"{type(e).__name__}: {e}"})
    sufficient=not errors and all(x["sufficient_forward_sample"] for x in results.values())
    status="PROVEN_PROSPECTIVE_PAPER_VALIDATION" if sufficient else "INSUFFICIENT_FORWARD_SAMPLE"
    ev={
      "status":status,
      "retrieved_at":retrieved,
      "source":"Kraken public REST API",
      "method":"fixed prospective paper evaluation after untouched holdout",
      "fixed_strategy":{"name":"long_momentum","window":WINDOW,"threshold":THRESHOLD},
      "costs":{"fee":FEE,"slippage":SLIP},
      "holdout_end_timestamp":HOLDOUT_END_TIMESTAMP,
      "minimum_forward_bars":MIN_FORWARD_BARS,
      "assets":results,
      "errors":errors,
      "selection_touched_forward_data":False,
      "live_money_execution":False,
      "automatic_live_orders":False,
      "profitability":"UNVERIFIED",
      "alpha":"UNVERIFIED",
      "next_transition":"require >=30 post-holdout daily bars per asset before treating prospective sample as evidence"
    }
    EVIDENCE.parent.mkdir(parents=True,exist_ok=True)
    EVIDENCE.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(ev,indent=2))
if __name__=="__main__": main()
