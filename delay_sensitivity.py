"""Exploratory deployment stress test: labels arrive after 0, 5, or 20 samples."""
import json
from pathlib import Path
import numpy as np,pandas as pd
from portable_runtime import PortableModel
ROOT=Path(__file__).resolve().parent
def run(a,X,y,keys,delay,positions=None):
 m=PortableModel(a);cfg=a['schedule'];gap=1;next_at=0;pending=[];pred=[];asked=[]
 def feedback(j):
  nonlocal gap,next_at
  surprise=abs(y[j]-pred[j]);z=m.transform(X[j]);m.update_scaled(z,float(y[j]),str(keys[j]))
  if surprise>cfg['threshold']*a['residual_std']:
   gap=cfg['min_gap'];next_at=min(next_at,j+delay)
  else:gap=min(cfg['max_gap'],gap+cfg['step'])
 for i in range(len(y)):
  for due,j in list(pending):
   if due<=i:feedback(j);pending.remove((due,j))
  z=m.transform(X[i]);pred.append(m.predict_scaled(z,str(keys[i])))
  ask=i>=next_at if positions is None else i in positions
  if ask:
   asked.append(i)
   if delay==0:feedback(i)
   else:pending.append((i+delay,i))
   next_at=i+gap
 err=np.abs(y-np.array(pred));return {'rmse':float(np.sqrt(np.mean(err**2))),'p90':float(np.quantile(err,.9)),'queries':len(asked),'n':len(y)}
rows=[]
for ds in [1,2]:
 a=json.loads((ROOT/f'models/reflex_{ds}.json').read_text());d=np.load(ROOT/f'models/replay_{ds}.npz',allow_pickle=False);X,y,k=d['X'],d['y'],d['keys']
 for delay in [0,5,20]:
  r=run(a,X,y,k,delay);pos=set(np.linspace(0,len(y)-1,r['queries']).round().astype(int));b=run(a,X,y,k,delay,pos)
  rows.extend([dict(dataset=ds,delay_samples=delay,method='event_triggered',**r),dict(dataset=ds,delay_samples=delay,method='same_count_uniform',**b)])
pd.DataFrame(rows).to_csv(ROOT/'results/delay_sensitivity.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
