from __future__ import annotations
import csv,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from astra.core import Bar,backtest,adversary
from astra.research import Experiment,walk_forward,cost_stress
DATA=ROOT/"data/real/kraken_BTCUSD_1d.csv"; OUT=ROOT/"evidence/real_data_research_ci.json"
def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
 return h.hexdigest()
def main():
 with DATA.open(encoding="utf-8") as f: rows=list(csv.DictReader(f))
 bars=[Bar(i,float(r["close"])) for i,r in enumerate(rows)]
 base=backtest(bars); adv=adversary(bars); wf=walk_forward(bars,Experiment(12,40,300,100,100)); costs=cost_stress(bars,12,40)
 ev={"status":"PROVEN_RESEARCH_RUN","dataset_sha256":sha256(DATA),"rows":len(bars),"source":"Kraken public REST API","dataset_synthetic":False,"baseline":base,"adversary":adv,"walk_forward":{"folds":wf.folds,"test_returns":wf.test_returns,"mean_return_pct":wf.mean_return_pct,"positive_fold_ratio":wf.positive_fold_ratio,"max_drawdown_pct":wf.max_drawdown_pct,"aggregate_return_pct":wf.aggregate_return_pct,"passed_gate":wf.passed},"cost_stress":costs,"profitability":"UNVERIFIED","live_money_execution":False}
 OUT.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(ev,indent=2))
if __name__=="__main__": main()
