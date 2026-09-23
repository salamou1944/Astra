from astra.alpaca import fetch_crypto_bars
def test_alpaca_validation():
    try: fetch_crypto_bars(symbol="BTCUSD")
    except ValueError as e: assert "BTC/USD" in str(e)
    else: assert False
def test_alpaca_limit_validation():
    try: fetch_crypto_bars(limit=10001)
    except ValueError: return
    assert False
