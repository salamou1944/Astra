from __future__ import annotations
import csv,json,hashlib
from pathlib import Path
from statistics import mean
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from astra.core import Bar,backtest_signals,backtest
from astra.strategies import trend,mean_reversion,breakout,long_momentum

DATA=ROOT/"data/real/kraken_BTCUSD_1d.csv"
OUT=ROOT/"evidence/real_data_candidate_research_ci.json"
FEE=0.0005
SLIP=0.0002
TRAIN=300
TEST=100
STEP=100
EMBARGO=5

def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
 return h.hexdigest()

CANDIDATES=[]
for f in (4,6,8,10,12,16,20):
 for s in (24,32,40,52,64,80):
  if f<s: CANDIDATES.append(("trend",{"fast":f,"slow":s},trend,s))
for w in (10,15,20,30,40,60):
 for z in (0.5,1.0,1.5,2.0,3.0):
  CANDIDATES.append(("mean_reversion",{"window":w,"z":z},mean_reversion,w))
for w in (10,15,20,30,40,60,80):
 CANDIDATES.append(("breakout",{"window":w},breakout,w))
for w in (10,20,30,40,60,80,120):
 for threshold in (0.0,2.0,5.0,10.0):
  CANDIDATES.append(("long_momentum",{"window":w,"threshold":threshold},long_momentum,w))

def signal_for(bars,name,params):
 return {"trend":trend,"mean_reversion":mean_reversion,"breakout":breakout,"long_momentum":long_momentum}[name](bars,**params)

def rank_train(bars):
 rows=[]
 mid=len(bars)//2
 a=bars[:mid]; b=bars[mid:]
 for name,p,_,_ in CANDIDATES:
  ra=backtest_signals(a,signal_for(a,name,p),fee=FEE,slip=SLIP)
  rb=backtest_signals(b,signal_for(b,name,p),fee=FEE,slip=SLIP)
  # Stability-first selection: reward consistency across two chronological
  # subwindows, then drawdown control, then aggregate return. Test data is untouched.
  wealth=(1+ra["return_pct"]/100)*(1+rb["return_pct"]/100)
  aggregate=(wealth-1)*100
  score=min(ra["return_pct"],rb["return_pct"])
  dd=max(ra["max_drawdown_pct"],rb["max_drawdown_pct"])
  rows.append((score,-dd,aggregate,-(ra["trades"]+rb["trades"]),name,p,{"return_pct":round(aggregate,4),"max_drawdown_pct":dd,"trades":ra["trades"]+rb["trades"]}))
 return max(rows,key=lambda x:x[:4])

def run():
 rows=list(csv.DictReader(DATA.open(encoding="utf-8")))
 bars=[Bar(i,float(r["close"])) for i,r in enumerate(rows)]
 folds=[]; start=0
 while start+TRAIN+EMBARGO+TEST<=len(bars):
  train_end=start+TRAIN; test_start=train_end+EMBARGO; test_end=test_start+TEST
  selected=rank_train(bars[start:train_end])
  name,p=selected[3],selected[4]
  # Context supplies indicator history without allowing any post-test observations.
  context_start=max(0,test_start-int(selected[2]))
  context=bars[context_start:test_end]
  sig=signal_for(context,name,p)
  off=test_start-context_start
  test=backtest_signals(context[off:],sig[off:],fee=FEE,slip=SLIP)
  folds.append({"fold":len(folds)+1,"train_start":start,"train_end":train_end-1,
                "test_start":test_start,"test_end":test_end-1,"selected":name,
                "params":p,"train_score_return_pct":selected[5]["return_pct"],
                "test":test})
  start+=STEP
 returns=[f["test"]["return_pct"] for f in folds]
 dds=[f["test"]["max_drawdown_pct"] for f in folds]
 wealth=1.0
 for x in returns: wealth*=1+x/100
 aggregate=(wealth-1)*100
 result={"status":"PROVEN_CANDIDATE_RESEARCH","dataset_sha256":sha256(DATA),"rows":len(bars),
         "candidate_count":len(CANDIDATES),"folds":folds,
         "summary":{"folds":len(folds),"test_returns":returns,"mean_return_pct":round(mean(returns),4),
                    "positive_fold_ratio":round(sum(x>0 for x in returns)/len(returns),4),
                    "max_drawdown_pct":round(max(dds),4),"aggregate_return_pct":round(aggregate,4),
                    "passed_gate":aggregate>0 and sum(x>0 for x in returns)/len(returns)>=0.5 and max(dds)<=8.0},
         "cost":{"fee":FEE,"slip":SLIP},"profitability":"UNVERIFIED","live_money_execution":False}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2))
if __name__=="__main__": run()
