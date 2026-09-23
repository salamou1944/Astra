import unittest
from decimal import Decimal

from astra.execution.ledger import OrderIntent
from astra.execution.lifecycle import PaperExecutionLifecycle
from astra.execution.paper import OrderStatus, PaperBroker


class PaperExecutionLifecycleTests(unittest.TestCase):
    def _intent(self):
        return OrderIntent.create(
            symbol="BTCUSD",
            side="buy",
            quantity="1",
            order_type="market",
            strategy_id="momentum-30",
            signal_timestamp="2026-09-23T00:00:00Z",
        )

    def test_submit_is_idempotent(self):
        lifecycle = PaperExecutionLifecycle(broker=PaperBroker())
        intent = self._intent()
        first = lifecycle.submit_intent(intent)
        second = lifecycle.submit_intent(intent)
        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)
        self.assertEqual(first.order_id, second.order_id)
        self.assertEqual(len(lifecycle.broker.orders), 1)
        self.assertEqual(
            [e.event_type for e in lifecycle.ledger.events],
            ["intent_created", "accepted"],
        )

    def test_fill_lifecycle_is_recorded_and_reconciles(self):
        lifecycle = PaperExecutionLifecycle(broker=PaperBroker())
        intent = self._intent()
        result = lifecycle.submit_intent(intent)
        changed = lifecycle.advance(symbol="BTCUSD", market_price=Decimal("100"))
        self.assertEqual(result.status, OrderStatus.ACCEPTED.value)
        self.assertEqual(changed[0].status, OrderStatus.FILLED)
        self.assertTrue(lifecycle.reconcile()[0])
        self.assertEqual(
            [e.event_type for e in lifecycle.ledger.events],
            ["intent_created", "accepted", "filled"],
        )

    def test_mapping_tamper_fails_reconciliation(self):
        lifecycle = PaperExecutionLifecycle(broker=PaperBroker())
        lifecycle.submit_intent(self._intent())
        lifecycle._intent_to_order.clear()
        ok, mismatches = lifecycle.reconcile()
        self.assertFalse(ok)
        self.assertIn("paper_order_mapping_mismatch", mismatches)


if __name__ == "__main__":
    unittest.main()
