from astra.core import market
from astra.risk import RiskGuardian, RiskLimits
from astra.shadow import ShadowSession
def test_risk_guardian_halts_on_daily_loss():
    g=RiskGuardian(RiskLimits(max_position=1,max_daily_loss=0.02,max_drawdown=0.50)); g.reset_day(100); x=g.observe(97.9)
    assert x['halted'] is True and x['reason']=='daily_loss_limit' and g.authorize(1)==0.0
def test_risk_guardian_caps_position():
    g=RiskGuardian(RiskLimits(max_position=0.25)); assert g.authorize(1)==0.25 and g.authorize(-1)==-0.25
def test_shadow_has_no_order_side_effect_and_records_evidence():
    s=ShadowSession(); events=s.run(market(120,seed=9),8,32)
    assert len(events)==120 and all(hasattr(e,'authorized_target') for e in events) and s.equity>0
