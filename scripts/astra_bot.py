"""ASTRA personal trading bot runner.

Default mode is PAPER. It consumes live public Kraken OHLC data, evaluates the
fixed ASTRA strategy, and routes simulated orders through the audited paper
lifecycle. Live exchange submission is never enabled by this runner.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astra.core import Bar
from astra.execution.lifecycle import PaperExecutionLifecycle
from astra.execution.ledger import OrderIntent
from astra.execution.paper import PaperBroker
from astra.execution.safety import ExecutionGate, KillSwitch
from astra.strategies import long_momentum

KRAKEN_URL = "https://api.kraken.com/0/public/OHLC"
PAIR = "XBTUSD"
INTERVAL = 1440
WINDOW = 30
THRESHOLD = 0.0
DEFAULT_QTY = Decimal("0.001")


@dataclass(frozen=True)
class BotSnapshot:
    mode: str
    pair: str
    interval: int
    observed_bars: int
    last_timestamp: str
    last_price: str
    signal: int
    previous_signal: int
    intent_created: bool
    order_id: str | None
    order_status: str | None
    paper_cash: str
    paper_position: str
    kill_switch_halted: bool
    live_order_submitted: bool


def _timestamp(t: int) -> str:
    return datetime.fromtimestamp(int(t), tz=timezone.utc).isoformat()


def fetch_ohlc(*, pair: str = PAIR, interval: int = INTERVAL, timeout: float = 15.0) -> list[Bar]:
    req = Request(
        f"{KRAKEN_URL}?pair={pair}&interval={interval}",
        headers={"User-Agent": "ASTRA-personal-bot/1.0"},
    )
    with urlopen(req, timeout=timeout) as response:
        payload = json.loads(response.read().decode())
    if payload.get("error"):
        raise RuntimeError("Kraken public API error: " + "; ".join(map(str, payload["error"])))
    result = payload["result"]
    pair_key = next(k for k in result if k != "last")
    rows = result[pair_key]
    bars = [
        Bar(t=int(row[0]), close=float(row[4]))
        for row in rows
    ]
    if len(bars) < WINDOW + 2:
        raise RuntimeError(f"insufficient public market data: {len(bars)} bars")
    return bars


def run_once(*, previous_signal: int = 0, quantity: Decimal = DEFAULT_QTY) -> BotSnapshot:
    bars = fetch_ohlc()
    signals = long_momentum(bars, window=WINDOW, threshold=THRESHOLD)
    signal = int(signals[-1])
    last = bars[-1]

    broker = PaperBroker(cash=Decimal("10000"), fee_rate=Decimal("0.0005"), slippage_bps=Decimal("2"))
    lifecycle = PaperExecutionLifecycle(broker=broker)
    kill_switch = KillSwitch()
    gate = ExecutionGate(kill_switch)

    intent_created = False
    order_id = None
    order_status = None

    # The bot observes every cycle but only creates an intent on a signal
    # transition. Entry is paper-only; live authorization is explicitly false.
    if signal != previous_signal:
        side = "buy" if signal == 1 else "sell"
        if side == "buy":
            intent = OrderIntent.create(
                symbol=PAIR,
                side=side,
                quantity=str(quantity),
                order_type="market",
                strategy_id="long_momentum_w30_t0",
                signal_timestamp=_timestamp(last.t),
            )
            result = lifecycle.submit_intent(intent)
            lifecycle.advance(symbol=PAIR, market_price=Decimal(str(last.close)))
            intent_created = True
            order_id = result.order_id
            order_status = lifecycle.broker.orders[order_id].status.value if order_id else None
        else:
            # A fresh process has no position to sell; this is deliberately
            # recorded as an observation rather than manufacturing a position.
            order_status = "no_position_to_sell"

    authorized = gate.authorize(
        data_valid=True,
        strategy_valid=False,
        risk_valid=True,
        execution_valid=True,
        reconciliation_valid=True,
        human_approval=False,
        live_enabled=False,
    )
    if authorized:
        raise AssertionError("ASTRA bot must never authorize live execution")

    ok, mismatches = lifecycle.reconcile()
    if not ok:
        kill_switch.trip("paper lifecycle reconciliation failed: " + ",".join(mismatches))
    return BotSnapshot(
        mode="PAPER",
        pair=PAIR,
        interval=INTERVAL,
        observed_bars=len(bars),
        last_timestamp=_timestamp(last.t),
        last_price=str(last.close),
        signal=signal,
        previous_signal=previous_signal,
        intent_created=intent_created,
        order_id=order_id,
        order_status=order_status,
        paper_cash=str(broker.cash),
        paper_position=str(broker.positions.get(PAIR, Decimal("0"))),
        kill_switch_halted=kill_switch.halted,
        live_order_submitted=False,
    )


def main() -> int:
    if os.getenv("ASTRA_LIVE_TRADING", "0") == "1":
        raise SystemExit("ASTRA bot runner refuses live mode; live trading is not part of this handover.")

    previous = int(os.getenv("ASTRA_PREVIOUS_SIGNAL", "0"))
    snapshot = run_once(previous_signal=previous)
    out = ROOT / "evidence" / "astra_bot_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(snapshot), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(asdict(snapshot), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
