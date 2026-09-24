from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

sys.path.insert(0, ".")
import scripts.astra_bot as bot


def _bars(n=40):
    return [
        bot.Bar(
            ts=datetime(2026, 1, 1 + i, tzinfo=timezone.utc),
            open=100 + i,
            high=101 + i,
            low=99 + i,
            close=100 + i,
            volume=10,
        )
        for i in range(n)
    ]


def test_bot_defaults_to_paper_and_never_authorizes_live():
    bars = _bars()
    with patch.object(bot, "fetch_ohlc", return_value=bars):
        snap = bot.run_once(previous_signal=0, quantity=Decimal("0.001"))
    assert snap.mode == "PAPER"
    assert snap.live_order_submitted is False
    assert snap.observed_bars == 40
    assert snap.intent_created is True
    assert snap.paper_position == "0.001"


def test_bot_rejects_live_environment():
    with patch.dict(os.environ, {"ASTRA_LIVE_TRADING": "1"}):
        try:
            bot.main()
        except SystemExit as exc:
            assert "refuses live mode" in str(exc)
        else:
            raise AssertionError("live mode was not rejected")


def test_bot_snapshot_is_serializable():
    bars = _bars()
    with patch.object(bot, "fetch_ohlc", return_value=bars):
        snap = bot.run_once(previous_signal=1)
    json.dumps(snap.__dict__)
