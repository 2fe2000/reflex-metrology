"""Portable, causal delayed-feedback replay. NumPy only; no sklearn/torch required."""
import json,time
from pathlib import Path
import numpy as np
from portable_runtime import PortableModel
from delay_model import DelayedEnsemble

class DelayedStream:
    def __init__(self,artifact,X,y,keys,delay=5,phase=0):
        self.a=artifact;self.X=X;self.y=y;self.keys=keys;self.delay=delay;self.phase=phase
        self.model=DelayedEnsemble(artifact['base'],artifact['spec'],artifact['config'],artifact['experts']['kalman'],artifact['experts']['regime'])
        self.baseline=PortableModel(artifact['base']);self.i=0;self.history=[];self.queries=0;self.arrived=0;self.last_observed=None
        self.pending={};self.latencies=[]

    def deliver(self,j,now):
        x,experts=self.pending.pop(j);truth=float(self.y[j]);key=str(self.keys[j])
        self.model.observe(x,key,j,truth,experts);self.baseline.update_scaled(x,truth,key)
        self.history[j]['measured']=truth;self.history[j]['arrived_at']=now
        self.arrived+=1;self.last_observed=j

    def advance(self,n=1):
        for _ in range(min(n,len(self.y)-self.i)):
            i=self.i;t=time.perf_counter();j=i-self.delay
            if self.delay>0 and j in self.pending:self.deliver(j,i)
            x=self.baseline.transform(self.X[i]);key=str(self.keys[i])
            pred,experts=self.model.predict(x,key,i);baseline=self.baseline.predict_scaled(x,key)
            request=i%5==self.phase
            self.history.append({'index':i,'prediction':pred,'baseline':baseline,'audit_truth':float(self.y[i]),'query':request,'measured':None,'arrived_at':None,'weights':self.model.weights.tolist()})
            if request:
                self.queries+=1;self.pending[i]=(x,experts)
                if self.delay==0:self.deliver(i,i)
            self.latencies.append((time.perf_counter()-t)*1000);self.i+=1
        y=np.array([h['audit_truth'] for h in self.history]);p=np.array([h['prediction'] for h in self.history]);b=np.array([h['baseline'] for h in self.history])
        return {'version':7,'index':self.i,'total':len(self.y),'delay':self.delay,'phase':self.phase,'queries':self.queries,'arrived':self.arrived,'pending':len(self.pending),
                'rmse':float(np.sqrt(np.mean((y-p)**2))) if len(y) else None,'baseline_rmse':float(np.sqrt(np.mean((y-b)**2))) if len(y) else None,
                'p90':float(np.quantile(np.abs(y-p),.9)) if len(y) else None,'baseline_p90':float(np.quantile(np.abs(y-b),.9)) if len(y) else None,
                'weights':self.model.weights.tolist(),'hypotheses':len(self.model.regime.weights),'state_age':self.i-1-self.last_observed if self.last_observed is not None else None,
                'step_ms_p95':float(np.quantile(self.latencies,.95)) if self.latencies else None,'history':self.history,'done':self.i==len(self.y),
                'note':'Public recorded features; actual local inference. Offline audit truth is not provided to models before a requested label arrives.'}

def export():
    root=Path(__file__).resolve().parent
    for ds in [1,2]:
        lock=json.loads((root/f'results/v7/locked_{ds}.json').read_text());base=json.loads((root/f'models/reflex_{ds}.json').read_text())
        artifact={'version':7,'dataset':ds,'base':base,'spec':lock['spec'],'config':lock['selected']['config'],'experts':lock['experts']}
        p=root/f'models/reflex_delayed_{ds}.json';p.write_text(json.dumps(artifact,separators=(',',':')));print(p.name,p.stat().st_size)

if __name__=='__main__':export()
