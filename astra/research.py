from __future__ import annotations
from dataclasses import dataclass
from statistics import mean
from .core import backtest, backtest_signals, market

@dataclass(frozen=True)
class Experiment:
    fast: int
    slow: int
    train_size: int = 300
    test_size: int = 100
    step: int = 100
    embargo: int = 0

@dataclass
class ExperimentResult:
    fast: int
    slow: int
    folds: int
    test_returns: list[float]
    mean_return_pct: float
    positive_fold_ratio: float
    max_drawdown_pct: float
    aggregate_return_pct: float
    turnover_trades: int
    passed: bool
    chosen_by_fold: list[tuple[int,int]]

def _rank_train(bars, fasts, slows, fee=0.0005, slip=0.0002):
    scored=[]
    for f in fasts:
        for s in slows:
            if f < s:
                r=backtest(bars, fast=f, slow=s, fee=fee, slip=slip)
                scored.append((r["return_pct"], -r["max_drawdown_pct"], -r["trades"], f, s))
    if not scored: raise ValueError("no valid parameter pairs")
    best=max(scored); return best[3], best[4]

def _equity_curve(bars, fast, slow, fee=0.0005, slip=0.0002):
    from .core import signals
    return signals(bars, fast, slow)

def walk_forward(bars, exp: Experiment, fasts=None, slows=None, fee=0.0005, slip=0.0002) -> ExperimentResult:
    if exp.train_size <= 0 or exp.test_size <= 0 or exp.step <= 0 or exp.embargo < 0: raise ValueError("invalid experiment parameters")
    fasts=tuple(fasts or (6,8,12,16)); slows=tuple(slows or (24,32,40,52))
    returns=[]; dds=[]; chosen=[]; start=0
    while start+exp.train_size+exp.embargo+exp.test_size<=len(bars):
        train_end=start+exp.train_size; test_start=train_end+exp.embargo; test_end=test_start+exp.test_size
        train=bars[start:train_end]; context_start=max(0,test_start-max(slows)); context=bars[context_start:test_end]
        f,s=_rank_train(train,fasts,slows,fee,slip); sig=_equity_curve(context,f,s,fee,slip); offset=test_start-context_start
        r=backtest_signals(context[offset:],sig[offset:],fee=fee,slip=slip)
        returns.append(r["return_pct"]); dds.append(r["max_drawdown_pct"]); chosen.append((f,s)); start+=exp.step
    if not returns: raise ValueError("not enough bars for a walk-forward run")
    mean_r=mean(returns); positive=sum(x>0 for x in returns)/len(returns); maxdd=max(dds); aggregate=1.0
    for x in returns: aggregate*=1.0+x/100.0
    aggregate_return=(aggregate-1.0)*100.0; trades=0; start=0
    for f,s in chosen:
        train_end=start+exp.train_size; test_start=train_end+exp.embargo; test_end=test_start+exp.test_size
        if test_end>len(bars): break
        context_start=max(0,test_start-max(slows)); context=bars[context_start:test_end]; sig=_equity_curve(context,f,s,fee,slip); off=test_start-context_start
        trades+=backtest_signals(context[off:],sig[off:],fee=fee,slip=slip)["trades"]; start+=exp.step
    passed=aggregate_return>0 and positive>=0.5 and maxdd<=8.0
    return ExperimentResult(chosen[-1][0],chosen[-1][1],len(returns),returns,round(mean_r,4),round(positive,4),round(maxdd,4),round(aggregate_return,4),trades,passed,chosen)

def walk_forward_candidate(bars, exp: Experiment, fast: int, slow: int, fee=0.0005, slip=0.0002) -> ExperimentResult:
    if fast<=0 or slow<=0 or fast>=slow: raise ValueError("invalid strategy parameters")
    if exp.train_size<=0 or exp.test_size<=0 or exp.step<=0 or exp.embargo<0: raise ValueError("invalid experiment parameters")
    returns=[]; dds=[]; chosen=[]; trades=0; start=0
    while start+exp.train_size+exp.embargo+exp.test_size<=len(bars):
        train_end=start+exp.train_size; test_start=train_end+exp.embargo; test_end=test_start+exp.test_size
        context_start=max(0,test_start-slow); context=bars[context_start:test_end]; sig=_equity_curve(context,fast,slow,fee,slip); offset=test_start-context_start
        r=backtest_signals(context[offset:],sig[offset:],fee=fee,slip=slip)
        returns.append(r["return_pct"]); dds.append(r["max_drawdown_pct"]); trades+=r["trades"]; chosen.append((fast,slow)); start+=exp.step
    if not returns: raise ValueError("not enough bars for a walk-forward run")
    mean_r=mean(returns); positive=sum(x>0 for x in returns)/len(returns); maxdd=max(dds); wealth=1.0
    for x in returns: wealth*=1.0+x/100.0
    aggregate=(wealth-1.0)*100.0; passed=aggregate>0 and positive>=0.5 and maxdd<=8.0
    return ExperimentResult(fast,slow,len(returns),returns,round(mean_r,4),round(positive,4),round(maxdd,4),round(aggregate,4),trades,passed,chosen)

def tournament(bars, fasts=(6,8,12,16), slows=(24,32,40,52), fee=0.0005, slip=0.0002):
    exp=Experiment(fasts[0],slows[0]); results=[]
    for f in fasts:
        for s in slows:
            if f<s: results.append(walk_forward_candidate(bars,exp,f,s,fee,slip))
    return sorted(results,key=lambda r:(r.passed,r.aggregate_return_pct,r.positive_fold_ratio,-r.max_drawdown_pct),reverse=True)

def cost_stress(bars, fast=12, slow=40, scenarios=None):
    scenarios=scenarios or ((0.0002,0.0001),(0.0005,0.0002),(0.0010,0.0005),(0.0020,0.0010)); out=[]
    for fee,slip in scenarios:
        r=backtest(bars,fast,slow,fee=fee,slip=slip); out.append({"fee":fee,"slip":slip,**r})
    return out

def demo_research(): return tournament(market(900, seed=19))
from .strategies import trend, mean_reversion, breakout
def strategy_tournament(bars, fee=0.0005, slip=0.0002):
    candidates=[("trend",trend,{"fast":8,"slow":32}),("trend",trend,{"fast":16,"slow":52}),("mean_reversion",mean_reversion,{"window":20,"z":1.5}),("breakout",breakout,{"window":30})]
    rows=[]
    for name,fn,params in candidates:
        sig=fn(bars,**params); r=backtest_signals(bars,sig,fee=fee,slip=slip); rows.append({"name":name,"params":params,**r})
    return sorted(rows,key=lambda r:(r["return_pct"],-r["max_drawdown_pct"]),reverse=True)
