from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json, platform, sys
from pathlib import Path
def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()
def write_run_manifest(path: Path, *, dataset: Path | None, experiment: dict, result: dict, status: str, notes: list[str]):
    payload={'generated_at': datetime.now(timezone.utc).isoformat(),'python': sys.version,'platform': platform.platform(),'status': status,'dataset': None if dataset is None else {'path': str(dataset), 'sha256': sha256_file(dataset)},'experiment': experiment,'result': result,'notes': notes}
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8'); return payload
