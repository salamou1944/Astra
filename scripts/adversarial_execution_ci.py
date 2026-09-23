"""Paper-only adversarial execution checks for ASTRA.

No exchange calls, no credentials, no live money. Each fault must fail closed.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astra.execution.paper import OrderStatus, PaperBroker
from astra.execution.safety import HaltReason, KillSwitch, reconcile_and_trip


def gate_off(kill: KillSwitch) -> bool:
    from astra.execution.safety import ExecutionGate
    return ExecutionGate(kill).authorize(
        data_valid=True, strategy_valid=True, risk_valid=True,
        execution_valid=True, reconciliation_valid=True,
        human_approval=True, live_enabled=True
    )


def main() -> None:
    cases = {}

    # Duplicate intent is rejected by the lifecycle/ledger layer; here we
    # verify the broker itself never turns one order into two fills.
    broker = PaperBroker(cash=Decimal("10000"), max_fill_fraction=Decimal("1"))
    a = broker.submit(symbol="BTC/USD", side="buy", quantity="1")
    b = broker.advance(symbol="BTC/USD", market_price="100")
    cases["single_order_single_fill"] = (
        len(b) == 1 and a.status == OrderStatus.FILLED and a.filled == Decimal("1")
    )

    # Partial fill followed by completion.
    broker = PaperBroker(cash=Decimal("10000"), max_fill_fraction=Decimal("0.4"))
    o = broker.submit(symbol="BTC/USD", side="buy", quantity="1")
    broker.advance(symbol="BTC/USD", market_price="100")
    partial_ok = o.status == OrderStatus.PARTIALLY_FILLED and o.filled == Decimal("0.4")
    broker.advance(symbol="BTC/USD", market_price="101")
    broker.advance(symbol="BTC/USD", market_price="102")
    full_ok = o.status == OrderStatus.FILLED and o.filled == Decimal("1")
    cases["partial_fill_then_fill"] = partial_ok and full_ok

    # Delayed fill: latency=2 means two waiting advances, fill on the third.
    broker = PaperBroker(cash=Decimal("10000"), latency_steps=2)
    o = broker.submit(symbol="BTC/USD", side="buy", quantity="1")
    broker.advance(symbol="BTC/USD", market_price="100")
    w1 = o.status == OrderStatus.ACCEPTED
    broker.advance(symbol="BTC/USD", market_price="100")
    w2 = o.status == OrderStatus.ACCEPTED
    broker.advance(symbol="BTC/USD", market_price="100")
    cases["delayed_fill"] = w1 and w2 and o.status == OrderStatus.FILLED

    # Cancellation race: cancellation requested before the next execution
    # step must prevent a fill.
    broker = PaperBroker(cash=Decimal("10000"))
    o = broker.submit(symbol="BTC/USD", side="buy", quantity="1")
    broker.cancel(o.order_id)
    broker.advance(symbol="BTC/USD", market_price="100")
    cases["cancel_before_fill_wins"] = o.status == OrderStatus.CANCELED and o.filled == 0

    # Rejection must not change cash/position.
    broker = PaperBroker(cash=Decimal("10000"), reject_next=True)
    o = broker.submit(symbol="BTC/USD", side="buy", quantity="1")
    snap = broker.snapshot()
    cases["rejected_order_no_position_change"] = (
        o.status == OrderStatus.REJECTED
        and snap["cash"] == "10000"
        and snap["positions"] == {}
    )

    # Every reconciliation fault trips the kill switch and blocks the gate.
    base = dict(
        local_orders={"o1": {"status": "filled", "filled": "1", "remaining": "0", "quantity": "1"}},
        exchange_orders={"o1": {"status": "filled", "filled": "1", "remaining": "0", "quantity": "1"}},
        local_positions={"BTC/USD": "1"},
        exchange_positions={"BTC/USD": "1"},
        local_balances={"USD": "9899"},
        exchange_balances={"USD": "9899"},
    )
    faults = {
        "missing_exchange_order": {**base, "exchange_orders": {}},
        "unknown_exchange_order": {**base, "exchange_orders": {**base["exchange_orders"], "o2": base["exchange_orders"]["o1"]}},
        "position_mismatch": {**base, "exchange_positions": {"BTC/USD": "0"}},
        "balance_mismatch": {**base, "exchange_balances": {"USD": "9999"}},
        "partial_fill_mismatch": {**base, "exchange_orders": {"o1": {"status": "partially_filled", "filled": "0.5", "remaining": "0.5", "quantity": "1"}}},
    }
    for name, kwargs in faults.items():
        kill = KillSwitch()
        result = reconcile_and_trip(kill_switch=kill, **kwargs)
        cases[name] = (
            not result.ok
            and kill.halted
            and kill.reason == HaltReason.RECONCILIATION.value
            and not gate_off(kill)
        )

    # Safety trip conditions are fail-closed even without exchange interaction.
    for name, reason in {
        "stale_data": HaltReason.STALE_DATA,
        "invalid_price": HaltReason.INVALID_PRICE,
        "abnormal_volatility": HaltReason.VOLATILITY,
        "corrupted_state": HaltReason.CORRUPTED_STATE,
        "clock_anomaly": HaltReason.CLOCK,
        "api_error": HaltReason.API_ERROR,
    }.items():
        kill = KillSwitch()
        kill.trip(reason)
        cases[name + "_halts_gate"] = kill.halted and not gate_off(kill)

    # No live execution is performed anywhere in this script.
    if not all(cases.values()):
        failed = [k for k, v in cases.items() if not v]
        raise AssertionError(f"adversarial cases failed: {failed}")

    evidence = {
        "status": "PROVEN_ADVERSARIAL_EXECUTION",
        "paper_only": True,
        "exchange_orders_submitted": 0,
        "live_money_execution": False,
        "withdrawal_capability": False,
        "cases": cases,
    }
    out = ROOT / "evidence" / "adversarial_execution_ci.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
