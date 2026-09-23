from astra.evidence_gate import DatasetEvidence, EvidenceStatus, research_gate
def test_synthetic_never_proves_research():
    d = DatasetEvidence('synthetic', 1000, 'a'*64, True, True, synthetic=True); g = research_gate(d)
    assert d.status is EvidenceStatus.UNVERIFIED and g['allowed'] is False
def test_verified_real_dataset_opens_gate():
    d = DatasetEvidence('binance_public_archive', 10000, 'b'*64, True, True); g = research_gate(d)
    assert d.status is EvidenceStatus.PROVEN and g['allowed'] is True
def test_missing_hash_blocks_gate():
    d = DatasetEvidence('binance_public_archive', 10000, None, True, True); assert research_gate(d)['allowed'] is False
def test_research_gate_blocks_small_official_fixture():
    d = DatasetEvidence('alpaca_official_fixture', 6, 'c' * 64, True, True); gate = research_gate(d)
    assert gate['allowed'] is False and gate['reason'] == 'research_scale_dataset_required:400_rows'
