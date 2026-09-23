from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class RiskLimits:
    max_position: float = 1.0
    max_daily_loss: float = 0.02
    max_drawdown: float = 0.08

class RiskGuardian:
    """Deterministic risk layer. It can only reduce/deny exposure; it never increases it."""
    def __init__(self, limits: RiskLimits = RiskLimits()):
        if limits.max_position < 0 or limits.max_daily_loss < 0 or limits.max_drawdown < 0:
            raise ValueError("risk limits must be non-negative")
        self.limits = limits; self.day_start = 1.0; self.peak = 1.0; self.halted = False; self.reason = None
    def reset_day(self, equity: float):
        equity = float(equity)
        if not math.isfinite(equity) or equity < 0: raise ValueError("equity must be non-negative")
        self.day_start = equity; self.peak = equity; self.halted = False; self.reason = None
    def observe(self, equity: float):
        equity = float(equity)
        if not math.isfinite(equity) or equity < 0: raise ValueError("equity must be a finite non-negative number")
        self.peak = max(self.peak, equity)
        daily_loss = (self.day_start - equity) / self.day_start if self.day_start else 0.0
        drawdown = (self.peak - equity) / self.peak if self.peak else 0.0
        if daily_loss >= self.limits.max_daily_loss: self.halted = True; self.reason = "daily_loss_limit"
        if drawdown >= self.limits.max_drawdown: self.halted = True; self.reason = "max_drawdown_limit"
        return {"equity": equity, "daily_loss": daily_loss, "drawdown": drawdown, "halted": self.halted, "reason": self.reason}
    def authorize(self, target: float) -> float:
        target = float(target)
        if not math.isfinite(target): raise ValueError("target must be finite")
        if self.halted: return 0.0
        return max(-self.limits.max_position, min(self.limits.max_position, target))
