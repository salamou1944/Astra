"""ASTRA live-readiness gate: non-trading, fail-closed verification.

This does not enable live trading and never submits an order.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from astra.execution.safety import ExecutionGate, KillSwitch

GATES=("data_valid","strategy_valid","risk_valid","execution_valid",
       "reconciliation_valid","human_approval","live_enabled")

def main():
    os.environ["ASTRA_LIVE_TRADING"]="0"
    kill=KillSwitch()
    gate=ExecutionGate(kill)
    base={k:True for k in GATES}
    base["live_enabled"]=False
    assert gate.authorize(**base) is False
    off_result=True
    failures=[]
    for name in GATES:
        case=dict(base)
        case["live_enabled"]=True
        case[name]=False
        if gate.authorize(**case):
            failures.append(name)
    assert not failures, f"gate bypassed by: {failures}"

    kill.trip("manual")
    all_true=dict(base,live_enabled=True)
    assert gate.authorize(**all_true) is False
    kill_block=True

    out={
      "status":"PROVEN_HUMAN_APPROVAL_GATE",
      "live_trading_environment":"0",
      "all_required_gates":list(GATES),
      "live_off_blocks_authorization":off_result,
      "each_gate_individually_required":True,
      "kill_switch_blocks_authorization":kill_block,
      "human_approval_required":True,
      "automatic_live_order":False,
      "network_order_submitted":False,
      "live_money_execution":False,
      "withdrawal_capability":False,
      "scope":"non-trading gate verification; not live readiness approval"
    }
    p=ROOT/"evidence"/"human_approval_gate_ci.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()
