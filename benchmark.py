"""Frozen-protocol retrospective active-metrology benchmark. No fabrication control."""
import argparse, hashlib, json, os, pickle, time, platform
from pathlib import Path
import numpy as np, pandas as pd
from scipy.linalg import cho_factor,cho_solve
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
ROOT=Path(__file__).resolve().parent
BUDGETS=[0,2,4,8,16,32]; SEEDS=[11,23,37,51,71]
METHODS=['frozen','offset_random','ridge_random','gp_random','gp_uncertainty','reflex_integrated']

def rmse(a,b):return float(np.sqrt(np.mean((np.asarray(a)-b)**2)))
def load():
    d=pd.read_csv(ROOT/'data/wafer_features.csv')
    cols=[c for c in d if '__' in c or c.startswith(('stage_','machine_','chamber_'))]
    return d,cols

def episodes(d):
    """40 early candidate wafers then 40 subsequent test wafers. No reused identities."""
    order=d.groupby('WAFER_ID').start.min().sort_values().index.to_numpy()
    for k,start in enumerate(range(0,len(order)-79,80)):
        pool=d[d.WAFER_ID.isin(order[start:start+40])].sort_values(['start','WAFER_ID','STAGE'])
        future=d[d.WAFER_ID.isin(order[start+40:start+80])].sort_values(['start','WAFER_ID','STAGE'])
        # Across-stage runs can overlap in time: embargo any candidate ending after first future observation.
        pool=pool[pool.end<future.start.min()]
        if len(pool)>=32 and len(future)>=20:
            assert not set(pool.WAFER_ID)&set(future.WAFER_ID)
            assert pool.end.max()<future.start.min()
            yield k,pool,future

def kernel(a,b,length):
    ds=np.maximum(0,(a*a).sum(1)[:,None]+(b*b).sum(1)[None,:]-2*a@b.T)/a.shape[1]
    return np.exp(-.5*ds/(length*length))

def choose_order(K,budget,method,seed,noise):
    rng=np.random.default_rng(seed)
    if method in ['offset_random','ridge_random','gp_random']:return rng.permutation(len(K))[:budget].tolist()
    C=K.copy();chosen=[]
    # Shared one random initialization for active strategies. Subsequent selection uses inputs only.
    for step in range(budget):
        if step==0:i=int(rng.integers(len(K)))
        else:
            diag=np.maximum(C.diagonal(),0)
            scores=diag if method=='gp_uncertainty' else np.sum(C*C,axis=0)/(diag+noise)
            scores[chosen]=-np.inf;i=int(np.argmax(scores))
        chosen.append(i);col=C[:,i].copy();C-=np.outer(col,col)/(C[i,i]+noise)
    return chosen

def run_eval(d,artifact,config,split,save=False):
    target=d[d.split==split]
    X=artifact['scaler'].transform(artifact['imputer'].transform(d[artifact['features']]))
    X=np.clip(X,-8,8)
    # Kernel uses observable sensor summaries only; no wafer ID, timestamp, labels or future features for selection.
    feat_idx=artifact['kernel_indices']; Z=X[:,feat_idx]
    base=artifact['model'].predict(X)
    records=[]; predictions=[]; demo=[]
    for block,pool,future in episodes(target):
        pi=pool.index.to_numpy();ti=future.index.to_numpy()
        xp,xt=Z[pi],Z[ti]; yp=pool.AVG_REMOVAL_RATE.to_numpy();yt=future.AVG_REMOVAL_RATE.to_numpy()
        bp,bt=base[pi],base[ti]; K=kernel(xp,xp,config['length']);Kt=kernel(xt,xp,config['length'])
        for seed in SEEDS:
            for method in METHODS:
                start=time.perf_counter();order=[] if method=='frozen' else choose_order(K,32,method,seed,config['noise'])
                selection_ms=(time.perf_counter()-start)*1e3
                for budget in ([0] if method=='frozen' else BUDGETS[1:]):
                    idx=order[:budget]; fit_start=time.perf_counter();pred=bt.copy()
                    if budget:
                        residual=yp[idx]-bp[idx]
                        if method=='offset_random':pred+=np.mean(residual)
                        elif method=='ridge_random':
                            model=Ridge(alpha=10).fit(xp[idx],residual);pred+=model.predict(xt)
                        else:
                            kk=K[np.ix_(idx,idx)]+config['noise']*np.eye(budget)
                            alpha=cho_solve(cho_factor(kk,lower=True),residual)
                            pred+=Kt[:,idx]@alpha
                    elapsed=(time.perf_counter()-fit_start)*1e3
                    err=np.abs(pred-yt)
                    records.append(dict(split=split,block=block,seed=seed,method=method,budget=budget,n_test=len(yt),rmse=rmse(yt,pred),mae=float(err.mean()),p90=float(np.quantile(err,.9)),fit_predict_ms=elapsed,selection32_ms=selection_ms))
                    if save:
                        for j in range(len(yt)):
                            predictions.append(dict(block=block,seed=seed,method=method,budget=budget,wafer=int(future.iloc[j].WAFER_ID),stage=str(future.iloc[j].STAGE),truth=float(yt[j]),prediction=float(pred[j])))
                        # Every block retained; presentation cannot silently select a favorable block.
                        if seed==SEEDS[0] and method in ['frozen','gp_uncertainty','reflex_integrated']:
                            demo.append(dict(block=block,method=method,budget=budget,pool_ids=[f'{int(pool.iloc[j].WAFER_ID)}-{pool.iloc[j].STAGE}' for j in range(len(pool))],selected=idx,prediction=pred.tolist(),truth=yt.tolist(),base=bt.tolist(),rmse=rmse(yt,pred),fit_predict_ms=elapsed))
    frame=pd.DataFrame(records)
    if save:
        frame.to_csv(ROOT/f'results/{split}_metrics.csv',index=False)
        pd.DataFrame(predictions).to_csv(ROOT/f'results/{split}_predictions.csv',index=False)
        (ROOT/f'results/{split}_replay.json').write_text(json.dumps(demo))
    return frame

def develop():
    d,cols=load();train=d[d.split=='train']; dev=d[d.split=='dev']
    imp=SimpleImputer(strategy='median',keep_empty_features=True).fit(train[cols])
    scaler=StandardScaler().fit(imp.transform(train[cols]))
    X=np.clip(scaler.transform(imp.transform(train[cols])),-8,8);y=train.AVG_REMOVAL_RATE.to_numpy()
    xd=np.clip(scaler.transform(imp.transform(dev[cols])),-8,8);yd=dev.AVG_REMOVAL_RATE.to_numpy()
    candidates={
      'extra_trees':ExtraTreesRegressor(n_estimators=300,min_samples_leaf=3,max_features=.8,n_jobs=4,random_state=11),
      'hist_gradient_boosting':HistGradientBoostingRegressor(max_iter=250,max_leaf_nodes=15,l2_regularization=10,learning_rate=.05,random_state=11)
    }
    scores={};models={}
    for name,m in candidates.items():
        t=time.perf_counter();m.fit(X,y);scores[name]={'rmse':rmse(yd,m.predict(xd)),'train_seconds':time.perf_counter()-t};models[name]=m;print(name,scores[name],flush=True)
    name=min(scores,key=lambda n:scores[n]['rmse']);model=models[name]
    kcols=[i for i,c in enumerate(cols) if c.endswith('__mean') or c.startswith('stage_')]
    artifact={'model':model,'model_name':name,'imputer':imp,'scaler':scaler,'features':cols,'kernel_indices':kcols}
    grid=[]
    for length in [.5,1.,2.,4.]:
        for noise in [.05,.2,1.]:
            cfg={'length':length,'noise':noise};m=run_eval(d,artifact,cfg,'dev')
            # Same hyperparameters for all GP selection methods. Select using their pooled development average.
            v=float(m[m.method.isin(['gp_random','gp_uncertainty','reflex_integrated'])].rmse.mean())
            grid.append(dict(**cfg,score=v));print('dev',cfg,v,flush=True)
    best=min(grid,key=lambda v:v['score']);cfg={k:best[k] for k in ['length','noise']}
    dm=run_eval(d,artifact,cfg,'dev',True)
    # Development-only threshold: best adaptive baseline with 16 labels, macro block/seed RMSE.
    baseline=dm[(dm.budget==16)&(~dm.method.isin(['reflex_integrated','frozen']))].groupby('method').rmse.mean()
    cfg.update(base_model=name,threshold_rmse=float(baseline.min()),threshold_source='best adaptive baseline at 16 labels on development',base_scores=scores,grid=grid)
    (ROOT/'results/locked_config.json').write_text(json.dumps(cfg,indent=2))
    with open(ROOT/'results/base_model.pkl','wb') as f:pickle.dump(artifact,f)
    print('LOCKED',json.dumps(cfg),flush=True)

def test():
    if (ROOT/'results/test_metrics.csv').exists():raise SystemExit('Test already run; preserve result. Use a new explicitly exploratory run instead.')
    d,_=load();cfg=json.loads((ROOT/'results/locked_config.json').read_text())
    with open(ROOT/'results/base_model.pkl','rb') as f:art=pickle.load(f)
    m=run_eval(d,art,cfg,'test',True)
    print(m.groupby(['method','budget'])[['rmse','mae','p90']].mean().to_string())
    print('blocks',m.block.nunique(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['develop','test']);a=p.parse_args()
    {'develop':develop,'test':test}[a.mode]()
