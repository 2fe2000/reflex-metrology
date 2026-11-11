"""End-to-end CPU model step timing, includes arrived-label updates; excludes sensor extraction/UI."""
import json,subprocess,platform,time,hashlib
from pathlib import Path
import numpy as np
from delayed_runtime import DelayedStream
root=Path(__file__).resolve().parent
out={'chip':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string']).decode().strip(),'numpy':np.__version__,'note':'Single recorded-stream pass, delay5 offset0; p95 step includes inference of candidate+baseline and any label arrival. Excludes raw-sensor feature extraction, instruments, network and UI. Warmup first200 steps excluded.','models':{}}
for ds in [1,2]:
 a=json.loads((root/f'models/reflex_delayed_{ds}.json').read_text());d=np.load(root/f'models/replay_{ds}.npz');s=DelayedStream(a,d['X'],d['y'],d['keys'],5,0);t=time.perf_counter();r=s.advance(len(d['y']));elapsed=time.perf_counter()-t
 out['models'][str(ds)]={'n':r['index'],'rmse':r['rmse'],'p90':r['p90'],'queries':r['queries'],'arrived':r['arrived'],'step_ms_p50':float(np.median(s.latencies[200:])),'step_ms_p95':float(np.quantile(s.latencies[200:],.95)),'full_replay_s':elapsed,'artifact_bytes':(root/f'models/reflex_delayed_{ds}.json').stat().st_size,'posterior_hypotheses':r['hypotheses']}
print(json.dumps(out,indent=2))
