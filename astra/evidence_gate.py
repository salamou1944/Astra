from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class EvidenceStatus(str, Enum):
    IMPLEMENTED = 'IMPLEMENTED'
    PROVEN = 'PROVEN'
    BLOCKED = 'BLOCKED'
    UNVERIFIED = 'UNVERIFIED'
    FAILED = 'FAILED'

@dataclass(frozen=True)
class DatasetEvidence:
    source: str
    rows: int
    sha256: str | None
    source_verified: bool
    locally_verified: bool
    synthetic: bool = False

    @property
    def status(self) -> EvidenceStatus:
        if self.synthetic:
            return EvidenceStatus.UNVERIFIED
        if self.source_verified and self.locally_verified and self.rows > 0 and self.sha256:
            return EvidenceStatus.PROVEN
        return EvidenceStatus.UNVERIFIED

def research_gate(dataset: DatasetEvidence, *, minimum_rows: int = 400) -> dict:
    if dataset.synthetic:
        allowed = False; reason = "real_locally_verified_dataset_required"
    elif not (dataset.source_verified and dataset.locally_verified and dataset.sha256):
        allowed = False; reason = "real_locally_verified_dataset_required"
    elif dataset.rows < minimum_rows:
        allowed = False; reason = f"research_scale_dataset_required:{minimum_rows}_rows"
    else:
        allowed = True; reason = None
    return {'allowed': allowed,'status': dataset.status.value if allowed else EvidenceStatus.UNVERIFIED.value,'reason': reason,'minimum_rows': minimum_rows,'rows': dataset.rows}
