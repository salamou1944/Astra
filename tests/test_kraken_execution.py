import unittest
from unittest.mock import patch

from astra.execution.kraken import KrakenExecutionConfig, KrakenExecutionError, KrakenSpotExecutor
from astra.execution.safety import ExecutionGate, KillSwitch


class KrakenExecutionSafetyTests(unittest.TestCase):
    def test_default_is_off(self):
        ex = KrakenSpotExecutor(KrakenExecutionConfig(api_key="", api_secret=""))
        result = ex.submit_if_authorized(
            pair="XBTUSD", side="buy", ordertype="market", volume="0.0001"
        )
        self.assertFalse(result["submitted"])
        self.assertEqual(result["mode"], "OFF")

    def test_live_requires_credentials(self):
        with self.assertRaises(KrakenExecutionError):
            KrakenSpotExecutor(KrakenExecutionConfig(api_key="", api_secret="", live_enabled=True))

    def test_order_validation(self):
        ex = KrakenSpotExecutor(KrakenExecutionConfig(api_key="", api_secret=""))
        with self.assertRaises(ValueError):
            ex.build_add_order(pair="XBTUSD", side="buy", ordertype="market", volume="0")
        with self.assertRaises(ValueError):
            ex.build_add_order(pair="XBTUSD", side="hold", ordertype="market", volume="1")

    def test_withdrawal_capability_does_not_exist(self):
        self.assertFalse(hasattr(KrakenSpotExecutor, "withdraw"))

    def test_private_methods_are_blocked_when_off(self):
        ex = KrakenSpotExecutor(KrakenExecutionConfig(api_key="", api_secret=""))
        for method, args in [
            ("query_balance", {}), ("query_open_orders", {}),
            ("query_orders", {}), ("cancel_order", {"txid": "x"}),
        ]:
            with self.subTest(method=method):
                with self.assertRaises(KrakenExecutionError):
                    getattr(ex, method)(**args)

    def test_direct_live_submission_is_blocked(self):
        ex = KrakenSpotExecutor(KrakenExecutionConfig(
            api_key="key", api_secret="c2VjcmV0", live_enabled=True
        ))
        with self.assertRaises(KrakenExecutionError):
            ex.submit_order(pair="XBTUSD", side="buy", ordertype="market", volume="0.0001")

    def test_live_submission_requires_gate_and_all_checks(self):
        ex = KrakenSpotExecutor(KrakenExecutionConfig(
            api_key="key", api_secret="c2VjcmV0", live_enabled=True
        ))
        gate = ExecutionGate(KillSwitch())
        blocked = ex.submit_if_authorized(
            gate=gate, data_valid=True, strategy_valid=True, risk_valid=True,
            execution_valid=True, reconciliation_valid=True, human_approval=False,
            pair="XBTUSD", side="buy", ordertype="market", volume="0.0001",
        )
        self.assertFalse(blocked["submitted"])
        self.assertEqual(blocked["mode"], "LIVE_BLOCKED")

    @patch("astra.execution.kraken.KrakenSpotExecutor._submit_order", return_value={"txid": ["T"]})
    def test_authorized_live_submission_reaches_only_private_submit(self, submit):
        ex = KrakenSpotExecutor(KrakenExecutionConfig(
            api_key="key", api_secret="c2VjcmV0", live_enabled=True
        ))
        gate = ExecutionGate(KillSwitch())
        result = ex.submit_if_authorized(
            gate=gate, data_valid=True, strategy_valid=True, risk_valid=True,
            execution_valid=True, reconciliation_valid=True, human_approval=True,
            pair="XBTUSD", side="buy", ordertype="market", volume="0.0001",
        )
        self.assertTrue(result["submitted"])
        submit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
