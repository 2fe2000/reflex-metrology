import json,platform,subprocess,time
from pathlib import Path
import numpy as np
from portable_runtime import PortableModel,LiveStream
ROOT=Path(__file__).resolve().parent
out={'host':platform.node(),'platform':platform.platform(),'numpy':np.__version__,'scope':'feature-vector preprocessing + single-sample prediction; excludes sensor feature extraction, network and instrument delay','models':{}}
try:out['chip']=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip()
except Exception:out['chip']=platform.processor()
for ds in [1,2]:
 a=json.loads((ROOT/f'models/reflex_{ds}.json').read_text());data=np.load(ROOT/f'models/replay_{ds}.npz',allow_pickle=False);X=data['X'];y=data['y'];keys=data['keys'];m=PortableModel(a);lat=[]
 for j in range(2200):
  i=j%len(X);t=time.perf_counter_ns();x=m.transform(X[i]);p=m.predict_scaled(x,str(keys[i]));elapsed=(time.perf_counter_ns()-t)/1e6
  if j>=200:lat.append(elapsed)
 s=LiveStream(a,X,y,keys);t=time.perf_counter();state=s.advance(len(y));duration=time.perf_counter()-t
 out['models'][str(ds)]={'model_bytes':(ROOT/f'models/reflex_{ds}.json').stat().st_size,'n_timed':len(lat),'predict_ms_p50':float(np.quantile(lat,.5)),'predict_ms_p95':float(np.quantile(lat,.95)),'full_stream_seconds':duration,'queries':state['queries'],'rmse':state['rmse'],'prediction_sha256':__import__('hashlib').sha256(np.array([h['prediction'] for h in state['history']],dtype='<f8').tobytes()).hexdigest()}
print(json.dumps(out,indent=2))
