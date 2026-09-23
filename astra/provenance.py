from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import json
from datetime import datetime, timezone
@dataclass(frozen=True)
class DatasetProvenance:
    dataset_id: str
    source: str
    source_url: str
    retrieved_at: str
    symbol: str
    timeframe: str
    start: str
    end: str
    rows: int
    sha256: str
    status: str
    note: str = ""
def sha256_file(path: str | Path) -> str:
    h=sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def build_provenance(path: str|Path, *, dataset_id: str, source: str, source_url: str, symbol: str, timeframe: str, start: str, end: str, rows: int, status: str, note: str="") -> DatasetProvenance:
    return DatasetProvenance(dataset_id=dataset_id,source=source,source_url=source_url,retrieved_at=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),symbol=symbol,timeframe=timeframe,start=start,end=end,rows=rows,sha256=sha256_file(path),status=status,note=note)
def write_provenance(record: DatasetProvenance, path: str|Path) -> None:
    Path(path).write_text(json.dumps(asdict(record),indent=2)+"\n",encoding="utf-8")
