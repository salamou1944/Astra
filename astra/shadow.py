from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from .core import Bar, signals
from .risk import RiskGuardian, RiskLimits

@dataclass(frozen=True)
class ShadowEvent:
    index: int
    timestamp: int
    signal: float
    authorized_target: float
    equity: float
    halted: bool
    reason: str | None

class ShadowSession:
    """No-order shadow execution: consumes bars/signals and records what ASTRA would do."""
    def __init__(self, limits: RiskLimits = RiskLimits()):
        self.guardian = RiskGuardian(limits); self.position = 0.0; self.equity = 1.0; self.events: list[ShadowEvent] = []
    def run(self, bars: list[Bar], fast=12, slow=40):
        if not bars: raise ValueError("bars cannot be empty")
        if fast <= 0 or slow <= 0 or fast >= slow: raise ValueError("require 0 < fast < slow")
        if any((not math.isfinite(b.close) or b.close <= 0) for b in bars): raise ValueError("bars must have finite positive closes")
        self.position = 0.0; self.equity = 1.0; self.events = []
        sig = signals(bars, fast, slow); self.guardian.reset_day(self.equity)
        for i, bar in enumerate(bars):
            if i: self.equity *= 1.0 + self.position * (bar.close / bars[i-1].close - 1.0)
            risk = self.guardian.observe(self.equity); target = self.guardian.authorize(sig[i]); self.position = target
            self.events.append(ShadowEvent(i, bar.t, float(sig[i]), target, self.equity, risk["halted"], risk["reason"]))
        return self.events
    def export(self): return [asdict(x) for x in self.events]
    def summary(self):
        return {"events": len(self.events), "final_equity": self.equity, "halted": self.guardian.halted, "halt_reason": self.guardian.reason, "real_orders": 0}
