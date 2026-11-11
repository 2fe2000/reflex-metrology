"""v7: delayed-loss expert weighting. No oracle selection of the best test model."""
import argparse,hashlib,itertools,json,time
from pathlib import Path
import numpy as np,pandas as pd
from portable_runtime import PortableModel
from delay_model import make_model,DelayedEnsemble
from delay_benchmark import load_artifact,prepare,design,run
from shift_benchmark import scenarios
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/v7';OUT.mkdir(exist_ok=True)


def expert_configs(ds):
    k=json.loads((ROOT/f'results/v4/locked_{ds}.json').read_text())['selected']['timestamped']['config']
    b=json.loads((ROOT/f'results/v6/locked_{ds}.json').read_text())['selected']['config']
    return k,b

def simulate(pack,a,cfg,delay,phase,ds,keep=False):
    k,b=expert_configs(ds);model=DelayedEnsemble(a,pack['spec'],cfg,k,b)
    n=len(pack['y']);pred=np.zeros(n);experts=np.zeros((n,3));weights=np.zeros((n,3));arrived=0
    requested=np.arange(n)%5==phase
    def feedback(j):
        nonlocal arrived
        model.observe(pack['X'][j],str(pack['keys'][j]),j,float(pack['y'][j]),experts[j]);arrived+=1
    for i in range(n):
        j=i-delay
        if delay>0 and j>=0 and requested[j]:feedback(j)
        pred[i],experts[i]=model.predict(pack['X'][i],str(pack['keys'][i]),i);weights[i]=model.weights
        if delay==0 and requested[i]:feedback(i)
    e=np.abs(pack['y']-pred)
    row={'dataset':ds,'method':'delayed_ensemble','delay':delay,'phase':phase,'rmse':float(np.sqrt(np.mean(e*e))),'p90':float(np.quantile(e,.9)),'queries':int(requested.sum()),'arrived':arrived,'n':n}
    return (row,pred,weights) if keep else row

def develop(ds):
    from stream_benchmark import bundle
    target=OUT/f'locked_{ds}.json'
    if target.exists():raise SystemExit('Already locked.')
    a=load_artifact(ds);spec=json.loads((ROOT/f'results/v4/locked_{ds}.json').read_text())['spec']
    data=bundle(ds,['valid','test']);dev=tuple(np.concatenate([data['valid'][i],data['test'][i]]) for i in range(3))
    p=prepare(dev,a,spec);packs=scenarios(p,a['residual_std']);ref={};candidates=[]
    for name,pack in packs:
        for d in [5,20]:
            for phase in [0,2]:ref[name,d,phase]=run(pack,a,'grape',{},d,phase)['rmse']
    for temp,share in itertools.product([.25,1.,4.,16.],[0.,.001,.01]):
        cfg={'temperature':temp,'share':share};scores=[];plain=[]
        for name,pack in packs:
            for d in [5,20]:
                for phase in [0,2]:
                    row=simulate(pack,a,cfg,d,phase,ds);ratio=row['rmse']/ref[name,d,phase];scores.append(ratio)
                    if name=='original':plain.append(ratio)
        candidates.append({'config':cfg,'score':float(np.mean(scores)),'original_ratio':float(np.mean(plain))})
    feasible=[r for r in candidates if r['original_ratio']<=1.02];selected=min(feasible or candidates,key=lambda r:r['score']);selected['ordinary_guard_pass']=bool(feasible)
    k,b=expert_configs(ds);lock={'dataset':ds,'spec':spec,'selected':selected,'experts':{'kalman':k,'regime':b},'protocol_sha256':hashlib.sha256((ROOT/'protocol_v7.json').read_bytes()).hexdigest(),'locked_at':time.time()}
    target.write_text(json.dumps(lock,indent=2));(OUT/f'development_{ds}.json').write_text(json.dumps(candidates,indent=2));print(ds,selected,flush=True)

def evaluate(ds):
    target=OUT/f'evaluation_{ds}.csv'
    if target.exists():raise SystemExit('Preserving first evaluation.')
    lock=json.loads((OUT/f'locked_{ds}.json').read_text());a=load_artifact(ds);d=np.load(ROOT/f'models/replay_{ds}.npz',allow_pickle=False)
    p=prepare((d['X'],d['y'],d['keys']),a,lock['spec']);rows=[];replays={'truth':d['y']}
    for delay in [0,5,20]:
        for phase in range(5):
            row,pred,w=simulate(p,a,lock['selected']['config'],delay,phase,ds,True);rows.append(row);replays[f'delayed_ensemble_d{delay}_p{phase}']=pred;replays[f'weights_d{delay}_p{phase}']=w
            base,bp=run(p,a,'grape',{},delay,phase,True);rows.append({'dataset':ds,**base});replays[f'grape_d{delay}_p{phase}']=bp
    pd.DataFrame(rows).to_csv(target,index=False);np.savez_compressed(OUT/f'predictions_{ds}.npz',**replays)
    print(pd.DataFrame(rows).groupby(['method','delay'])[['rmse','p90','queries']].mean().to_string(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['develop','evaluate']);p.add_argument('--dataset',type=int,required=True);a=p.parse_args();{'develop':develop,'evaluate':evaluate}[a.mode](a.dataset)
