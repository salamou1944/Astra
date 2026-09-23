import unittest

from astra.execution.ledger import ExecutionLedger, OrderIntent


class ExecutionLedgerTests(unittest.TestCase):
    def test_identical_intent_has_stable_id(self):
        kwargs = dict(
            symbol="btcusd", side="BUY", quantity="1.25",
            order_type="MARKET", strategy_id="momentum-30",
            signal_timestamp="2026-09-23T00:00:00Z",
        )
        a = OrderIntent.create(**kwargs)
        b = OrderIntent.create(**kwargs)
        self.assertEqual(a.intent_id, b.intent_id)

    def test_duplicate_intent_is_rejected(self):
        ledger = ExecutionLedger()
        intent = OrderIntent.create(
            symbol="BTCUSD", side="buy", quantity="1",
            order_type="market", strategy_id="s", signal_timestamp="t",
        )
        self.assertTrue(ledger.register_intent(intent))
        self.assertFalse(ledger.register_intent(intent))
        self.assertEqual(len(ledger.events), 1)

    def test_unknown_intent_cannot_append_event(self):
        ledger = ExecutionLedger()
        with self.assertRaises(KeyError):
            ledger.append(intent_id="intent-missing", event_type="submitted", payload={})

    def test_events_are_sequence_ordered(self):
        ledger = ExecutionLedger()
        intent = OrderIntent.create(
            symbol="BTCUSD", side="buy", quantity="1",
            order_type="market", strategy_id="s", signal_timestamp="t",
        )
        ledger.register_intent(intent)
        ledger.append(intent_id=intent.intent_id, event_type="submitted", payload={"order_id": "x"})
        ledger.append(intent_id=intent.intent_id, event_type="filled", payload={"qty": "1"})
        self.assertEqual([e.sequence for e in ledger.events], [1, 2, 3])
        self.assertTrue(ledger.contains_event(intent.intent_id, "filled"))


if __name__ == "__main__":
    unittest.main()
