from pathlib import Path
from astra.market_data import download_binance_daily_archive
from astra.dataset_pipeline import validate_csv
def test_public_archive_failure_is_explicit_not_fake():
    r=download_binance_daily_archive('BTCUSDT','2024-01-01',Path('/tmp/astra-v10-test'))
    assert r.status in {'SOURCE_FETCHED','BLOCKED'}
    if r.status=='BLOCKED': assert r.sha256 is None and r.path is None
def test_existing_fixture_validation():
    p=Path('data/fixtures/alpaca_btc_usd_2022-09-01_2022-09-06.csv'); x=validate_csv(p)
    assert x['rows']==6 and x['audit_pass'] is True
