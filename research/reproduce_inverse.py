"""Run physical device generation and search in a new isolated directory."""
from pathlib import Path
from datetime import datetime,timezone
import os,shutil,subprocess,sys
root=Path(__file__).resolve().parents[1];out=root/'reruns'/('inverse_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir(parents=True)
shutil.copytree(root/'research',out/'research',ignore=shutil.ignore_patterns('__pycache__'))
(out/'results').mkdir();(out/'models').mkdir()
for script in ['inverse_design.py','export_surrogate.py']:subprocess.run([sys.executable,str(out/'research'/script)],cwd=out,env={**os.environ,'OPENBLAS_NUM_THREADS':'1'},check=True)
print('Preserved rerun:',out)
