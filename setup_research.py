"""Fetch pinned public baseline and CMP manifest for reproducible research."""
import json,subprocess
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parent;dest=ROOT/'external/GRAPE';sha='cce2d27a092abd9e397d7739e4beb6dfe0ae145e'
if not dest.exists():subprocess.run(['git','clone','https://github.com/cheonwoolee/GRAPE.git',str(dest)],check=True)
subprocess.run(['git','-C',str(dest),'checkout',sha],check=True)
tree=ROOT/'data/source_tree.json';tree.parent.mkdir(exist_ok=True)
if not tree.exists():
 r=requests.get('https://api.github.com/repos/akangel0307/PHM-Data-Challenge/git/trees/master?recursive=1',timeout=30);r.raise_for_status()
 paths=[{'path':x['path'],'size':x.get('size',0)} for x in r.json()['tree'] if '2016 PHM' in x['path'] and x['type']=='blob'];tree.write_text(json.dumps(paths))
print('Pinned baseline and public CMP source manifest ready.')
