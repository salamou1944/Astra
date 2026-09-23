from __future__ import annotations
import csv,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from astra.core import Bar,signals
from astra.risk import RiskGuardian,RiskLimits
DATA=ROOT/"data/real/kraken_BTCUSD_1d.csv"; OUT=ROOT/"evidence/real_data_risk_shadow_ci.json"
def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
 return h.hexdigest()
def main():
 with DATA.open(encoding="utf-8") as f: rows=list(csv.DictReader(f))
 bars=[Bar(i,float(r["close"])) for i,r in enumerate(rows)]; sig=signals(bars,12,40)
 g=RiskGuardian(RiskLimits(max_position=1.0,max_daily_loss=0.02,max_drawdown=0.08))
 equity=1.0; peak=1.0; halted_at=None; authorized=[]
 for i,b in enumerate(bars):
  if i: equity*=1.0 + authorized[-1]*(b.close/bars[i-1].close-1.0)
  obs=g.observe(equity)
  if obs["halted"] and halted_at is None: halted_at={"bar":i,"equity":equity,"reason":obs["reason"]}
  authorized.append(g.authorize(sig[i]))
 ev={"status":"PROVEN_RISK_SHADOW_RUN","dataset_sha256":sha256(DATA),"rows":len(bars),"risk_limits":{"max_position":1.0,"max_daily_loss":0.02,"max_drawdown":0.08},"final_equity":equity,"halted":g.halted,"halted_at":halted_at,"hypothetical_orders":sum(1 for i in range(1,len(authorized)) if authorized[i]!=authorized[i-1]),"live_money_execution":False,"broker_orders_submitted":0,"profitability":"UNVERIFIED"}
 OUT.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(ev,indent=2))
if __name__=="__main__": main()
