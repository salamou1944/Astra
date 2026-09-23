from __future__ import annotations
import hashlib, json
from pathlib import Path
from .data import load_csv, audit_bars


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    p = Path(path)
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def validate_csv(path: str | Path) -> dict:
    bars = load_csv(path)
    audit = audit_bars(bars)
    return {
        "rows": len(bars),
        "audit_pass": audit.status == "PASS",
        "audit": audit.__dict__,
        "sha256": sha256_file(path),
    }


def write_manifest(
    path: str | Path,
    result: dict,
    source_url: str,
    symbol: str,
    interval: str,
    *,
    source: str | None = None,
    generated_by: str = "ASTRA",
) -> None:
    """Persist truthful provenance; source identity is never hardcoded."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    source_name = source or source_url.split("/")[2]
    payload = {
        "dataset_id": f"{source_name.lower()}-{symbol.lower()}-{interval}",
        "symbol": symbol,
        "interval": interval,
        "source": source_name,
        "source_url": source_url,
        "status": result.get("status"),
        "rows": result.get("rows"),
        "sha256": result.get("sha256"),
        "audit": result.get("audit"),
        "generated_by": generated_by,
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
