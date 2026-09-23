"""Non-trading execution preflight.

This check proves only safety invariants that can be established without
exchange credentials or sending network orders. It must remain safe to run in
CI and on developer machines.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import json
import os
from pathlib import Path

from astra.execution.kraken import KrakenExecutionConfig, KrakenExecutionError, KrakenSpotExecutor

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    # CI must prove the safe default even if a developer shell happens to have
    # unrelated credentials configured.
    os.environ.pop("ASTRA_LIVE_TRADING", None)
    cfg = KrakenExecutionConfig.from_env()

    assert cfg.live_enabled is False, "preflight must start with live trading OFF"
    ex = KrakenSpotExecutor(cfg)

    order = ex.build_add_order(
        pair="XBTUSD", side="buy", ordertype="market", volume="0.0001"
    )
    dry = ex.submit_if_authorized(**order)
    assert dry["submitted"] is False
    assert dry["mode"] == "OFF"

    # Private authenticated calls must be impossible while OFF.
    try:
        ex.query_open_orders()
    except KrakenExecutionError as exc:
        assert "OFF" in str(exc)
    else:
        raise AssertionError("private API call escaped the OFF gate")

    # Architectural invariant: no withdrawal method exists on the executor.
    forbidden = [name for name in dir(ex) if "withdraw" in name.lower()]
    assert forbidden == [], f"withdrawal capability detected: {forbidden}"

    # Explicitly prove that enabling live without credentials does not silently
    # degrade into a network attempt or an implicit dry run.
    try:
        KrakenSpotExecutor(
            KrakenExecutionConfig(api_key="", api_secret="", live_enabled=True)
        )
    except KrakenExecutionError as exc:
        assert "requires" in str(exc)
    else:
        raise AssertionError("live mode accepted missing credentials")

    out = {
        "status": "PROVEN_NON_TRADING_EXECUTION_PREFLIGHT",
        "live_trading_default": False,
        "order_construction": "PROVEN",
        "submission_while_off": "BLOCKED",
        "private_api_while_off": "BLOCKED",
        "withdrawal_capability": False,
        "missing_credentials_live_mode": "BLOCKED",
        "network_order_submitted": False,
        "live_money_execution": False,
        "evidence_scope": "non-trading safety invariants only; no provider/live execution proof",
    }
    evidence = ROOT / "evidence" / "execution_live_preflight.json"
    evidence.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
