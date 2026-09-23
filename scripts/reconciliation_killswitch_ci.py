"""Paper-only reconciliation fault injection and kill-switch evidence."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from astra.execution.paper import PaperBroker
from astra.execution.safety import ExecutionGate, KillSwitch, HaltReason, reconcile_and_trip

ROOT = Path(__file__).resolve().parents[1]
cases = [
    ("missing_exchange_order", {"local_orders":{"o1":{"status":"open"}}, "exchange_orders":{}}),
    ("unknown_exchange_order", {"local_orders":{}, "exchange_orders":{"o2":{"status":"open"}}}),
    ("position_mismatch", {"local_orders":{}, "exchange_orders":{}, "local_positions":{"BTC":"1"}, "exchange_positions":{"BTC":"0"}}),
    ("balance_mismatch", {"local_orders":{}, "exchange_orders":{}, "local_balances":{"USD":"100"}, "exchange_balances":{"USD":"99"}}),
    ("partial_fill_mismatch", {"local_orders":{"o3":{"status":"partially_filled","filled":"0.5","remaining":"0.5"}}, "exchange_orders":{"o3":{"status":"filled","filled":"1","remaining":"0"}}}),
]
base = dict(local_orders={}, exchange_orders={}, local_positions={"BTC":"0"}, exchange_positions={"BTC":"0"}, local_balances={"USD":"100"}, exchange_balances={"USD":"100"})
results=[]
for name, delta in cases:
    args=dict(base)
    args.update(delta)
    ks=KillSwitch()
    result=reconcile_and_trip(kill_switch=ks, **args)
    gate=ExecutionGate(ks)
    authorized=gate.authorize(data_valid=True,strategy_valid=True,risk_valid=True,execution_valid=True,reconciliation_valid=result.ok,human_approval=True,live_enabled=True)
    results.append({"case":name,"ok":result.ok,"mismatches":list(result.mismatches),"kill_halted":ks.halted,"kill_reason":ks.reason,"gate_authorized":authorized})
    assert not result.ok and ks.halted and ks.reason == HaltReason.RECONCILIATION.value and not authorized

clean_ks=KillSwitch()
clean=reconcile_and_trip(kill_switch=clean_ks, **base)
assert clean.ok and not clean_ks.halted
paper=PaperBroker()
paper.submit(symbol="BTCUSD", side="buy", quantity="1")
changed=paper.advance(symbol="BTCUSD", market_price="100")
assert len(changed)==1 and paper.positions["BTCUSD"] == 1
assert all(r["gate_authorized"] is False for r in results)
payload={"status":"PROVEN_RECONCILIATION_KILL_SWITCH","cases":results,"clean_reconciliation_ok":clean.ok,"paper_orders_submitted":1,"exchange_orders_submitted":0,"live_money_execution":False,"withdrawal_capability":False}
payload["sha256"]=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
out=ROOT/"evidence/reconciliation_killswitch_ci.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
print(json.dumps(payload,indent=2))
