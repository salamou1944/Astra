from astra.core import market
from astra.research import Experiment, walk_forward_candidate, tournament
from astra.risk import RiskGuardian, RiskLimits
def test_candidate_walk_forward_does_not_reselect_parameters():
    r=walk_forward_candidate(market(900,seed=19),Experiment(6,40,300,100,100),6,40)
    assert r.folds==6 and r.chosen_by_fold==[(6,40)]*6
def test_tournament_rows_are_independent_candidates():
    rows=tournament(market(900,seed=19),fasts=(6,8),slows=(24,32))
    assert len(rows)==4 and {(r.fast,r.slow) for r in rows}=={(6,24),(6,32),(8,24),(8,32)}
def test_reset_day_resets_high_water_mark():
    g=RiskGuardian(RiskLimits(max_daily_loss=1.0,max_drawdown=0.10)); g.reset_day(100); g.observe(120); g.reset_day(110); x=g.observe(100)
    assert round(x['drawdown'],6)==round((110-100)/110,6) and x['halted'] is False
def test_reset_day_rejects_negative_equity():
    g=RiskGuardian()
    try: g.reset_day(-1)
    except ValueError: return
    assert False
from astra.evidence_gate import DatasetEvidence
from astra.guarded_research import run_guarded_tournament
def test_guarded_tournament_requires_proven_dataset():
    blocked=DatasetEvidence(source="synthetic",rows=900,sha256="x",source_verified=False,locally_verified=True,synthetic=True)
    try: run_guarded_tournament(market(900),blocked)
    except RuntimeError as e:
        assert "research blocked" in str(e); return
    assert False
def test_guarded_tournament_persists_provenance_fingerprint():
    proven=DatasetEvidence(source="verified-fixture",rows=900,sha256="abc",source_verified=True,locally_verified=True,synthetic=False)
    rows,evidence=run_guarded_tournament(market(900),proven,fasts=(6,8),slows=(24,32))
    assert len(rows)==4 and evidence.dataset_status=="PROVEN" and len(evidence.code_fingerprint)==64 and evidence.experiment["type"]=="tournament"
