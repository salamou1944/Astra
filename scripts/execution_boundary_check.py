"""Offline execution-boundary verification. Never submits an order."""
import json
from pathlib import Path
from astra.execution.kraken import KrakenExecutionConfig, KrakenSpotExecutor

ROOT = Path(__file__).resolve().parents[1]
ex = KrakenSpotExecutor(KrakenExecutionConfig(api_key="", api_secret="", live_enabled=False))
order = ex.build_add_order(pair="XBTUSD", side="buy", ordertype="market", volume="0.0001")
result = ex.submit_if_authorized(**order)
assert result["submitted"] is False
assert result["mode"] == "OFF"
assert not hasattr(ex, "withdraw")

out = {
    "status": "PROVEN_EXECUTION_BOUNDARY_OFFLINE",
    "network_order_submitted": False,
    "live_money_execution": False,
    "withdrawal_capability": False,
    "order_construction": "PROVEN",
    "private_api_network_access": "BLOCKED_WHEN_OFF",
    "credentials_source": "environment_only",
    "evidence_scope": "offline safety boundary; not a live execution proof"
}
(ROOT / "evidence" / "execution_boundary_check.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
