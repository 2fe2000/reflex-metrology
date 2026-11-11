"""v5: stress-augmented DEVELOPMENT selection; preserve the failed v4 evidence."""
import argparse,copy,hashlib,itertools,json,time
from pathlib import Path
import numpy as np,pandas as pd
from delay_benchmark import load_artifact,prepare,run
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/v5';OUT.mkdir(exist_ok=True)

def scenarios(p,sigma):
    n=len(p['y']);t=np.arange(n);out=[('original',p)]
    for name,offset in [('step_up',np.where(t>=n//2,8*sigma,0.)),('step_down',np.where(t>=n//2,-8*sigma,0.)),('pulse',np.where((t>=n//3)&(t<2*n//3),4*sigma,0.)),('ramp',np.linspace(0,8*sigma,n))]:
        q={**p,'y':p['y']+offset};out.append((name,q))
    return out

def grids(method,sigma):
    if method=='ema':return [{'rate':r} for r in [.02,.05,.1,.2,.4,.7,1.]]
    if method=='reset_ema':return [dict(rate=r,threshold=h,confirm=c,noise_std=sigma) for r,h,c in itertools.product([.02,.1,.4],[2.,3.,4.,6.],[1,2])]
    return [dict(dim=0,context=context,q=q,trend=t,prior=1.,threshold=h,confirm=c,noise_std=sigma) for context,q,t,h,c in itertools.product([False,True],[.0001,.001,.01],[False,True],[2.,3.,4.,6.],[1,2])]

def develop(ds):
    from stream_benchmark import bundle
    target=OUT/f'locked_{ds}.json'
    if target.exists():raise SystemExit('Already locked.')
    a=load_artifact(ds);spec=json.loads((ROOT/f'results/v4/locked_{ds}.json').read_text())['spec']
    data=bundle(ds,['valid','test']);dev=tuple(np.concatenate([data['valid'][i],data['test'][i]]) for i in range(3))
    p=prepare(dev,a,spec);packs=scenarios(p,a['residual_std']);reference={};records=[];selected={}
    for name,pack in packs:
        for delay in [5,20]:
            for phase in [0,2]:reference[(name,delay,phase)]=run(pack,a,'grape',{},delay,phase)['rmse']
    for method in ['ema','reset_ema','adaptive_timestamped']:
        candidates=[]
        for cid,cfg in enumerate(grids(method,a['residual_std'])):
            scores=[];plain=[]
            for name,pack in packs:
                for delay in [5,20]:
                    for phase in [0,2]:
                        r=run(pack,a,method,cfg,delay,phase);ratio=r['rmse']/reference[(name,delay,phase)];scores.append(ratio)
                        if name=='original':plain.append(ratio)
            result={'config':cfg,'score':float(np.mean(scores)),'original_ratio':float(np.mean(plain))}
            candidates.append(result);records.append({'method':method,'candidate':cid,**result,'config':json.dumps(cfg)})
        # Guard against buying robustness by materially sacrificing the ordinary dev stream.
        feasible=[r for r in candidates if r['original_ratio']<=1.05]
        selected[method]=min(feasible or candidates,key=lambda r:r['score']);selected[method]['ordinary_guard_pass']=bool(feasible)
        print(ds,method,selected[method],flush=True)
    lock={'dataset':ds,'spec':spec,'selected':selected,'protocol_sha256':hashlib.sha256((ROOT/'protocol_v5.json').read_bytes()).hexdigest(),'locked_at':time.time(),'selection':'Only original valid+test plus predefined synthetic shifts; no unseen loaded during development'}
    target.write_text(json.dumps(lock,indent=2));pd.DataFrame(records).to_csv(OUT/f'development_{ds}.csv',index=False)

def evaluate(ds):
    target=OUT/f'evaluation_{ds}.csv'
    if target.exists():raise SystemExit('Preserving first evaluation.')
    lock=json.loads((OUT/f'locked_{ds}.json').read_text());a=load_artifact(ds);d=np.load(ROOT/f'models/replay_{ds}.npz',allow_pickle=False)
    p=prepare((d['X'],d['y'],d['keys']),a,lock['spec']);rows=[];replays={'truth':d['y']}
    for method in ['grape','ema','reset_ema','adaptive_timestamped']:
        cfg=lock['selected'].get(method,{}).get('config',{})
        for delay in [0,5,20]:
            for phase in range(5):
                row,pred=run(p,a,method,cfg,delay,phase,True);rows.append({'dataset':ds,**row});replays[f'{method}_d{delay}_p{phase}']=pred
    pd.DataFrame(rows).to_csv(target,index=False);np.savez_compressed(OUT/f'predictions_{ds}.npz',**replays)
    print(pd.DataFrame(rows).groupby(['method','delay'])[['rmse','p90','queries']].mean().to_string(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['develop','evaluate']);p.add_argument('--dataset',type=int,required=True);a=p.parse_args();{'develop':develop,'evaluate':evaluate}[a.mode](a.dataset)
