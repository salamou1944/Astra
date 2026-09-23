"""Unified non-live execution lifecycle.

The lifecycle is deliberately broker-agnostic at the boundary and uses the
execution ledger as the idempotency/audit source. Paper execution is the only
broker wired here; live exchange submission remains behind the Kraken safety
gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .ledger import ExecutionLedger, OrderIntent
from .paper import OrderStatus, PaperBroker, PaperOrder


@dataclass(frozen=True)
class LifecycleResult:
    intent_id: str
    order_id: str | None
    status: str
    duplicate: bool = False


class PaperExecutionLifecycle:
    """Signal -> intent -> paper order -> fills -> ledger events."""

    def __init__(self, *, broker: PaperBroker | None = None,
                 ledger: ExecutionLedger | None = None) -> None:
        self.broker = broker or PaperBroker()
        self.ledger = ledger or ExecutionLedger()
        self._intent_to_order: dict[str, str] = {}

    def submit_intent(self, intent: OrderIntent) -> LifecycleResult:
        if intent.intent_id in self._intent_to_order:
            order_id = self._intent_to_order[intent.intent_id]
            return LifecycleResult(
                intent.intent_id,
                order_id,
                self.broker.orders[order_id].status.value,
                duplicate=True,
            )

        if not self.ledger.register_intent(intent):
            raise RuntimeError("ledger rejected an untracked duplicate intent")

        order = self.broker.submit(
            symbol=intent.symbol,
            side=intent.side,
            quantity=Decimal(intent.quantity),
            order_type=intent.order_type,
        )
        self._intent_to_order[intent.intent_id] = order.order_id
        self.ledger.append(
            intent_id=intent.intent_id,
            event_type="accepted" if order.status != OrderStatus.REJECTED else "rejected",
            payload={"order_id": order.order_id, "status": order.status.value},
        )
        return LifecycleResult(intent.intent_id, order.order_id, order.status.value)

    def advance(self, *, symbol: str, market_price: Decimal | str) -> list[PaperOrder]:
        changed = self.broker.advance(symbol=symbol, market_price=market_price)
        reverse = {order_id: intent_id for intent_id, order_id in self._intent_to_order.items()}
        for order in changed:
            intent_id = reverse[order.order_id]
            if order.status == OrderStatus.PARTIALLY_FILLED:
                event = "partially_filled"
            elif order.status == OrderStatus.FILLED:
                event = "filled"
            elif order.status == OrderStatus.CANCELED:
                event = "canceled"
            elif order.status == OrderStatus.REJECTED:
                event = "rejected"
            else:
                continue
            self.ledger.append(
                intent_id=intent_id,
                event_type=event,
                payload={
                    "order_id": order.order_id,
                    "filled": str(order.filled),
                    "remaining": str(order.remaining),
                    "avg_fill_price": str(order.avg_fill_price),
                },
            )
        return changed

    def cancel(self, intent_id: str) -> PaperOrder:
        order_id = self._intent_to_order[intent_id]
        order = self.broker.cancel(order_id)
        return order

    def reconcile(self) -> tuple[bool, tuple[str, ...]]:
        """Reconcile the lifecycle's own broker state against its ledger mapping."""
        mismatches: list[str] = []
        known_order_ids = set(self.broker.orders)
        mapped_order_ids = set(self._intent_to_order.values())
        if known_order_ids != mapped_order_ids:
            mismatches.append("paper_order_mapping_mismatch")
        for intent_id, order_id in self._intent_to_order.items():
            if not self.ledger.contains_event(intent_id, "intent_created"):
                mismatches.append(f"missing_intent:{intent_id}")
            if order_id not in self.broker.orders:
                mismatches.append(f"missing_paper_order:{order_id}")
        return (not mismatches, tuple(mismatches))
