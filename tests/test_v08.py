import json
from unittest.mock import patch
from astra.core import Bar, backtest_signals
from astra.binance import fetch_klines, to_ohlcv
from astra.providers import BinanceProvider
from astra.research import strategy_tournament
class Resp:
    def __init__(self, rows): self.rows=rows
    def __enter__(self): return self
    def __exit__(self,*a): pass
    def __iter__(self): return iter(())
    def read(self): return json.dumps(self.rows).encode()
def test_binance_fixture_adapter_and_pagination():
    rows1=[[100,"1","2","0.5","1.5","10",0,0,0,0,0,0]]; rows2=[[200,"1.5","2.5","1","2","11",0,0,0,0,0,0]]
    def fake(req, timeout=0): return Resp(rows1 if "startTime" not in req.full_url else rows2)
    with patch("astra.binance.urlopen", side_effect=fake):
        f=fetch_klines(limit=1,max_pages=2)
    assert len(f.bars)==2 and f.pages==2 and len(to_ohlcv(f))==2 and to_ohlcv(f)[0].t.endswith("Z")
def test_binance_provider_blocks_cleanly_when_network_fails():
    with patch("astra.binance.urlopen", side_effect=OSError("network blocked")):
        r=BinanceProvider().fetch("BTCUSDT","1d",10)
    assert r.status=="BLOCKED" and "network blocked" in r.detail
def test_strategy_tournament_uses_shared_execution_model():
    bars=[Bar(i,100+i*0.2) for i in range(120)]; rows=strategy_tournament(bars,fee=0.01,slip=0.01)
    assert rows and all("trades" in r for r in rows)
def test_explicit_signal_costs_are_applied():
    bars=[Bar(i,100+i) for i in range(10)]; sig=[0,1,1,0,-1,-1,0,1,0,0]
    free=backtest_signals(bars,sig,fee=0,slip=0); costly=backtest_signals(bars,sig,fee=.01,slip=.01)
    assert costly["return_pct"] < free["return_pct"]
