from pathlib import Path
from astra.market_data import fetch_kraken_ohlc
def test_kraken_network_failure_is_explicit(tmp_path,monkeypatch):
    import urllib.request
    def fail(*args,**kwargs): raise OSError('network unavailable')
    monkeypatch.setattr(urllib.request,'urlopen',fail); r=fetch_kraken_ohlc('XBTUSD',1440,tmp_path/'out.csv')
    assert r.status=='BLOCKED' and r.path is None and r.rows==0
def test_research_gate_requires_research_scale_dataset():
    from astra.evidence_gate import DatasetEvidence,research_gate
    d=DatasetEvidence('official_fixture',399,'a'*64,True,True); gate=research_gate(d)
    assert gate['allowed'] is False and gate['reason']=='research_scale_dataset_required:400_rows'
def test_research_gate_allows_research_scale_dataset():
    from astra.evidence_gate import DatasetEvidence,research_gate
    d=DatasetEvidence('official_archive',400,'b'*64,True,True); gate=research_gate(d)
    assert gate['allowed'] is True and gate['status']=='PROVEN'
