"""Frozen-v7 measurement/accuracy frontier and development-defined error exceedances."""
import json,hashlib,time
from pathlib import Path
import numpy as np,pandas as pd
from portable_runtime import PortableModel
from delay_model import DelayedEnsemble
from delay_benchmark import prepare
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/customer';OUT.mkdir(exist_ok=True)

def simulate(pack,a,method,delay,period,phase):
    base=a['base'];m=PortableModel(base) if method=='grape' else DelayedEnsemble(base,a['spec'],a['config'],a['experts']['kalman'],a['experts']['regime'])
    n=len(pack['y']);pred=np.zeros(n);saved={};asked=np.arange(n)%period==phase
    def update(j):
        x=pack['X'][j];y=float(pack['y'][j]);key=str(pack['keys'][j])
        if method=='grape':m.update_scaled(x,y,key)
        else:m.observe(x,key,j,y,saved.pop(j))
    for i in range(n):
        j=i-delay
        if delay>0 and j>=0 and asked[j]:update(j)
        if method=='grape':pred[i]=m.predict_scaled(pack['X'][i],str(pack['keys'][i]))
        else:
            pred[i],experts=m.predict(pack['X'][i],str(pack['keys'][i]),i)
            if asked[i]:saved[i]=experts
        if delay==0 and asked[i]:update(i)
    return pred,int(asked.sum())

def main():
    from stream_benchmark import bundle
    if (OUT/'metrics.csv').exists():raise SystemExit('Preserving first completed customer benchmark.')
    locks={};dev_data={};artifacts={}
    for ds in [1,2]:
        a=json.loads((ROOT/f'models/reflex_delayed_{ds}.json').read_text());artifacts[ds]=a
        d=bundle(ds,['valid','test']);raw=tuple(np.concatenate([d['valid'][i],d['test'][i]]) for i in range(3));p=prepare(raw,a['base'],a['spec']);dev_data[ds]=p
        for delay in [5,20]:
            preds=np.array([simulate(p,a,'grape',delay,5,phase)[0] for phase in range(5)])
            threshold=float(np.quantile(np.abs(preds-p['y']),.95));locks[f'{ds}_{delay}']=threshold
    (OUT/'threshold_lock.json').write_text(json.dumps({'locked_at':time.time(),'thresholds':locks,'source':'valid+test; GRAPE period5 all offsets; pooled95th absolute-error quantile','protocol_sha256':hashlib.sha256((ROOT/'protocol_customer_benchmark.json').read_bytes()).hexdigest()},indent=2))
    rows=[]
    for ds in [1,2]:
        a=artifacts[ds];d=np.load(ROOT/f'models/replay_{ds}.npz');p=prepare((d['X'],d['y'],d['keys']),a['base'],a['spec']);replays={'truth':d['y']}
        for delay in [5,20]:
            for method in ['grape','reflex']:
                for period in [1,2,5,10,20]:
                    preds=[]
                    for phase in range(period):
                        pred,queries=simulate(p,a,method,delay,period,phase);error=np.abs(pred-p['y']);preds.append(pred)
                        rows.append({'dataset':ds,'delay':delay,'method':method,'period':period,'phase':phase,'n':len(pred),'queries':queries,'rmse':float(np.sqrt(np.mean(error**2))),'p90':float(np.quantile(error,.9)),'threshold':locks[f'{ds}_{delay}'],'error_exceedance_rate':float(np.mean(error>locks[f'{ds}_{delay}']))})
                    replays[f'{method}_d{delay}_p{period}']=np.array(preds)
                    print(ds,delay,method,period,flush=True)
        np.savez_compressed(OUT/f'replays_{ds}.npz',**replays)
    pd.DataFrame(rows).to_csv(OUT/'metrics.csv',index=False)
    means=pd.DataFrame(rows).groupby(['dataset','delay','method','period'])[['queries','rmse','p90','error_exceedance_rate']].mean().reset_index();means.to_csv(OUT/'means.csv',index=False);print(means.to_string(index=False),flush=True)

if __name__=='__main__':main()
