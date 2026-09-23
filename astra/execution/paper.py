"""Deterministic paper execution engine.

Paper execution never calls an exchange. It models order lifecycle and keeps a
separate broker state so execution/reconciliation logic can be exercised
without risking capital.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"


@dataclass
class PaperOrder:
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    limit_price: Decimal | None
    remaining: Decimal
    filled: Decimal = Decimal("0")
    avg_fill_price: Decimal = Decimal("0")
    status: OrderStatus = OrderStatus.ACCEPTED
    submitted_step: int = 0
    cancel_requested: bool = False


@dataclass
class PaperBroker:
    """Deterministic broker with fees, slippage, latency and partial fills."""

    cash: Decimal = Decimal("10000")
    fee_rate: Decimal = Decimal("0.0004")
    slippage_bps: Decimal = Decimal("2")
    latency_steps: int = 0
    max_fill_fraction: Decimal = Decimal("1")
    reject_next: bool = False
    orders: dict[str, PaperOrder] = field(default_factory=dict)
    positions: dict[str, Decimal] = field(default_factory=dict)
    fees_paid: Decimal = Decimal("0")
    step: int = 0
    _sequence: int = 0

    def submit(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal | str,
        order_type: str = "market",
        limit_price: Decimal | str | None = None,
    ) -> PaperOrder:
        side = side.lower()
        order_type = order_type.lower()
        qty = Decimal(str(quantity))
        price = None if limit_price is None else Decimal(str(limit_price))
        if side not in {"buy", "sell"} or qty <= 0:
            raise ValueError("invalid paper order")
        if order_type not in {"market", "limit"}:
            raise ValueError("unsupported order type")
        if order_type == "limit" and (price is None or price <= 0):
            raise ValueError("limit orders require a positive price")

        self._sequence += 1
        oid = f"paper-{self._sequence:08d}"
        status = OrderStatus.REJECTED if self.reject_next else OrderStatus.ACCEPTED
        self.reject_next = False
        order = PaperOrder(
            order_id=oid,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            limit_price=price,
            remaining=qty,
            status=status,
            submitted_step=self.step,
        )
        self.orders[oid] = order
        return order

    def advance(self, *, symbol: str, market_price: Decimal | str) -> list[PaperOrder]:
        """Advance one market step and fill eligible orders."""
        self.step += 1
        px = Decimal(str(market_price))
        if px <= 0:
            raise ValueError("market price must be positive")
        changed = []
        for order in self.orders.values():
            if order.status not in {OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED}:
                continue
            if self.step - order.submitted_step < self.latency_steps:
                continue
            if order.cancel_requested:
                order.status = OrderStatus.CANCELED
                changed.append(order)
                continue
            if order.order_type == "limit":
                eligible = (order.side == "buy" and px <= order.limit_price) or (
                    order.side == "sell" and px >= order.limit_price
                )
                if not eligible:
                    continue
            fill_qty = min(order.remaining, order.quantity * self.max_fill_fraction)
            if fill_qty <= 0:
                continue
            slip = self.slippage_bps / Decimal("10000")
            fill_px = px * (Decimal("1") + slip if order.side == "buy" else Decimal("1") - slip)
            notional = fill_qty * fill_px
            fee = notional * self.fee_rate
            if order.side == "buy":
                if self.cash < notional + fee:
                    order.status = OrderStatus.REJECTED
                    changed.append(order)
                    continue
                self.cash -= notional + fee
                self.positions[order.symbol] = self.positions.get(order.symbol, Decimal("0")) + fill_qty
            else:
                position = self.positions.get(order.symbol, Decimal("0"))
                if position < fill_qty:
                    order.status = OrderStatus.REJECTED
                    changed.append(order)
                    continue
                self.positions[order.symbol] = position - fill_qty
                self.cash += notional - fee
            prior_notional = order.avg_fill_price * order.filled
            order.filled += fill_qty
            order.remaining -= fill_qty
            order.avg_fill_price = (prior_notional + notional) / order.filled
            self.fees_paid += fee
            order.status = OrderStatus.FILLED if order.remaining == 0 else OrderStatus.PARTIALLY_FILLED
            changed.append(order)
        return changed

    def cancel(self, order_id: str) -> PaperOrder:
        order = self.orders[order_id]
        if order.status in {OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED}:
            order.cancel_requested = True
        return order

    def snapshot(self) -> dict:
        return {
            "cash": str(self.cash),
            "positions": {k: str(v) for k, v in self.positions.items()},
            "fees_paid": str(self.fees_paid),
            "step": self.step,
            "orders": {
                k: {
                    "status": v.status.value,
                    "quantity": str(v.quantity),
                    "filled": str(v.filled),
                    "remaining": str(v.remaining),
                    "avg_fill_price": str(v.avg_fill_price),
                }
                for k, v in self.orders.items()
            },
        }
