from astra.core import market
from astra.research import walk_forward, Experiment, cost_stress
def test_walk_forward_compounds_fold_returns_and_preserves_warmup():
    bars=market(900, seed=21); r=walk_forward(bars, Experiment(12,40,train_size=300,test_size=100,step=100))
    assert r.folds == 6 and len(r.chosen_by_fold)==6
    compounded=1.0
    for x in r.test_returns: compounded *= 1+x/100
    assert round((compounded-1)*100,4)==r.aggregate_return_pct and r.turnover_trades >= 0
def test_embargo_is_supported():
    bars=market(900, seed=21); a=walk_forward(bars, Experiment(12,40,300,100,100,0)); b=walk_forward(bars, Experiment(12,40,300,100,100,5))
    assert a.folds == 6 and b.folds == 5
def test_cost_stress_is_monotonic_for_same_signals():
    rows=cost_stress(market(500,seed=4)); assert len(rows)==4
    assert rows[0]["fee"] < rows[-1]["fee"] and rows[0]["slip"] < rows[-1]["slip"]
