"""Locked development and evaluation of a bounded Bayesian regime residual model."""
import argparse,hashlib,itertools,json,time
from pathlib import Path
import numpy as np,pandas as pd
from delay_benchmark import load_artifact,prepare,run
from shift_benchmark import scenarios
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/v6';OUT.mkdir(exist_ok=True)

def develop(ds):
    from stream_benchmark import bundle
    target=OUT/f'locked_{ds}.json'
    if target.exists():raise SystemExit('Already locked.')
    a=load_artifact(ds);spec=json.loads((ROOT/f'results/v4/locked_{ds}.json').read_text())['spec']
    data=bundle(ds,['valid','test']);dev=tuple(np.concatenate([data['valid'][i],data['test'][i]]) for i in range(3))
    p=prepare(dev,a,spec);packs=scenarios(p,a['residual_std']);reference={};candidates=[]
    for name,pack in packs:
        for d in [5,20]:
            for phase in [0,2]:reference[name,d,phase]=run(pack,a,'grape',{},d,phase)['rmse']
    for h,m,w in itertools.product([.002,.01,.05],[1.,1.5,2.],[4.,16.]):
        cfg={'hazard':h,'noise_multiplier':m,'prior_width':w,'noise_std':a['residual_std']};scores=[];plain=[]
        for name,pack in packs:
            for d in [5,20]:
                for phase in [0,2]:
                    row=run(pack,a,'bayesian_regime',cfg,d,phase);ratio=row['rmse']/reference[name,d,phase];scores.append(ratio)
                    if name=='original':plain.append(ratio)
        candidates.append({'config':cfg,'score':float(np.mean(scores)),'original_ratio':float(np.mean(plain))})
    feasible=[r for r in candidates if r['original_ratio']<=1.02];selected=min(feasible or candidates,key=lambda r:r['score']);selected['ordinary_guard_pass']=bool(feasible)
    lock={'dataset':ds,'spec':spec,'selected':selected,'protocol_sha256':hashlib.sha256((ROOT/'protocol_v6.json').read_bytes()).hexdigest(),'locked_at':time.time()}
    target.write_text(json.dumps(lock,indent=2));(OUT/f'development_{ds}.json').write_text(json.dumps(candidates,indent=2));print(ds,selected,flush=True)

def evaluate(ds):
    target=OUT/f'evaluation_{ds}.csv'
    if target.exists():raise SystemExit('Preserving first evaluation.')
    lock=json.loads((OUT/f'locked_{ds}.json').read_text());a=load_artifact(ds);d=np.load(ROOT/f'models/replay_{ds}.npz',allow_pickle=False)
    p=prepare((d['X'],d['y'],d['keys']),a,lock['spec']);rows=[];replays={'truth':d['y']}
    reset=json.loads((ROOT/f'results/v5/locked_{ds}.json').read_text())['selected']['reset_ema']['config']
    for method,cfg in [('grape',{}),('reset_ema',reset),('bayesian_regime',lock['selected']['config'])]:
        for delay in [0,5,20]:
            for phase in range(5):
                row,pred=run(p,a,method,cfg,delay,phase,True);rows.append({'dataset':ds,**row});replays[f'{method}_d{delay}_p{phase}']=pred
    pd.DataFrame(rows).to_csv(target,index=False);np.savez_compressed(OUT/f'predictions_{ds}.npz',**replays)
    print(pd.DataFrame(rows).groupby(['method','delay'])[['rmse','p90','queries']].mean().to_string(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['develop','evaluate']);p.add_argument('--dataset',type=int,required=True);a=p.parse_args();{'develop':develop,'evaluate':evaluate}[a.mode](a.dataset)
