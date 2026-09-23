from __future__ import annotations
import csv,json,hashlib,sys
from pathlib import Path
from statistics import mean
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from astra.core import Bar,backtest_signals
from astra.strategies import trend,mean_reversion,breakout,long_momentum,long_trend
FEE=0.0005; SLIP=0.0002; TRAIN=300; TEST=100; STEP=100; EMBARGO=5
ASSETS=("BTCUSD","ETHUSD","SOLUSD","LTCUSD")
CANDIDATES=[]
for f in (4,6,8,10,12,16,20):
 for s in (24,32,40,52,64,80):
  if f<s: CANDIDATES.append(("trend",{"fast":f,"slow":s},trend,s))
for w in (10,15,20,30,40,60):
 for z in (0.5,1.0,1.5,2.0,3.0): CANDIDATES.append(("mean_reversion",{"window":w,"z":z},mean_reversion,w))
for w in (10,15,20,30,40,60,80): CANDIDATES.append(("breakout",{"window":w},breakout,w))
for w in (10,20,30,40,60,80,120):
 for threshold in (0.0,2.0,5.0,10.0): CANDIDATES.append(("long_momentum",{"window":w,"threshold":threshold},long_momentum,w))
for f in (10,20,30,40):
 for s in (50,80,120,160):
  if f<s: CANDIDATES.append(("long_trend",{"fast":f,"slow":s},long_trend,s))
def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
 return h.hexdigest()
def load(symbol):
 rows=list(csv.DictReader((ROOT/"data/real"/f"kraken_{symbol}_1d.csv").open(encoding="utf-8")))
 return [Bar(i,float(r["close"])) for i,r in enumerate(rows)]
def signal_for(bars,name,p):
 return {"trend":trend,"mean_reversion":mean_reversion,"breakout":breakout,"long_momentum":long_momentum,"long_trend":long_trend}[name](bars,**p)
def rank_train(data,start):
 rows=[]
 for name,p,_,_ in CANDIDATES:
  sub=[]
  for sym,bars in data.items():
   a=bars[start:start+150]; b=bars[start+150:start+TRAIN]
   ra=backtest_signals(a,signal_for(a,name,p),fee=FEE,slip=SLIP)
   rb=backtest_signals(b,signal_for(b,name,p),fee=FEE,slip=SLIP)
   agg=((1+ra["return_pct"]/100)*(1+rb["return_pct"]/100)-1)*100
   sub.append((ra["return_pct"],rb["return_pct"],max(ra["max_drawdown_pct"],rb["max_drawdown_pct"]),agg))
  total_trades=0
  for sym,bars in data.items():
   a=bars[start:start+150]; b=bars[start+150:start+TRAIN]
   total_trades += backtest_signals(a,signal_for(a,name,p),fee=FEE,slip=SLIP)["trades"] + backtest_signals(b,signal_for(b,name,p),fee=FEE,slip=SLIP)["trades"]
  if total_trades >= 8:
   rows.append((min(x for q in sub for x in q[:2]),-max(x[2] for x in sub),mean(x[3] for x in sub),name,p,total_trades))
 if not rows: raise RuntimeError("no active candidate met the training activity floor")
 return max(rows,key=lambda x:x[:3])
def run():
 data={s:load(s) for s in ASSETS}
 if min(len(v) for v in data.values())<TRAIN+EMBARGO+TEST: raise RuntimeError("insufficient aligned real data")
 folds=[]; start=0
 while start+TRAIN+EMBARGO+TEST<=min(len(v) for v in data.values()):
  selected=rank_train(data,start); name,p=selected[3],selected[4]
  asset_tests={}
  for sym,bars in data.items():
   test_start=start+TRAIN+EMBARGO; test_end=test_start+TEST
   lookback=max([int(v) for k,v in p.items() if k in ("fast","slow","window")] or [1])
   context_start=max(0,test_start-lookback)
   context=bars[context_start:test_end]; off=test_start-context_start
   asset_tests[sym]=backtest_signals(context[off:],signal_for(context,name,p)[off:],fee=FEE,slip=SLIP)
  folds.append({"fold":len(folds)+1,"train_start":start,"train_end":start+TRAIN-1,"test_start":start+TRAIN+EMBARGO,"test_end":start+TRAIN+EMBARGO+TEST-1,"selected":name,"params":p,"train_stability_score":selected[0],"train_max_dd":-selected[1],"train_mean_aggregate_return_pct":selected[2],"train_activity_trades":selected[5],"asset_tests":asset_tests})
  start+=STEP
 fold_returns=[mean(v["return_pct"] for v in f["asset_tests"].values()) for f in folds]
 all_asset_returns=[v["return_pct"] for f in folds for v in f["asset_tests"].values()]
 wealth=1.0
 for x in fold_returns: wealth*=1+x/100
 agg=(wealth-1)*100
 maxdd=max(v["max_drawdown_pct"] for f in folds for v in f["asset_tests"].values())
 positive=sum(x>0 for x in all_asset_returns)/len(all_asset_returns)
 ev={"status":"PROVEN_CROSS_ASSET_RESEARCH","dataset_sha256":{s:sha256(ROOT/"data/real"/f"kraken_{s}_1d.csv") for s in ASSETS},"rows":{s:len(v) for s,v in data.items()},"candidate_count":len(CANDIDATES),"folds":folds,"summary":{"folds":len(folds),"mean_asset_fold_return_pct":round(mean(fold_returns),4),"positive_asset_fold_ratio":round(positive,4),"aggregate_equal_weight_fold_return_pct":round(agg,4),"max_asset_drawdown_pct":round(maxdd,4),"passed_gate":agg>0 and positive>=0.5 and maxdd<=8.0},"cost":{"fee":FEE,"slip":SLIP},"profitability":"UNVERIFIED","live_money_execution":False}
 out=ROOT/"evidence/cross_asset_research_ci.json"; out.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(ev,indent=2))
if __name__=="__main__": run()
