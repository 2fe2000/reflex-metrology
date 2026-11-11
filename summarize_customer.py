"""Summarize the frozen customer protocol. Shared time blocks across offsets/methods."""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/customer'

def interval(v): return [float(x) for x in np.quantile(v,[.025,.975])]
def metrics(e): return np.sqrt(np.mean(e**2,axis=-1)).mean(axis=-1),np.quantile(e,.9,axis=-1).mean(axis=-1)
def main():
    rng=np.random.default_rng(761102);rows=[]
    thresholds=json.loads((OUT/'threshold_lock.json').read_text())['thresholds']
    for ds in [1,2]:
        a=np.load(OUT/f'replays_{ds}.npz');n=len(a['truth'])
        for delay in [5,20]:
            errs={f'{m}{p}':np.abs(a[f'{m}_d{delay}_p{p}']-a['truth']) for m,p in [('grape',5),('grape',10),('reflex',5),('reflex',10)]}
            threshold=thresholds[f'{ds}_{delay}'];dist={k:[] for k in ['reflex10_rmse_ratio','reflex10_p90_ratio','grape10_rmse_ratio','grape10_p90_ratio','exceedance_relative_reduction','exceedance_pp_reduction']}
            point={k:metrics(e) for k,e in errs.items()}
            for start in range(0,5000,50):
                idx=(rng.integers(0,n,size=(50,(n+49)//50,1))+np.arange(50))%n;idx=idx.reshape(50,-1)[:,:n]
                # batch, phase, time; one time resample shared by all phases/methods
                sampled={k:metrics(e[:,idx].transpose(1,0,2)) for k,e in errs.items()}
                for name in ['reflex10','grape10']:
                    for j,metric in enumerate(['rmse','p90']):dist[f'{name}_{metric}_ratio'].extend(sampled[name][j]/sampled['grape5'][j])
                b=(errs['grape5'][:,idx]>threshold).mean(axis=(0,2));c=(errs['reflex5'][:,idx]>threshold).mean(axis=(0,2))
                dist['exceedance_relative_reduction'].extend(np.divide(b-c,b,out=np.zeros_like(b),where=b>0)*100)
                dist['exceedance_pp_reduction'].extend((b-c)*100)
            rates={m:float(np.mean(errs[m+'5']>threshold)) for m in ['grape','reflex']}
            r={'dataset':ds,'delay':delay,'n':n,'threshold':threshold,'same_budget':{'grape_rmse':float(point['grape5'][0]),'reflex_rmse':float(point['reflex5'][0]),'rmse_improvement_pct':float((1-point['reflex5'][0]/point['grape5'][0])*100),'p90_improvement_pct':float((1-point['reflex5'][1]/point['grape5'][1])*100),'exceedance_rates':rates,'exceedance_reduction_pct':(1-rates['reflex']/rates['grape'])*100,'exceedance_reduction_pp':(rates['grape']-rates['reflex'])*100,'exceedance_reduction_pct_ci95':interval(dist['exceedance_relative_reduction']),'exceedance_reduction_pp_ci95':interval(dist['exceedance_pp_reduction'])},'half_measurements':{}}
            for name in ['reflex10','grape10']:
                ratios={metric:float(point[name][j]/point['grape5'][j]) for j,metric in enumerate(['rmse','p90'])};cis={metric:interval(dist[f'{name}_{metric}_ratio']) for metric in ['rmse','p90']}
                r['half_measurements'][name]={'ratios':ratios,'ci95':cis,'point_pass':ratios['rmse']<=1.02 and ratios['p90']<=1.05,'ci_pass':cis['rmse'][1]<=1.02 and cis['p90'][1]<=1.05}
            rows.append(r)
            print(json.dumps(r),flush=True)
    result={'protocol_sha256':hashlib.sha256((ROOT/'protocol_customer_benchmark.json').read_bytes()).hexdigest(),'replicates':5000,'block_length':50,'seed':761102,'conditions':rows,'frontier':pd.read_csv(OUT/'means.csv').to_dict(orient='records'),'primary_pass':all(r['half_measurements']['reflex10']['ci_pass'] for r in rows),'limits':'Exploratory reused streams; intervals conditional on frozen candidate and do not correct repeated inspection/model selection. Offsets are not independent trials. Exceedance is normalized prediction error, not defect rate or physical specification.'}
    (OUT/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':main()
