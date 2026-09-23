from pathlib import Path
import json, pytest
from astra.core import market
from astra.evidence_gate import DatasetEvidence
from astra.guarded_research import run_guarded_walk_forward, write_research_evidence
from astra.research import Experiment
def test_guard_blocks_synthetic_research():
    dataset=DatasetEvidence("synthetic",900,"abc",True,True,synthetic=True)
    with pytest.raises(RuntimeError,match="research blocked"): run_guarded_walk_forward(market(900),dataset,Experiment(12,40))
def test_guard_allows_verified_dataset_and_persists_evidence(tmp_path:Path):
    dataset=DatasetEvidence("official_fixture",900,"a"*64,True,True,synthetic=False)
    result,evidence=run_guarded_walk_forward(market(900),dataset,Experiment(12,40),fasts=(8,12),slows=(32,40))
    assert result.folds>0 and evidence.dataset_status=="PROVEN" and evidence.dataset_sha256=="a"*64
    out=tmp_path/"evidence.json"; write_research_evidence(out,evidence); payload=json.loads(out.read_text())
    assert payload["dataset_rows"]==900 and payload["result"]["folds"]==result.folds
