"""Reproducible small-device inverse design: physical solver -> data -> GP -> next design.
Not a new optimizer; standard GP expected improvement. Not a fab-qualified device.
"""
import json,hashlib,time,warnings
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from scipy.stats import qmc,norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern,ConstantKernel
from sklearn.exceptions import ConvergenceWarning
from device_simulator import simulate
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/inverse';OUT.mkdir(exist_ok=True)

def parameters(x):return [float(16+2*x[0]),float(16+2*x[1]),float(.1+.9*x[2])]
def gp(X,y):
    model=GaussianProcessRegressor(kernel=ConstantKernel(1.,'fixed')*Matern(length_scale=np.ones(3)*.35,length_scale_bounds=(.05,2),nu=2.5),alpha=1e-6,normalize_y=True,n_restarts_optimizer=0,random_state=11)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',ConvergenceWarning);model.fit(X,y)
    return model

def generate():
    if (OUT/'dataset.json').exists():return
    protocol={'created_utc':datetime.now(timezone.utc).isoformat(),'task':'Match target I-V behavior by choosing p/n doping and junction length. 1D silicon diode, not an advanced-node transistor.','simulator':'DEVSIM2.11.2; finite-volume Poisson/drift-diffusion/SRH;300K;constant upstream mobility;no quantum/tunnelling/high-field/breakdown model','space':{'log10_acceptor_cm3':[16,18],'log10_donor_cm3':[16,18],'length_um':[.1,1.]},'target_reference_parameters':[17.3,17.6,.55],'biases_v':[.2,.4,.5],'design_pool':192,'heldout_surrogate_test':64,'dataset_seed':261111,'search_seeds':[11,23,37,51,71],'initial_points':8,'budget':32,'methods':['random','standard_gp_expected_improvement'],'primary':'Mean best target log-current MSE after32 queried designs versus paired random search; report all5seeds. No tuned win threshold.','secondary':'Fixed heldout log-current prediction RMSE at8,16,24,32labels; no heldout label provided to model.','limits':'Offline replay of an actually generated TCAD pool: all256 simulations incur generation cost. Search query savings are counterfactual, not measured wall-clock or fab savings. Target is a known synthetic reference, not a better-than-market device. Same pool shared across seeds.','qualification':'Retain simulation failures. Final best designs independently rerun at double mesh density; report current conservation and mesh sensitivity.'}
    (ROOT/'protocol_inverse_design.json').write_text(json.dumps(protocol,indent=2))
    X=qmc.LatinHypercube(3,seed=261111).random(256);records=[];t0=time.time()
    target=simulate(17.3,17.6,.55)
    for i,x in enumerate(X):
        t=time.time()
        try:r={'ok':True,**simulate(*parameters(x))}
        except Exception as exc:r={'ok':False,'error':str(exc)}
        records.append({'index':i,'split':'pool' if i<192 else 'heldout','x':x.tolist(),'parameters':parameters(x),'seconds':time.time()-t,**r})
        if i%20==0:print('GENERATED',i,flush=True)
    (OUT/'dataset.json').write_text(json.dumps({'protocol_sha256':hashlib.sha256((ROOT/'protocol_inverse_design.json').read_bytes()).hexdigest(),'target':target,'records':records,'elapsed_s':time.time()-t0},indent=2,allow_nan=False))

def run():
    data=json.loads((OUT/'dataset.json').read_text());rows=data['records'];fail=[r for r in rows if not r['ok']]
    if fail:raise RuntimeError(f'{len(fail)} simulator failures retained; do not silently discard them')
    X=np.array([r['x'] for r in rows]);Y=np.array([r['log_currents'] for r in rows]);target=np.array(data['target']['log_currents']);loss=np.mean((Y-target)**2,axis=1);traces=[];checkpoints=[]
    for seed in [11,23,37,51,71]:
        initial=np.random.default_rng(seed).choice(192,8,replace=False).tolist()
        for method in ['random','expected_improvement']:
            seen=initial.copy();rng=np.random.default_rng(seed+10000);trace=[]
            while True:
                best=min(seen,key=lambda i:loss[i]);entry={'labels':len(seen),'best_index':int(best),'best_loss':float(loss[best])}
                if len(seen) in [8,16,24,32]:
                    surrogate=gp(X[seen],Y[seen]);pred=surrogate.predict(X[192:]);entry['heldout_log_current_rmse']=float(np.sqrt(np.mean((pred-Y[192:])**2)))
                    checkpoints.append({'seed':seed,'method':method,'labels':len(seen),'indices':seen.copy(),'kernel':str(surrogate.kernel_),'rmse':entry['heldout_log_current_rmse']})
                trace.append(entry)
                if len(seen)==32:break
                remaining=np.array([i for i in range(192) if i not in seen])
                if method=='random':next_i=int(rng.choice(remaining))
                else:
                    model=gp(X[seen],np.log10(loss[seen]+1e-12));mu,std=model.predict(X[remaining],return_std=True);delta=float(np.min(np.log10(loss[seen]+1e-12)))-mu-.01;z=delta/np.maximum(std,1e-12);ei=delta*norm.cdf(z)+std*norm.pdf(z);next_i=int(remaining[np.argmax(ei)])
                seen.append(next_i)
            traces.append({'seed':seed,'method':method,'initial_indices':initial,'queried_indices':seen,'trace':trace});print('SEARCH',seed,method,trace[-1],flush=True)
    outcomes=[]
    for seed in [11,23,37,51,71]:
        row={'seed':seed}
        for method in ['random','expected_improvement']:
            t=next(t for t in traces if t['seed']==seed and t['method']==method);row[method]=t['trace'][-1]['best_loss']
        row['improvement_pct']=(1-row['expected_improvement']/row['random'])*100;outcomes.append(row)
    best=min((t['trace'][-1]['best_index'] for t in traces if t['method']=='expected_improvement'),key=lambda i:loss[i]);fine=simulate(*rows[best]['parameters'],fine=True);coarse=rows[best];relative=np.abs(np.array(fine['currents'])/np.array(coarse['currents'])-1)*100
    random_mean=np.mean([x['random'] for x in outcomes]);ei_mean=np.mean([x['expected_improvement'] for x in outcomes]);summary={'generated_utc':datetime.now(timezone.utc).isoformat(),'pool_n':192,'heldout_n':64,'all_simulation_cost_s':data['elapsed_s'],'failed_simulations':len(fail),'outcomes':outcomes,'mean_loss_random':float(random_mean),'mean_loss_ei':float(ei_mean),'mean_loss_reduction_pct':float((1-ei_mean/random_mean)*100),'search_wins':sum(x['improvement_pct']>0 for x in outcomes),'max_pool_current_imbalance':max(r['max_current_imbalance'] for r in rows),'best_design':{'index':int(best),'parameters':coarse['parameters'],'coarse':coarse,'fine':fine,'mesh_change_pct':relative.tolist()},'traces':traces,'checkpoints':checkpoints,'scope':'Simulated target-matching study on a basic1D diode. GP expected improvement is standard prior art. No fabrication, novel chip, power/performance improvement over existing products, or real research-cycle savings demonstrated.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False));print('SUMMARY',json.dumps({k:v for k,v in summary.items() if k not in ['traces','checkpoints','best_design']}),flush=True)
if __name__=='__main__':generate();run()
