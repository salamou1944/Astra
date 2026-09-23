import unittest

from astra.data import OHLCV, audit_market_quality


class DataQualityTests(unittest.TestCase):
    def test_detects_missing_daily_candle(self):
        bars = [
            OHLCV("2026-09-20T00:00:00Z", 1, 2, 1, 1.5),
            OHLCV("2026-09-22T00:00:00Z", 1.5, 2, 1, 1.8),
        ]
        result = audit_market_quality(bars, interval_seconds=86400)
        self.assertEqual(result["gap_count"], 1)
        self.assertEqual(result["status"], "FAIL")

    def test_clean_series_passes(self):
        bars = [
            OHLCV("2026-09-20T00:00:00Z", 1, 2, 1, 1.5),
            OHLCV("2026-09-21T00:00:00Z", 1.5, 2, 1, 1.8),
        ]
        result = audit_market_quality(bars, interval_seconds=86400)
        self.assertEqual(result["gap_count"], 0)
        self.assertEqual(result["status"], "PASS")

    def test_detects_explicit_return_outlier(self):
        bars = [
            OHLCV("2026-09-20T00:00:00Z", 100, 101, 99, 100),
            OHLCV("2026-09-21T00:00:00Z", 200, 201, 199, 200),
        ]
        result = audit_market_quality(bars, interval_seconds=86400, max_return=0.25)
        self.assertEqual(result["outlier_count"], 1)
        self.assertEqual(result["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
