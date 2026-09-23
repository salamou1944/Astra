import unittest

from astra.execution.safety import ExecutionGate, HaltReason, KillSwitch, reconcile, reconcile_and_trip


class ExecutionSafetyTests(unittest.TestCase):
    def test_kill_switch_fails_closed(self):
        ks = KillSwitch()
        self.assertTrue(ks.authorize())
        ks.trip(HaltReason.API_ERROR)
        self.assertFalse(ks.authorize())
        self.assertEqual(ks.reason, "api_error")

    def test_reconciliation_detects_unknown_and_missing_orders(self):
        result = reconcile(
            local_orders={"a": {"status": "open"}},
            exchange_orders={"b": {"status": "open"}},
            local_positions={"BTC": "1"},
            exchange_positions={"BTC": "1"},
            local_balances={"USD": "100"},
            exchange_balances={"USD": "100"},
        )
        self.assertFalse(result.ok)
        self.assertIn("missing_exchange_order:a", result.mismatches)
        self.assertIn("unknown_exchange_order:b", result.mismatches)

    def test_reconciliation_detects_state_mismatch(self):
        result = reconcile(
            local_orders={}, exchange_orders={},
            local_positions={"BTC": "1"},
            exchange_positions={"BTC": "0"},
            local_balances={"USD": "100"},
            exchange_balances={"USD": "99"},
        )
        self.assertFalse(result.ok)
        self.assertIn("position_mismatch", result.mismatches)
        self.assertIn("balance_mismatch", result.mismatches)


    def test_reconciliation_mismatch_trips_kill_switch_and_blocks_gate(self):
        ks = KillSwitch()
        result = reconcile_and_trip(
            kill_switch=ks,
            local_orders={"a": {"status": "open"}}, exchange_orders={},
            local_positions={"BTC": "1"}, exchange_positions={"BTC": "1"},
            local_balances={"USD": "100"}, exchange_balances={"USD": "100"},
        )
        self.assertFalse(result.ok)
        self.assertTrue(ks.halted)
        self.assertEqual(ks.reason, "reconciliation_failure")
        gate = ExecutionGate(ks)
        self.assertFalse(gate.authorize(
            data_valid=True, strategy_valid=True, risk_valid=True,
            execution_valid=True, reconciliation_valid=True,
            human_approval=True, live_enabled=True,
        ))

    def test_clean_reconciliation_does_not_trip_kill_switch(self):
        ks = KillSwitch()
        result = reconcile_and_trip(
            kill_switch=ks,
            local_orders={"a": {"status": "filled"}}, exchange_orders={"a": {"status": "filled"}},
            local_positions={"BTC": "1"}, exchange_positions={"BTC": "1"},
            local_balances={"USD": "100"}, exchange_balances={"USD": "100"},
        )
        self.assertTrue(result.ok)
        self.assertFalse(ks.halted)

    def test_gate_requires_every_condition_and_human_approval(self):
        ks = KillSwitch()
        gate = ExecutionGate(ks)
        kwargs = dict(
            data_valid=True, strategy_valid=True, risk_valid=True,
            execution_valid=True, reconciliation_valid=True,
            human_approval=True, live_enabled=True,
        )
        self.assertTrue(gate.authorize(**kwargs))
        kwargs["human_approval"] = False
        self.assertFalse(gate.authorize(**kwargs))
        kwargs["human_approval"] = True
        ks.trip(HaltReason.MANUAL)
        self.assertFalse(gate.authorize(**kwargs))

    def test_live_disabled_cannot_pass_even_if_everything_else_is_true(self):
        gate = ExecutionGate(KillSwitch())
        self.assertFalse(gate.authorize(
            data_valid=True, strategy_valid=True, risk_valid=True,
            execution_valid=True, reconciliation_valid=True,
            human_approval=True, live_enabled=False,
        ))


if __name__ == "__main__":
    unittest.main()
