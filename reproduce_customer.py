"""Isolated rerun; never overwrite the locked submission evidence."""
from pathlib import Path
from datetime import datetime,timezone
import os,shutil,subprocess,sys
root=Path(__file__).resolve().parent
out=root/'reruns'/('customer_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir(parents=True)
for p in root.glob('*.py'):shutil.copy2(p,out/p.name)
shutil.copy2(root/'protocol_customer_benchmark.json',out/'protocol_customer_benchmark.json')
for name in ['external','models']:(out/name).symlink_to(root/name,target_is_directory=True)
(out/'results').mkdir();env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
for script in ['customer_benchmark.py','summarize_customer.py']:subprocess.run([sys.executable,script],cwd=out,env=env,check=True)
print(out)
