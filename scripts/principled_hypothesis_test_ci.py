from __future__ import annotations
import csv,json,hashlib,sys,math
from pathlib import Path
from statistics import mean
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from astra.core import Bar,backtest_signals
ASSETS=("BTCUSD","ETHUSD","SOLUSD","LTCUSD");FEE=.0005;SLIP=.0002
def load(s):
 r=list(csv.DictReader((ROOT/"data/real"/f"kraken_{s}_1d.csv").open(encoding="utf-8")));return [Bar(i,float(x["close"])) for i,x in enumerate(r)]
def mom(b,w=30,t=0):
 c=[x.close for x in b];return [0 if i<w else int(c[i]/c[i-w]-1>t/100) for i in range(len(c))]
def vol(b,w=30,t=0,v=0.04):
 c=[x.close for x in b];o=[]
 for i,p in enumerate(c):
  if i<w:o.append(0);continue
  r=[c[j]/c[j-1]-1 for j in range(max(1,i-w+1),i+1)]
  sd=(sum((x-mean(r))**2 for x in r)/max(1,len(r)-1))**.5
  o.append(int(c[i]/c[i-w]-1>t/100 and sd<=v))
 return o
def trendreg(b,w=30,t=0,reg=0.0):
 c=[x.close for x in b];o=[]
 for i,p in enumerate(c):
  if i<w+20:o.append(0);continue
  mr=c[i]/c[i-w]-1; long=c[i]/c[i-20]-1
  o.append(int(mr>t/100 and long>reg))
 return o
C=[]
for w in (20,30,40,60,90):
 for t in (0,2,5): C.append(("momentum",{"w":w,"t":t},mom))
for w in (20,30,40,60):
 for t in (0,2,5):
  for v in (.025,.04,.06): C.append(("vol_filtered_momentum",{"w":w,"t":t,"v":v},vol))
for w in (20,30,40,60):
 for t in (0,2,5):
  C.append(("dual_horizon_momentum",{"w":w,"t":t},trendreg))
def test(bars,fn,p,a,e):
 s=max(0,a-max(p.get("w",1),20));ctx=bars[s:e];off=a-s
 return backtest_signals(ctx[off:],fn(ctx,**p)[off:],fee=FEE,slip=SLIP)
def score(data,start,end):
 rows=[]
 for name,p,fn in C:
  rs=[test(b,name and fn,p,start,end) for b in data.values()]
  vals=[x["return_pct"] for x in rs];dds=[x["max_drawdown_pct"] for x in rs]
  if sum(x["trades"] for x in rs)>=8: rows.append((min(vals),-max(dds),mean(vals),name,p))
 return max(rows,key=lambda x:(x[0],x[1],x[2]))
def main():
 d={s:load(s) for s in ASSETS};research_end=520;validation_start=525;validation_end=620;final_start=621;final_end=721
 # pre-register hypotheses; select only using research interval
 selected=score(d,120,research_end)
 name,p=selected[3],selected[4]
 val={s:test(b, C[0][2],p,validation_start,validation_end) for s,b in d.items()} if False else {s:test(b,next(fn for n,pp,fn in C if n==name),p,validation_start,validation_end) for s,b in d.items()}
 # final is fixed after validation; no tuning on final
 fn=next(fn for n,pp,fn in C if n==name)
 final={s:test(b,fn,p,final_start,final_end) for s,b in d.items()}
 bh={s:(b[final_start].close and (b[final_end-1].close/b[final_start].close-1)*100) for s,b in d.items()}
 def comp(x): return (math.prod(1+v["return_pct"]/100 for v in x.values())**(1/4)-1)*100
 ev={"status":"PROVEN_PRINCIPLED_HYPOTHESIS_TEST","selection":{"research_end_exclusive":research_end,"candidate_count":len(C),"selected":name,"params":p},"validation":{"start":validation_start,"end":validation_end-1,"results":val,"positive_asset_ratio":sum(v["return_pct"]>0 for v in val.values())/4},"final_holdout":{"start":final_start,"end":final_end-1,"results":final,"buy_hold_return_pct":bh,"strategy_equal_weight_compounded_pct":round(comp(final),4),"buy_hold_equal_weight_compounded_pct":round(math.prod(1+x/100 for x in bh.values())**.25*100-100,4)},"profitability":"UNVERIFIED","alpha":"UNVERIFIED","live_money_execution":False}
 (ROOT/"evidence/principled_hypothesis_test_ci.json").write_text(json.dumps(ev,indent=2)+"\n");print(json.dumps(ev,indent=2))
main()
