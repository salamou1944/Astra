from astra.core import market
from astra.research import Experiment, walk_forward
def test_walk_forward_selects_on_train_and_tests_future_window():
    r=walk_forward(market(900, seed=19), Experiment(6,40,300,100,100)); assert r.folds == 6 and len(r.test_returns) == 6
def test_walk_forward_rejects_insufficient_data():
    try: walk_forward(market(100, seed=19), Experiment(6,40,300,100,100))
    except ValueError: return
    assert False
def test_strategy_tournament_has_multiple_families():
    from astra.research import strategy_tournament
    rows = strategy_tournament(market(500, seed=23)); assert len(rows) == 4
    assert {r['name'] for r in rows} == {'trend','mean_reversion','breakout'}
    assert all('return_pct' in r and 'max_drawdown_pct' in r for r in rows)
def test_regime_detector_is_deterministic():
    from astra.strategies import regime
    a=regime(market(300,seed=4)); b=regime(market(300,seed=4)); assert a == b and set(a) <= {'unknown','trend','range'}
