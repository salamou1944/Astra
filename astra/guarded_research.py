from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
import hashlib, json
from .core import Bar
from .evidence_gate import DatasetEvidence, research_gate
from .research import Experiment, ExperimentResult, tournament, walk_forward

@dataclass(frozen=True)
class ResearchEvidence:
    dataset_status: str
    dataset_sha256: str | None
    dataset_rows: int
    experiment: dict
    result: dict | list
    code_fingerprint: str

def _code_fingerprint() -> str:
    root=Path(__file__).resolve().parent
    files=[root/"research.py",root/"validation.py",root/"evidence_gate.py",root/"core.py"]
    h=hashlib.sha256()
    for p in files:
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()

def _require_proven(dataset: DatasetEvidence) -> None:
    gate=research_gate(dataset,minimum_rows=400)
    if not gate["allowed"]: raise RuntimeError(f"research blocked: {gate['reason']}; status={gate['status']}")

def run_guarded_walk_forward(bars: Iterable[Bar], dataset: DatasetEvidence, experiment: Experiment, *, fasts=(6,8,12,16), slows=(24,32,40,52), fee=0.0005, slip=0.0002) -> tuple[ExperimentResult,ResearchEvidence]:
    _require_proven(dataset); result=walk_forward(list(bars),experiment,fasts,slows,fee,slip)
    evidence=ResearchEvidence(dataset.status.value,dataset.sha256,dataset.rows,asdict(experiment),asdict(result),_code_fingerprint())
    return result,evidence

def run_guarded_tournament(bars: Iterable[Bar], dataset: DatasetEvidence, *, fasts=(6,8,12,16), slows=(24,32,40,52), fee=0.0005, slip=0.0002) -> tuple[list[ExperimentResult],ResearchEvidence]:
    _require_proven(dataset); rows=tournament(list(bars),fasts=fasts,slows=slows,fee=fee,slip=slip)
    evidence=ResearchEvidence(dataset.status.value,dataset.sha256,dataset.rows,{"type":"tournament","fasts":list(fasts),"slows":list(slows),"fee":fee,"slip":slip},[asdict(r) for r in rows],_code_fingerprint())
    return rows,evidence

def write_research_evidence(path: str|Path,evidence: ResearchEvidence) -> None:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(asdict(evidence),indent=2,sort_keys=True),encoding="utf-8")
