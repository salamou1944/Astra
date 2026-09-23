from pathlib import Path
from astra.data import load_csv, audit_bars
from astra.provenance import sha256_file
from astra.validation import purged_walk_forward_splits, assert_no_future_leakage
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'data/fixtures/alpaca_btc_usd_2022-09-01_2022-09-06.csv'
def test_official_real_market_fixture_loads_and_audits():
    bars=load_csv(FIXTURE); a=audit_bars(bars)
    assert len(bars)==6 and a.status=='PASS'
    assert a.duplicates==a.non_monotonic==a.invalid_ohlc==a.negative_volume==a.naive_timestamps==0
def test_fixture_hash_matches_provenance():
    import json
    rec=json.loads((FIXTURE.parent/'provenance.json').read_text())
    assert rec['status']=='SOURCE_VERIFIED' and rec['sha256']==sha256_file(FIXTURE)
def test_purged_walk_forward_has_embargo_and_no_overlap():
    splits=purged_walk_forward_splits(1000,300,100,100,10)
    assert len(splits)==6 and all(s.train_end + s.embargo == s.test_start for s in splits)
    assert_no_future_leakage(splits)
