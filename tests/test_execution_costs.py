from astra.core import Bar, backtest
def test_slippage_and_fees_reduce_strategy_result():
    bars=[Bar(i, 100.0 + i) for i in range(120)]
    free=backtest(bars, fee=0.0, slip=0.0); costly=backtest(bars, fee=0.01, slip=0.01)
    assert costly['return_pct'] < free['return_pct']
def test_execution_costs_are_deterministic():
    bars=[Bar(i, 100.0 + (i % 7)) for i in range(120)]
    a=backtest(bars, fee=0.001, slip=0.0005); b=backtest(bars, fee=0.001, slip=0.0005)
    assert a == b
