"""Fetch public PHM 2016 CMP mirror; record hashes and provenance."""
import concurrent.futures, hashlib, json, time
from pathlib import Path
from urllib.parse import quote
import requests

ROOT=Path(__file__).resolve().parent
paths=json.loads((ROOT/'data/source_tree.json').read_text())
selected=[p for p in paths if p['path'].endswith('.csv') and '__MACOSX' not in p['path'] and 'PHM16TestValidationAnswers' not in p['path']]
def fetch(item):
    path=item['path']; dest=ROOT/'data/raw'/path.split('data/2016 PHM Data Challenge/',1)[1]
    dest.parent.mkdir(parents=True,exist_ok=True)
    url='https://raw.githubusercontent.com/akangel0307/PHM-Data-Challenge/master/'+quote(path)
    if not dest.exists():
        for attempt in range(4):
            try:
                r=requests.get(url,timeout=45);r.raise_for_status();dest.write_bytes(r.content);break
            except Exception:
                if attempt==3:raise
                time.sleep(attempt+1)
    content=dest.read_bytes()
    return {'file':str(dest.relative_to(ROOT)), 'source':url,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    manifest=[]
    for i,item in enumerate(pool.map(fetch,selected),1):
        manifest.append(item)
        if i%50==0: print('downloaded',i,'/',len(selected),flush=True)
(ROOT/'data/manifest.json').write_text(json.dumps(manifest,indent=2))
print('DONE',len(manifest),sum(x['bytes'] for x in manifest),flush=True)
