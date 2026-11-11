"""v4 protocol: development-only tuning, then one locked exploratory reevaluation."""
import argparse, hashlib, itertools, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from portable_runtime import PortableModel
from delay_model import make_model

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/v4'
OUT.mkdir(exist_ok=True)

def load_artifact(ds):
    return json.loads((ROOT/f'models/reflex_{ds}.json').read_text())

def prepare(pack, artifact, spec):
    X,y,keys=pack
    mean=np.array(artifact['mean']); scale=np.array(artifact['scale'])
    xs=(np.nan_to_num(X)-mean)/scale
    # Match the deployed base's float32 arithmetic per row.
    m=PortableModel(artifact)
    base=np.array([m.base(x) for x in xs])
    return dict(X=xs,y=y,keys=keys,base=base,spec=spec)

def design(pack,cfg):
    dim=cfg.get('dim',0); context=cfg.get('context',False)
    columns=[np.ones((len(pack['y']),1))]
    if dim:
        columns.append(np.clip(pack['X'][:,pack['spec']['indices'][:dim]],-5,5)/np.sqrt(dim))
    if context:
        mapping={k:i for i,k in enumerate(pack['spec']['contexts'])}
        z=np.zeros((len(pack['y']),len(mapping)))
        for i,k in enumerate(pack['keys']):
            if str(k) in mapping:z[i,mapping[str(k)]]=.5
        columns.append(z)
    return np.concatenate(columns,axis=1)

def run(pack,artifact,method,cfg,delay,phase,keep=False):
    y=pack['y'];n=len(y);pred=np.zeros(n);period=5
    requests=np.arange(phase,n,period); requested=np.zeros(n,bool);requested[requests]=True
    if method=='grape': model=PortableModel(artifact)
    elif method!='frozen':
        Z=design(pack,cfg);model=make_model(method,cfg,Z.shape[1])
    arrivals=0
    def feedback(j):
        nonlocal arrivals
        # First label read by the model happens only in this delivery callback.
        if method=='grape':model.update_scaled(pack['X'][j],float(y[j]),str(pack['keys'][j]))
        elif method!='frozen':model.observe(Z[j],float(y[j]-pack['base'][j]),j)
        arrivals+=1
    for i in range(n):
        j=i-delay
        if delay>0 and j>=0 and requested[j] and method!='frozen':feedback(j)
        if method=='grape':pred[i]=model.predict_scaled(pack['X'][i],str(pack['keys'][i]))
        elif method=='frozen':pred[i]=pack['base'][i]
        else:pred[i]=pack['base'][i]+model.predict(Z[i],i)
        if delay==0 and requested[i] and method!='frozen':feedback(i)
    error=np.abs(y-pred)
    row={'method':method,'delay':delay,'phase':phase,'rmse':float(np.sqrt(np.mean(error**2))),
         'p90':float(np.quantile(error,.9)),'queries':int(requested.sum()) if method!='frozen' else 0,
         'arrived':arrivals,'n':n}
    return (row,pred) if keep else row

def grids(method):
    if method=='ema':return [{'rate':x} for x in [.02,.05,.1,.2,.4,.7,1.]]
    if method=='rls':return [dict(dim=d,context=c,forget=f,prior=p) for d,c,f,p in itertools.product([0,4,12],[False,True],[.99,.999,1.],[.1,1.])]
    return [dict(dim=d,context=c,q=q,trend=t,prior=1.) for d,c,q,t in itertools.product([0,4],[False,True],[.0001,.001,.01,.1,1.],[False,True])]

def develop(ds):
    from stream_benchmark import bundle
    target=OUT/f'locked_{ds}.json'
    if target.exists():raise SystemExit('Development already locked; preserve previous run.')
    a=load_artifact(ds);data=bundle(ds,['train','valid','test']);xt,yt,kt=data['train']
    xs=(xt-np.array(a['mean']))/np.array(a['scale']);m=PortableModel(a)
    r=yt-np.array([m.base(x) for x in xs])
    corr=np.abs(np.nan_to_num(np.corrcoef(np.column_stack([xs,r]).T)[-1,:-1]))
    spec={'indices':np.argsort(corr)[::-1].tolist(),'contexts':sorted(set(map(str,kt)))}
    dev=tuple(np.concatenate([data['valid'][i],data['test'][i]]) for i in range(3))
    p=prepare(dev,a,spec);records=[];selected={}
    for method in ['ema','rls','timestamped']:
        candidates=[]
        for cid,cfg in enumerate(grids(method)):
            rows=[run(p,a,method,cfg,d,phase) for d in [0,5,20] for phase in [0,2]]
            score=float(np.mean([r['rmse'] for r in rows]))
            candidates.append({'config':cfg,'score':score})
            records.append({'method':method,'candidate':cid,'config':json.dumps(cfg),'score':score})
        selected[method]=min(candidates,key=lambda v:v['score'])
        print(ds,method,selected[method],flush=True)
    lock={'dataset':ds,'spec':spec,'selected':selected,'protocol_sha256':hashlib.sha256((ROOT/'protocol_v4.json').read_bytes()).hexdigest(),
          'locked_at':time.time(),'selection_data':'train for base/features; valid+test for hyperparameters; unseen never loaded by develop'}
    target.write_text(json.dumps(lock,indent=2));pd.DataFrame(records).to_csv(OUT/f'development_{ds}.csv',index=False)

def evaluate(ds):
    target=OUT/f'evaluation_{ds}.csv'
    if target.exists():raise SystemExit('Preserving first locked evaluation.')
    lock=json.loads((OUT/f'locked_{ds}.json').read_text());a=load_artifact(ds)
    d=np.load(ROOT/f'models/replay_{ds}.npz',allow_pickle=False)
    p=prepare((d['X'],d['y'],d['keys']),a,lock['spec']);rows=[];replays={'truth':d['y']}
    for method in ['frozen','grape','ema','rls','timestamped']:
        cfg=lock['selected'].get(method,{}).get('config',{})
        for delay in [0,5,20]:
            for phase in range(5):
                row,pred=run(p,a,method,cfg,delay,phase,True);rows.append({'dataset':ds,**row})
                replays[f'{method}_d{delay}_p{phase}']=pred
    pd.DataFrame(rows).to_csv(target,index=False);np.savez_compressed(OUT/f'predictions_{ds}.npz',**replays)
    print(pd.DataFrame(rows).groupby(['method','delay'])[['rmse','p90','queries']].mean().to_string(),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['develop','evaluate']);parser.add_argument('--dataset',type=int,required=True)
    args=parser.parse_args();{'develop':develop,'evaluate':evaluate}[args.mode](args.dataset)
