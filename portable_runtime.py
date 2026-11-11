"""NumPy deployment of the public GRAPE equations + REFLEX measurement schedule.
GRAPE algorithm credit: https://github.com/cheonwoolee/GRAPE (Apache-2.0).
This module is an independently written portable implementation, not a new base model.
"""
import json,time
from pathlib import Path
import numpy as np

class PortableModel:
 def __init__(self,artifact):
  self.a=artifact;self.mean=np.array(artifact['mean']);self.scale=np.array(artifact['scale']);self.coef=np.array(artifact['coef'],np.float32)
  self.indices=np.array(artifact['adapter_indices']);self.w=np.zeros(len(self.indices));self.temporal=0.;self.global_mean=0.;self.global_count=0;self.buckets=[{},{},{}]
 def transform(self,x):return (np.nan_to_num(np.asarray(x,float))-self.mean)/self.scale
 def base(self,x):return float(np.asarray(x,np.float32)@self.coef+np.float32(self.a['intercept']))
 def correction(self,key):
  parts=key.rsplit('_',1);ks=[parts[0],parts[1] if len(parts)>1 else '',key];vals=[self.global_mean];weights=[self.global_count/(self.global_count+self.a['n_min'])]
  for b,k in zip(self.buckets,ks):
   if k in b:
    mean,count=b[k];vals.append(mean);weights.append(count/(count+self.a['n_min']))
  return float(np.dot(vals,weights)/sum(weights)) if sum(weights)>1e-12 else 0.
 def predict_scaled(self,x,key):
  raw=self.base(x)+float(self.w@x[self.indices])+self.correction(key)
  clipped=float(np.clip(raw,*self.a['base_bounds']))
  temp=self.temporal if abs(self.temporal)>=self.a['activation_threshold'] else 0.
  return float(np.clip(clipped+temp,*self.a['label_bounds']))
 def update_scaled(self,x,y,key):
  xa=x[self.indices];raw=self.base(x)+float(self.w@xa)+self.correction(key);clipped=float(np.clip(raw,*self.a['base_bounds']))
  yt=float(np.clip(y,*self.a['label_bounds']));yb=float(np.clip(yt,*self.a['base_bounds']))
  self.temporal=.5*self.temporal+.5*(yt-clipped)
  self.w+=self.a['nlms_lr']*(yb-clipped)*xa/(float(xa@xa)+1e-3)
  residual=yb-(self.base(x)+float(self.w@xa));ema=self.a['ema']
  self.global_count+=1;self.global_mean=(1-ema)*self.global_mean+ema*residual
  parts=key.rsplit('_',1);ks=[parts[0],parts[1] if len(parts)>1 else '',key]
  for b,k in zip(self.buckets,ks):
   if k not in b:b[k]=(residual,1)
   else:
    m,c=b[k];b[k]=((1-ema)*m+ema*residual,c+1)

class LiveStream:
 def __init__(self,artifact,X,y,keys,policy='burst'):
  self.model=PortableModel(artifact);self.X=X;self.y=y;self.keys=keys;self.policy=policy;self.i=0;self.next_at=0;self.interval=1;self.history=[];self.queries=0;self.artifact=artifact
 def advance(self,n=1):
  for _ in range(min(n,len(self.y)-self.i)):
   i=self.i;t=time.perf_counter();x=self.model.transform(self.X[i]);base=self.model.base(x);pred=self.model.predict_scaled(x,str(self.keys[i]))
   latency=(time.perf_counter()-t)*1e3
   ask=(i>=self.next_at) if self.policy=='burst' else (self.policy=='all' or self.policy=='uniform' and i%5==0)
   reason='PREDICT';update_ms=0.
   if ask:
    # The label is accessed only after the request decision.
    truth=float(self.y[i]);innovation=abs(truth-pred);cfg=self.artifact['schedule']
    if innovation>cfg['threshold']*self.artifact['residual_std']:
     self.interval=cfg['min_gap'];reason='BURST'
    else:self.interval=min(cfg['max_gap'],self.interval+cfg['step']);reason='STABLE'
    t=time.perf_counter();self.model.update_scaled(x,truth,str(self.keys[i]));update_ms=(time.perf_counter()-t)*1e3
    self.next_at=i+self.interval;self.queries+=1
   self.history.append({'index':i,'prediction':pred,'base':base,'measured':float(self.y[i]) if ask else None,'audit_truth':float(self.y[i]),'query':ask,'reason':reason,'next_gap':self.interval,'predict_ms':latency,'update_ms':update_ms})
   self.i+=1
  y=np.array([h['audit_truth'] for h in self.history]);p=np.array([h['prediction'] for h in self.history]);base=np.array([h['base'] for h in self.history])
  return {'index':self.i,'total':len(self.y),'queries':self.queries,'rmse':float(np.sqrt(np.mean((y-p)**2))) if len(y) else None,'frozen_rmse':float(np.sqrt(np.mean((y-base)**2))) if len(y) else None,'history':self.history,'policy':self.policy,'done':self.i==len(self.y),'mode':'LIVE LOCAL INFERENCE / PUBLIC DATA REPLAY','audit_note':'Audit truth is for offline scoring only; unavailable to request policy before a measurement.'}

def export():
 import pickle
 from stream_benchmark import ROOT,bundle
 out=ROOT/'models';out.mkdir(exist_ok=True)
 for ds in [1,2]:
  with open(ROOT/f'results/stream_model_{ds}.pkl','rb') as f:art=pickle.load(f)
  m=art['grape'];a={'version':1,'dataset':ds,'upstream':'GRAPE cce2d27a092abd9e397d7739e4beb6dfe0ae145e','mean':art['scaler'].mean_.tolist(),'scale':art['scaler'].scale_.tolist(),'coef':m.global_model.coef_.cpu().numpy().tolist(),'intercept':float(m.global_model.intercept_),'adapter_indices':m.adapter_feature_indices.tolist(),'nlms_lr':m.nlms_lr,'ema':m.config.ema,'n_min':m.context.n_min,'activation_threshold':m.global_temporal_adapter.activation_threshold,'base_bounds':[m.base_label_min,m.base_label_max],'label_bounds':[m.label_min,m.label_max],'residual_std':float(np.sqrt(art['noise'])),'schedule':json.loads((ROOT/f'results/burst_config_{ds}.json').read_text())['config']}
  (out/f'reflex_{ds}.json').write_text(json.dumps(a,separators=(',',':')))
  X,y,keys=bundle(ds,['unseen'])['unseen'];np.savez_compressed(out/f'replay_{ds}.npz',X=X,y=y,keys=keys)
  # Equivalence check for full stream, including dynamic measurement schedule.
  s=LiveStream(a,X,y,keys);state=s.advance(len(y));ref=json.loads((ROOT/f'results/burst_replay_{ds}.json').read_text());got=np.array([h['prediction'] for h in state['history']]);err=float(np.max(np.abs(got-np.array(ref['prediction']))))
  assert np.array_equal([h['query'] for h in state['history']],ref['queried'])
  assert err<1e-4,(ds,err)
  print('portable',ds,'max_abs_difference',err,'model_bytes',(out/f'reflex_{ds}.json').stat().st_size,flush=True)
if __name__=='__main__':export()
