from astra.data import OHLCV, audit_bars, validate_bars
def sample():
    return [OHLCV("2026-01-01T00:00:00Z", 10, 11, 9, 10.5, 3), OHLCV("2026-01-02T00:00:00Z", 10.5, 12, 10, 11.5, 4)]
def test_data_audit_passes_clean_utc_data():
    a = audit_bars(sample()); assert a.status == "PASS" and a.bars == 2 and a.naive_timestamps == 0
def test_validate_rejects_naive_timestamp():
    bad = [OHLCV("2026-01-01T00:00:00",10,11,9,10), OHLCV("2026-01-02T00:00:00Z",10,11,9,10)]
    try: validate_bars(bad)
    except ValueError as e: assert "timezone" in str(e)
    else: assert False
def test_data_audit_detects_duplicate():
    b = sample(); b.append(b[-1]); a = audit_bars(b)
    assert a.duplicates == 1 and a.status == "FAIL"
