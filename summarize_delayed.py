"""Paired time-block intervals; same resampled indices for all sampling phases."""
import json
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/v7';rng=np.random.default_rng(20261111)
summary=[];replicates=5000;block=50
for ds in [1,2]:
    en=np.load(OUT/f'predictions_{ds}.npz');bayes=np.load(ROOT/f'results/v6/predictions_{ds}.npz');y=en['truth'];n=len(y)
    for delay in [0,5,20]:
        baseline=np.array([en[f'grape_d{delay}_p{p}'] for p in range(5)])
        eb=np.abs(baseline-y)
        for method,file in [('delayed_ensemble',en),('bayesian_regime',bayes)]:
            candidate=np.array([file[f'{method}_d{delay}_p{p}'] for p in range(5)]);ec=np.abs(candidate-y)
            br=float(np.sqrt(np.mean(eb**2,axis=1)).mean());cr=float(np.sqrt(np.mean(ec**2,axis=1)).mean())
            bp=float(np.quantile(eb,.9,axis=1).mean());cp=float(np.quantile(ec,.9,axis=1).mean())
            boot_r=[];boot_p=[]
            for start in range(0,replicates,100):
                count=min(100,replicates-start);starts=rng.integers(0,n,size=(count,int(np.ceil(n/block))))
                ids=((starts[:,:,None]+np.arange(block))%n).reshape(count,-1)[:,:n]
                b=eb[:,ids];c=ec[:,ids]
                b_rm=np.sqrt(np.mean(b*b,axis=2)).mean(axis=0);c_rm=np.sqrt(np.mean(c*c,axis=2)).mean(axis=0)
                b_p=np.quantile(b,.9,axis=2).mean(axis=0);c_p=np.quantile(c,.9,axis=2).mean(axis=0)
                boot_r.extend((100*(1-c_rm/b_rm)).tolist());boot_p.extend((100*(1-c_p/b_p)).tolist())
            row={'dataset':ds,'delay':delay,'method':method,'rmse_baseline':br,'rmse_candidate':cr,'rmse_improvement_pct':100*(1-cr/br),
                 'rmse_ci95':np.quantile(boot_r,[.025,.975]).tolist(),'p90_baseline':bp,'p90_candidate':cp,'p90_improvement_pct':100*(1-cp/bp),
                 'p90_ci95':np.quantile(boot_p,[.025,.975]).tolist(),'n':n,'queries_by_phase':[len(np.arange(p,n,5)) for p in range(5)]}
            summary.append(row);print(ds,delay,method,'RMSE',round(row['rmse_improvement_pct'],2),row['rmse_ci95'],'P90',round(row['p90_improvement_pct'],2),row['p90_ci95'],flush=True)
primary=[r for r in summary if r['method']=='delayed_ensemble' and r['delay']>0]
mean=float(np.mean([r['rmse_improvement_pct'] for r in primary]));pass_gate=mean>=10 and min(r['rmse_improvement_pct'] for r in primary)>=-2 and min(r['p90_improvement_pct'] for r in primary)>=-5
payload={'status':'Exploratory; repeatedly inspected evaluation data; conditional intervals do not correct model selection bias.',
         'uncertainty':{'method':'paired circular moving-block bootstrap; phases share sampled time indices','block':block,'replicates':replicates,'seed':20261111},
         'primary_gate':{'mean_rmse_improvement_pct':mean,'target_pct':10,'passed':pass_gate},'comparisons':summary}
(OUT/'summary.json').write_text(json.dumps(payload,indent=2));print('PRIMARY',payload['primary_gate'])
