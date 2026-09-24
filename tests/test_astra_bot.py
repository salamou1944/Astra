from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch

sys.path.insert(0, ".")
import scripts.astra_bot as bot


def _bars(n=40):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        bot.Bar(
            t=int((start + timedelta(days=i)).timestamp()),
            close=100 + i,
        )
        for i in range(n)
    ]


class AstraBotTests(unittest.TestCase):
    def test_bot_defaults_to_paper_and_never_authorizes_live(self):
        bars = _bars()
        with patch.object(bot, "fetch_ohlc", return_value=bars):
            snap = bot.run_once(previous_signal=0, quantity=Decimal("0.001"))
        self.assertEqual(snap.mode, "PAPER")
        self.assertFalse(snap.live_order_submitted)
        self.assertEqual(snap.observed_bars, 40)
        self.assertTrue(snap.intent_created)
        self.assertEqual(snap.paper_position, "0.001")

    def test_bot_rejects_live_environment(self):
        with patch.dict(os.environ, {"ASTRA_LIVE_TRADING": "1"}):
            with self.assertRaisesRegex(SystemExit, "refuses live mode"):
                bot.main()

    def test_bot_snapshot_is_serializable(self):
        bars = _bars()
        with patch.object(bot, "fetch_ohlc", return_value=bars):
            snap = bot.run_once(previous_signal=1)
        json.dumps(snap.__dict__)


if __name__ == "__main__":
    unittest.main()
