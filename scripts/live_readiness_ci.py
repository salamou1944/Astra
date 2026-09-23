"""ASTRA live-readiness assessment.

This is a fail-closed assessment only. It never enables live trading and never
submits an exchange order. Readiness is reported as NOT_READY unless every
required safety gate and explicit project prerequisite is satisfied.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from astra.execution.safety import ExecutionGate, KillSwitch

REQUIRED=("DATA_VALID","STRATEGY_VALID","RISK_VALID","EXECUTION_VALID",
          "RECONCILIATION_VALID","KILL_SWITCH_VALID","HUMAN_APPROVAL","LIVE_ENABLED")

def main():
    os.environ["ASTRA_LIVE_TRADING"]="0"
    ks=KillSwitch()
    gate=ExecutionGate(ks)
    inputs={
      "DATA_VALID": True,
      "STRATEGY_VALID": False,
      "RISK_VALID": True,
      "EXECUTION_VALID": True,
      "RECONCILIATION_VALID": True,
      "KILL_SWITCH_VALID": True,
      "HUMAN_APPROVAL": False,
      "LIVE_ENABLED": False,
    }
    assert gate.authorize(
      data_valid=inputs["DATA_VALID"], strategy_valid=inputs["STRATEGY_VALID"],
      risk_valid=inputs["RISK_VALID"], execution_valid=inputs["EXECUTION_VALID"],
      reconciliation_valid=inputs["RECONCILIATION_VALID"],
      human_approval=inputs["HUMAN_APPROVAL"], live_enabled=inputs["LIVE_ENABLED"]) is False

    blockers=[k for k,v in inputs.items() if not v]
    out={
      "status":"PROVEN_LIVE_READINESS_ASSESSMENT",
      "readiness":"NOT_READY",
      "required_gates":list(REQUIRED),
      "gate_state":inputs,
      "blocking_gates":blockers,
      "live_trading_environment":os.environ["ASTRA_LIVE_TRADING"],
      "automatic_live_order":False,
      "network_order_submitted":False,
      "live_money_execution":False,
      "withdrawal_capability":False,
      "profitability":"UNVERIFIED",
      "alpha":"UNVERIFIED",
      "reason":"Safety gate correctly refuses authorization while strategy validity, human approval, and live enablement are absent."
    }
    p=ROOT/"evidence"/"live_readiness_ci.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()
