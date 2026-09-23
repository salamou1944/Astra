"""Deterministic order-intent ledger primitives.

The ledger is independent of an exchange and gives every order intent a stable
idempotency key. It is deliberately append-only at the API level: callers can
record a new event but cannot mutate an earlier event through these primitives.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass(frozen=True)
class OrderIntent:
    intent_id: str
    symbol: str
    side: str
    quantity: str
    order_type: str
    strategy_id: str
    signal_timestamp: str

    @staticmethod
    def create(*, symbol: str, side: str, quantity: str, order_type: str,
               strategy_id: str, signal_timestamp: str) -> "OrderIntent":
        canonical = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "quantity": str(quantity),
            "order_type": order_type.lower(),
            "strategy_id": strategy_id,
            "signal_timestamp": signal_timestamp,
        }
        raw = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        intent_id = "intent-" + hashlib.sha256(raw).hexdigest()[:24]
        return OrderIntent(intent_id=intent_id, **canonical)


@dataclass(frozen=True)
class ExecutionEvent:
    sequence: int
    intent_id: str
    event_type: str
    timestamp: str
    payload: dict

    @staticmethod
    def now(*, sequence: int, intent_id: str, event_type: str, payload: dict) -> "ExecutionEvent":
        return ExecutionEvent(
            sequence=sequence,
            intent_id=intent_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=dict(payload),
        )


class ExecutionLedger:
    def __init__(self) -> None:
        self._events: list[ExecutionEvent] = []
        self._intent_ids: set[str] = set()

    @property
    def events(self) -> tuple[ExecutionEvent, ...]:
        return tuple(self._events)

    def register_intent(self, intent: OrderIntent) -> bool:
        """Return False instead of registering a duplicate intent."""
        if intent.intent_id in self._intent_ids:
            return False
        self._intent_ids.add(intent.intent_id)
        self._events.append(ExecutionEvent.now(
            sequence=len(self._events) + 1,
            intent_id=intent.intent_id,
            event_type="intent_created",
            payload={"symbol": intent.symbol, "side": intent.side, "quantity": intent.quantity},
        ))
        return True

    def append(self, *, intent_id: str, event_type: str, payload: dict) -> ExecutionEvent:
        if intent_id not in self._intent_ids:
            raise KeyError(f"unknown intent: {intent_id}")
        event = ExecutionEvent.now(
            sequence=len(self._events) + 1,
            intent_id=intent_id,
            event_type=event_type,
            payload=payload,
        )
        self._events.append(event)
        return event

    def contains_event(self, intent_id: str, event_type: str) -> bool:
        return any(e.intent_id == intent_id and e.event_type == event_type for e in self._events)
