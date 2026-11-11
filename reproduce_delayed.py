"""Reproduce v4-v7 in an isolated run without overwriting original evidence."""
from pathlib import Path
from datetime import datetime,timezone
import os,shutil,subprocess,sys
root=Path(__file__).resolve().parent
out=root/'reruns'/('delayed_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir(parents=True)
for p in root.glob('*.py'):shutil.copy2(p,out/p.name)
for p in root.glob('protocol*.json'):shutil.copy2(p,out/p.name)
for name in ['data','external','models']:(out/name).symlink_to(root/name,target_is_directory=True)
(out/'results').mkdir();env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
for script in ['delay_benchmark.py','shift_benchmark.py','regime_benchmark.py','ensemble_benchmark.py']:
    for mode in ['develop','evaluate']:
        for ds in [1,2]:
            command=[sys.executable,script,mode,'--dataset',str(ds)]
            print('RUN',*command,flush=True);subprocess.run(command,cwd=out,env=env,check=True)
subprocess.run([sys.executable,'summarize_delayed.py'],cwd=out,env=env,check=True)
print('Preserved rerun:',out)
