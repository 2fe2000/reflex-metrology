"""Re-run in an isolated directory without overwriting first-run evidence."""
import os,shutil,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
out=ROOT/'reruns'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out.mkdir(parents=True)
for p in ROOT.glob('*.py'):shutil.copy2(p,out/p.name)
for name in ['protocol.json','protocol_v2.json']:shutil.copy2(ROOT/name,out/name)
(out/'data').symlink_to(ROOT/'data',target_is_directory=True);(out/'external').symlink_to(ROOT/'external',target_is_directory=True);(out/'results').mkdir()
env={**os.environ,'OPENBLAS_NUM_THREADS':'4','OMP_NUM_THREADS':'4'}
commands=[['benchmark.py','develop'],['benchmark.py','test'],['stream_benchmark.py','fit','--dataset','1'],['stream_benchmark.py','fit','--dataset','2'],['stream_benchmark.py','final','--dataset','1'],['stream_benchmark.py','final','--dataset','2'],['burst_exploration.py'],['portable_runtime.py'],['delay_sensitivity.py']]
for command in commands:
 print('RUN',*command,flush=True);subprocess.run([sys.executable,*command],cwd=out,env=env,check=True)
print('Preserved independent rerun:',out)
