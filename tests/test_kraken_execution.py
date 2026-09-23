import unittest
from astra.execution.kraken import KrakenExecutionConfig, KrakenExecutionError, KrakenSpotExecutor

class KrakenExecutionSafetyTests(unittest.TestCase):
    def test_default_is_off(self):
        ex = KrakenSpotExecutor(KrakenExecutionConfig(api_key="", api_secret=""))
        result = ex.submit_if_authorized(pair="XBTUSD", side="buy", ordertype="market", volume="0.0001")
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
            ("query_balance", {}),
            ("query_open_orders", {}),
            ("query_orders", {}),
            ("cancel_order", {"txid": "x"}),
        ]:
            with self.subTest(method=method):
                with self.assertRaises(KrakenExecutionError):
                    getattr(ex, method)(**args)

if __name__ == "__main__":
    unittest.main()
