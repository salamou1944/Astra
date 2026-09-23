import unittest
from decimal import Decimal

from astra.execution.paper import OrderStatus, PaperBroker


class PaperBrokerTests(unittest.TestCase):
    def test_market_order_fills_with_fee_and_slippage(self):
        broker = PaperBroker(
            cash=Decimal("1000"), fee_rate=Decimal("0.001"),
            slippage_bps=Decimal("10")
        )
        order = broker.submit(symbol="BTCUSD", side="buy", quantity="1")
        changed = broker.advance(symbol="BTCUSD", market_price="100")
        self.assertEqual(changed[0].status, OrderStatus.FILLED)
        self.assertEqual(order.filled, Decimal("1"))
        self.assertGreater(broker.fees_paid, 0)
        self.assertEqual(broker.positions["BTCUSD"], Decimal("1"))

    def test_partial_fill_is_preserved_across_steps(self):
        broker = PaperBroker(
            cash=Decimal("1000"), max_fill_fraction=Decimal("0.4")
        )
        order = broker.submit(symbol="BTCUSD", side="buy", quantity="1")
        broker.advance(symbol="BTCUSD", market_price="100")
        self.assertEqual(order.status, OrderStatus.PARTIALLY_FILLED)
        self.assertEqual(order.filled, Decimal("0.4"))
        broker.advance(symbol="BTCUSD", market_price="101")
        self.assertEqual(order.status, OrderStatus.PARTIALLY_FILLED)
        self.assertEqual(order.filled, Decimal("0.8"))

    def test_latency_delays_fill(self):
        broker = PaperBroker(cash=Decimal("1000"), latency_steps=2)
        order = broker.submit(symbol="BTCUSD", side="buy", quantity="1")
        self.assertEqual(broker.advance(symbol="BTCUSD", market_price="100"), [])
        self.assertEqual(broker.advance(symbol="BTCUSD", market_price="100"), [])
        self.assertEqual(broker.advance(symbol="BTCUSD", market_price="100")[0].status, OrderStatus.FILLED)
        self.assertEqual(order.status, OrderStatus.FILLED)

    def test_rejection_does_not_change_position(self):
        broker = PaperBroker(cash=Decimal("1000"), reject_next=True)
        order = broker.submit(symbol="BTCUSD", side="buy", quantity="1")
        self.assertEqual(order.status, OrderStatus.REJECTED)
        self.assertEqual(broker.advance(symbol="BTCUSD", market_price="100"), [])
        self.assertEqual(broker.positions, {})

    def test_sell_requires_position(self):
        broker = PaperBroker(cash=Decimal("1000"))
        order = broker.submit(symbol="BTCUSD", side="sell", quantity="1")
        changed = broker.advance(symbol="BTCUSD", market_price="100")
        self.assertEqual(changed[0].status, OrderStatus.REJECTED)

    def test_limit_order_waits_for_market(self):
        broker = PaperBroker(cash=Decimal("1000"))
        order = broker.submit(
            symbol="BTCUSD", side="buy", quantity="1",
            order_type="limit", limit_price="99"
        )
        self.assertEqual(broker.advance(symbol="BTCUSD", market_price="100"), [])
        self.assertEqual(order.status, OrderStatus.ACCEPTED)
        self.assertEqual(broker.advance(symbol="BTCUSD", market_price="98")[0].status, OrderStatus.FILLED)

    def test_cancel_stops_pending_order(self):
        broker = PaperBroker(cash=Decimal("1000"))
        order = broker.submit(
            symbol="BTCUSD", side="buy", quantity="1",
            order_type="limit", limit_price="90"
        )
        broker.cancel(order.order_id)
        changed = broker.advance(symbol="BTCUSD", market_price="100")
        self.assertEqual(changed[0].status, OrderStatus.CANCELED)

    def test_snapshot_is_serializable_state(self):
        broker = PaperBroker(cash=Decimal("1000"))
        broker.submit(symbol="BTCUSD", side="buy", quantity="1")
        broker.advance(symbol="BTCUSD", market_price="100")
        snap = broker.snapshot()
        self.assertEqual(snap["positions"]["BTCUSD"], "1")
        self.assertIn("paper-00000001", snap["orders"])


if __name__ == "__main__":
    unittest.main()
