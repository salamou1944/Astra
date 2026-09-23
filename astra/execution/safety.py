"""Independent execution safety controls.

These controls sit above strategy output and below any intelligence layer.
They fail closed: an unsafe state cannot authorize an order.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HaltReason(str, Enum):
    DRAWdown = "drawdown_limit"
    DAILY_LOSS = "daily_loss_limit"
    STALE_DATA = "stale_data"
    API_ERROR = "api_error"
    RECONCILIATION = "reconciliation_failure"
    VOLATILITY = "abnormal_volatility"
    INVALID_PRICE = "invalid_price"
    DUPLICATE_ORDER = "duplicate_order"
    UNKNOWN_POSITION = "unknown_position"
    CORRUPTED_STATE = "corrupted_state"
    CLOCK = "clock_anomaly"
    MANUAL = "manual"


@dataclass
class KillSwitch:
    halted: bool = False
    reason: str | None = None

    def trip(self, reason: HaltReason | str) -> None:
        self.halted = True
        self.reason = reason.value if isinstance(reason, HaltReason) else str(reason)

    def reset(self) -> None:
        self.halted = False
        self.reason = None

    def authorize(self) -> bool:
        return not self.halted


@dataclass(frozen=True)
class ReconciliationResult:
    ok: bool
    mismatches: tuple[str, ...]


def reconcile(
    *,
    local_orders: dict[str, dict],
    exchange_orders: dict[str, dict],
    local_positions: dict[str, str],
    exchange_positions: dict[str, str],
    local_balances: dict[str, str],
    exchange_balances: dict[str, str],
) -> ReconciliationResult:
    mismatches: list[str] = []
    local_ids = set(local_orders)
    remote_ids = set(exchange_orders)
    mismatches.extend(f"missing_exchange_order:{x}" for x in sorted(local_ids - remote_ids))
    mismatches.extend(f"unknown_exchange_order:{x}" for x in sorted(remote_ids - local_ids))
    for order_id in sorted(local_ids & remote_ids):
        local = local_orders[order_id]
        remote = exchange_orders[order_id]
        for field in ("status", "filled", "remaining", "quantity"):
            if field in local and field in remote and str(local[field]) != str(remote[field]):
                mismatches.append(f"order_field_mismatch:{order_id}:{field}")
    if local_positions != exchange_positions:
        mismatches.append("position_mismatch")
    if local_balances != exchange_balances:
        mismatches.append("balance_mismatch")
    return ReconciliationResult(not mismatches, tuple(mismatches))


def reconcile_and_trip(
    *,
    kill_switch: KillSwitch,
    local_orders: dict[str, dict],
    exchange_orders: dict[str, dict],
    local_positions: dict[str, str],
    exchange_positions: dict[str, str],
    local_balances: dict[str, str],
    exchange_balances: dict[str, str],
) -> ReconciliationResult:
    """Reconcile state and trip the kill switch on any mismatch."""
    result = reconcile(
        local_orders=local_orders,
        exchange_orders=exchange_orders,
        local_positions=local_positions,
        exchange_positions=exchange_positions,
        local_balances=local_balances,
        exchange_balances=exchange_balances,
    )
    if not result.ok:
        kill_switch.trip(HaltReason.RECONCILIATION)
    return result


class ExecutionGate:
    """Final fail-closed gate; no strategy or ChatGPT output can bypass it."""

    def __init__(self, kill_switch: KillSwitch):
        self.kill_switch = kill_switch

    def authorize(
        self,
        *,
        data_valid: bool,
        strategy_valid: bool,
        risk_valid: bool,
        execution_valid: bool,
        reconciliation_valid: bool,
        human_approval: bool,
        live_enabled: bool,
    ) -> bool:
        return bool(
            live_enabled
            and data_valid
            and strategy_valid
            and risk_valid
            and execution_valid
            and reconciliation_valid
            and human_approval
            and self.kill_switch.authorize()
        )
