from pathlib import Path
from astra.evidence_run import write_run_manifest
def test_manifest_hashes_dataset(tmp_path):
    d=tmp_path/'x.csv'; d.write_text('a,b\n1,2\n',encoding='utf-8'); out=tmp_path/'manifest.json'
    x=write_run_manifest(out,dataset=d,experiment={'name':'unit'},result={'ok':True},status='PROVEN',notes=[])
    assert len(x['dataset']['sha256'])==64 and out.exists()
