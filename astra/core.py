from dataclasses import dataclass
import math, random

@dataclass(frozen=True)
class Bar:
    t:int; close:float

def market(n=600, seed=7):
    rng=random.Random(seed); p=100.0; out=[]
    for t in range(n):
        drift=0.0012 if t<180 else (-0.0007 if t<360 else 0.0010)
        shock=rng.gauss(0,0.0025)
        p*=math.exp(drift+shock)
        out.append(Bar(t,p))
    return out

def sma(x,w):
    return [None if i+1<w else sum(x[i+1-w:i+1])/w for i in range(len(x))]

def signals(bars,fast=12,slow=40):
    c=[b.close for b in bars]; f=sma(c,fast); s=sma(c,slow); sig=[]
    prev=0
    for i in range(len(c)):
        cur=prev
        if f[i] is not None and s[i] is not None: cur=1 if f[i]>s[i] else -1
        sig.append(cur); prev=cur
    return sig

def backtest_signals(bars, sig, fee=0.0005, slip=0.0002, max_pos=1.0, stop_loss=0.03):
    """Backtest an explicit target-signal series with deterministic execution costs."""
    if len(sig) != len(bars):
        raise ValueError("signals length must match bars length")
    equity=1.0; pos=0.0; entry=None; peak=1.0; maxdd=0.; trades=0
    for i,b in enumerate(bars):
        if i:
            equity *= 1.0 + pos*(b.close/bars[i-1].close-1.0)
        raw=sig[i]
        target=max(-max_pos,min(max_pos,float(raw)))
        if pos and entry is not None and b.close <= entry*(1-stop_loss):
            target=0.0
        delta=target-pos
        if delta:
            equity *= max(0.0, 1.0 - abs(delta)*(fee+slip))
            trades += 1
            pos=target
            entry=b.close if pos else None
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    return {'return_pct':round((equity-1)*100,4),'max_drawdown_pct':round(maxdd*100,4),'trades':trades}

def backtest(bars, fast=12, slow=40, fee=0.0005, slip=0.0002, max_pos=1.0, stop_loss=0.03):
    """Deterministic close-to-close backtest using the SMA target signal."""
    return backtest_signals(bars, signals(bars, fast, slow), fee, slip, max_pos, stop_loss)

def adversary(bars, base=(12,40)):
    variants=[(10,35),(11,42),(12,40),(13,45),(15,50)]
    results=[backtest(bars,*v) for v in variants]
    basev=backtest(bars,*base)['return_pct']; survived=sum(r['max_drawdown_pct'] <= 8.0 for r in results)/len(results)
    return {'base_return_pct':basev,'survival_ratio':survived,'passed':survived>=0.8,'variants':[r['return_pct'] for r in results], 'max_drawdowns':[r['max_drawdown_pct'] for r in results]}

@dataclass
class Risk:
    max_position:float=1.0; max_daily_loss:float=0.02

class PaperBroker:
    def __init__(self,risk=Risk()):
        self.position=0.0; self.equity=1.0; self.risk=risk; self.orders=[]; self.day_start_equity=1.0; self.halted=False
    def reset_day(self):
        self.day_start_equity=self.equity; self.halted=False
    def mark_equity(self,equity):
        self.equity=float(equity)
        if self.equity <= self.day_start_equity*(1-self.risk.max_daily_loss):
            self.position=0.0; self.halted=True; self.orders.append(0.0)
        return self.equity
    def order(self,target):
        if self.halted: return 0.0
        target=max(-self.risk.max_position,min(self.risk.max_position,target)); self.position=target; self.orders.append(target); return target
