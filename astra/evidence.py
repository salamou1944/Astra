from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from datetime import datetime, timezone

@dataclass
class EvidenceRecord:
    name: str
    status: str
    maturity: str
    detail: str

class EvidenceLedger:
    def __init__(self): self.records=[]
    def add(self, name, status, detail, maturity="IMPLEMENTED"):
        self.records.append(EvidenceRecord(name,status,maturity,detail))
    def save(self, path):
        payload={"generated_at":datetime.now(timezone.utc).isoformat(),"records":[asdict(r) for r in self.records]}
        p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
