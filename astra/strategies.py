from __future__ import annotations
from dataclasses import dataclass
from .core import Bar, sma

@dataclass(frozen=True)
class StrategySpec:
    name: str
    params: tuple[int, ...]

def _closes(bars): return [b.close for b in bars]

def trend(bars, fast=12, slow=40):
    c=_closes(bars); f=sma(c,fast); s=sma(c,slow); out=[]
    for i in range(len(c)):
        out.append(0 if f[i] is None or s[i] is None else (1 if f[i]>s[i] else -1))
    return out

def mean_reversion(bars, window=20, z=1.5):
    c=_closes(bars); m=sma(c,window); out=[]
    for i,p in enumerate(c):
        if m[i] is None: out.append(0); continue
        d=(p/m[i])-1
        out.append(1 if d < -z/100 else (-1 if d > z/100 else 0))
    return out

def breakout(bars, window=30):
    c=_closes(bars); out=[]
    for i,p in enumerate(c):
        if i < window: out.append(0); continue
        hi=max(c[i-window:i]); lo=min(c[i-window:i])
        out.append(1 if p>hi else (-1 if p<lo else 0))
    return out

def regime(bars, short=10, long=40):
    c=_closes(bars); out=[]
    for i in range(len(c)):
        if i < long: out.append('unknown'); continue
        short_ret=c[i]/c[i-short]-1
        long_ret=c[i]/c[i-long]-1
        out.append('trend' if short_ret*long_ret>0 and abs(long_ret)>0.01 else 'range')
    return out


def long_momentum(bars, window=30, threshold=0.0):
    c=_closes(bars); out=[]
    for i,p in enumerate(c):
        if i < window: out.append(0); continue
        ret=p/c[i-window]-1
        out.append(1 if ret > threshold/100 else 0)
    return out
