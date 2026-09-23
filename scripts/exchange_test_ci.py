"""Safe exchange-boundary test using Kraken public Spot endpoints only.

No API credentials, no private endpoints, no order submission, no real money.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astra.execution.kraken import KrakenExecutionConfig, KrakenExecutionError, KrakenSpotExecutor
from astra.execution.safety import ExecutionGate, KillSwitch


def public_get(path: str, params: dict[str, str]) -> dict:
    url = "https://api.kraken.com" + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "ASTRA-safe-exchange-test/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if data.get("error"):
        raise RuntimeError("Kraken public API error: " + "; ".join(map(str, data["error"])))
    return data


def main() -> None:
    evidence: dict = {
        "status": "PROVEN_SAFE_EXCHANGE_TEST",
        "exchange": "Kraken",
        "public_api": True,
        "private_api_called": False,
        "orders_submitted": 0,
        "live_money_execution": False,
        "withdrawal_capability": False,
    }

    ticker = public_get("/0/public/Ticker", {"pair": "XBTUSD"})
    result = ticker["result"]
    if not result:
        raise AssertionError("Kraken returned no ticker result")
    pair_key = next(iter(result))
    last = float(result[pair_key]["c"][0])
    if not (last > 0):
        raise AssertionError("invalid live public market price")
    evidence["ticker_pair"] = pair_key
    evidence["live_public_price_positive"] = True

    assets = public_get("/0/public/AssetPairs", {"pair": "XBTUSD"})
    if not assets["result"]:
        raise AssertionError("Kraken returned no AssetPairs result")
    evidence["asset_pair_metadata_available"] = True

    cfg = KrakenExecutionConfig(api_key="", api_secret="", live_enabled=False)
    executor = KrakenSpotExecutor(cfg)
    payload = executor.build_add_order(
        pair="XBTUSD", side="buy", ordertype="limit", volume="0.001", price=str(last)
    )
    if payload["pair"] != "XBTUSD" or payload["type"] != "buy":
        raise AssertionError("order payload construction failed")
    evidence["order_payload_validation"] = True

    kill = KillSwitch()
    gate = ExecutionGate(kill)
    blocked = executor.submit_if_authorized(
        gate=gate,
        data_valid=True, strategy_valid=True, risk_valid=True,
        execution_valid=True, reconciliation_valid=True,
        human_approval=True, pair="XBTUSD", side="buy",
        ordertype="limit", volume="0.001", price=str(last),
    )
    if blocked.get("submitted") is not False or blocked.get("mode") != "OFF":
        raise AssertionError("live-off boundary did not fail closed")
    evidence["live_off_gate_blocked"] = True

    if hasattr(executor, "withdraw") or hasattr(executor, "withdraw_funds"):
        raise AssertionError("withdrawal capability unexpectedly present")

    try:
        executor._private("/0/private/Balance", {})
    except KrakenExecutionError as exc:
        if str(exc) != "live execution is OFF":
            raise
        evidence["private_endpoint_blocked_when_off"] = True
    else:
        raise AssertionError("private endpoint was not blocked")

    out = ROOT / "evidence" / "exchange_test_ci.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
