from astra.core import market,backtest,adversary,PaperBroker
def test_market_deterministic(): assert [b.close for b in market(10)] == [b.close for b in market(10)]
def test_backtest_deterministic(): assert backtest(market()) == backtest(market())
def test_risk_cap():
    b=PaperBroker(); assert b.order(99)==1 and b.order(-99)==-1
def test_adversary():
    a=adversary(market()); assert a['passed'] and a['survival_ratio'] >= 0.8
def test_paper_broker_daily_loss_kill_switch():
    from astra.core import Risk
    b=PaperBroker(Risk(max_position=1.0, max_daily_loss=0.02)); b.order(1); b.mark_equity(0.979)
    assert b.halted and b.position == 0.0
    assert b.order(1) == 0.0
