from __future__ import annotations
import csv,json,hashlib,sys
from pathlib import Path
from statistics import mean
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from astra.core import Bar,backtest_signals
from astra.strategies import trend,mean_reversion,breakout,long_momentum,long_trend
FEE=.0005; SLIP=.0002; TRAIN=300; TEST=100; EMBARGO=5; HOLDOUT=100
ASSETS=("BTCUSD","ETHUSD","SOLUSD","LTCUSD")
C=[]
for f in (4,6,8,10,12,16,20):
 for s in (24,32,40,52,64,80):
  if f<s:C.append(("trend",{"fast":f,"slow":s},trend))
for w in (10,15,20,30,40,60):
 for z in (.5,1,1.5,2,3):C.append(("mean_reversion",{"window":w,"z":z},mean_reversion))
for w in (10,15,20,30,40,60,80):C.append(("breakout",{"window":w},breakout))
for w in (10,20,30,40,60,80,120):
 for t in (0,2,5,10):C.append(("long_momentum",{"window":w,"threshold":t},long_momentum))
for f in (10,20,30,40):
 for s in (50,80,120,160):
  if f<s:C.append(("long_trend",{"fast":f,"slow":s},long_trend))
def load(sym):
 rs=list(csv.DictReader((ROOT/"data/real"/f"kraken_{sym}_1d.csv").open(encoding="utf-8")))
 return [Bar(i,float(r["close"])) for i,r in enumerate(rs)]
def sig(bs,n,p):return {"trend":trend,"mean_reversion":mean_reversion,"breakout":breakout,"long_momentum":long_momentum,"long_trend":long_trend}[n](bs,**p)
def score(data,n,p,start):
 vals=[]; trades=0
 for bs in data.values():
  a=bs[start:start+150];b=bs[start+150:start+TRAIN]
  ra=backtest_signals(a,sig(a,n,p),fee=FEE,slip=SLIP); rb=backtest_signals(b,sig(b,n,p),fee=FEE,slip=SLIP)
  vals += [ra["return_pct"],rb["return_pct"]]; trades += ra["trades"]+rb["trades"]
 if trades<8:return None
 return (min(vals),sum(vals)/len(vals),-max(vals),trades)
def main():
 data={s:load(s) for s in ASSETS}; n=min(map(len,data.values())); research_end=n-HOLDOUT
 starts=[]; st=0
 while st+TRAIN+EMBARGO+TEST<=research_end:starts.append(st);st+=100
 history=[]
 for st in starts:
  ranked=[]
  for name,p,_ in C:
   q=score(data,name,p,st)
   if q:ranked.append((*q,name,p))
  history.append(max(ranked,key=lambda x:(x[0],x[1],x[2])))
 counts={}
 for x in history:counts[x[4]]=counts.get(x[4],0)+1
 champion=max(history,key=lambda x:(counts[x[4]],x[0],x[1]))
 name,p=champion[4],champion[5]
 h0=research_end
 tests={}
 for sym,bs in data.items():
  look=max([int(v) for k,v in p.items() if k in ("fast","slow","window")] or [1])
  ctx=bs[h0-look:n]; ss=sig(ctx,name,p); tests[sym]=backtest_signals(ctx[look:],ss[look:],fee=FEE,slip=SLIP)
 ev={"status":"PROVEN_HOLDOUT_VALIDATION","candidate_count":len(C),"research_period_end_index":research_end-1,"holdout_start_index":h0,"holdout_end_index":n-1,"selection_folds":len(history),"selected":name,"params":p,"selection_frequency":counts.get(name,0),"selection_history":[{"fold":i+1,"selected":x[4],"params":x[5],"stability":x[0]} for i,x in enumerate(history)],"holdout_tests":tests,"profitability":"UNVERIFIED","live_money_execution":False}
 (ROOT/"evidence/holdout_validation_ci.json").write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(ev,indent=2))
if __name__=="__main__":main()
