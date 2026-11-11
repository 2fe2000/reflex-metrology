"""Independent sparse-label experiment using the public GRAPE feature bundles."""
import argparse,copy,hashlib,json,logging,pickle,sys,time
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'external/GRAPE/src'))
from models.grape import GrapeModel
logging.getLogger('grape').setLevel(logging.WARNING)
SEEDS=[11,23,37,51,71];BUDGETS=[.1,.2,.4,1.]

class Restricted(pickle.Unpickler):
 def find_class(self,module,name):
  if (module,name) not in {('numpy._core.multiarray','_reconstruct'),('numpy.core.multiarray','_reconstruct'),('numpy','ndarray'),('numpy','dtype'),('numpy._core.numeric','_frombuffer'),('numpy.core.numeric','_frombuffer')}:
   raise ValueError(f'Unapproved pickle global {module}.{name}')
  return super().find_class(module,name)
def read(path):
 with path.open('rb') as f:return Restricted(f).load()
def bundle(ds,splits):
 folder=ROOT/f'external/GRAPE/data/data{ds}'
 ctx=read(folder/f'data{ds}_context_ids.pkl');out={}
 for s in splits:
  x=np.asarray(read(folder/f'data{ds}_{s}_features.pkl'),float);y=np.asarray(read(folder/f'data{ds}_{s}_label.pkl'),float)
  c=ctx[s];keys=np.array([f'{a}_{b}' for a,b in zip(c['eqp'],c['ch'])])
  assert len(x)==len(y)==len(keys)
  assert np.isfinite(y).all()
  out[s]=(np.nan_to_num(x),y,keys)
 return out
def metrics(y,p):
 e=np.abs(y-p);return {'rmse':float(np.sqrt(np.mean(e*e))),'mae':float(e.mean()),'p90':float(np.quantile(e,.9))}

class Residual:
 def __init__(self,dim,noise,process,clip):
  self.w=np.zeros(dim);self.P=np.eye(dim)*noise;self.noise=noise;self.process=process;self.clip=clip;self.context={}
 def predict(self,z,key):
  self.P+=np.eye(len(z))*self.process*self.noise
  mean,var=self.context.get(key,(0.,self.noise))
  var+=self.process*self.noise;self.context[key]=(mean,var)
  return float(self.w@z+mean),float(z@self.P@z+var)
 def update(self,z,key,residual):
  mean,var=self.context[key];p=self.P@z;den=float(self.noise+z@p+var)
  error=float(np.clip(residual-self.w@z-mean,-self.clip,self.clip))
  gain=p/den;self.w+=gain*error;self.P-=np.outer(p,p)/den
  self.context[key]=(mean+var/den*error,max(var-var*var/den,1e-12))

def experiment(pack,art,cfg,method,budget,seed,keep=False):
 X,y,keys=pack;X=art['scaler'].transform(X);base=art['base'].predict(X)
 Z=np.clip(X[:,art['indices'][:cfg['dim']]],-5,5)
 Z=np.column_stack([np.ones(len(Z)),Z/max(np.sqrt(cfg['dim']),1)])
 if method.startswith('grape'):
  model=copy.deepcopy(art['grape'])
 else:model=Residual(Z.shape[1],art['noise'],cfg['process'],art['clip'])
 preds=np.empty(len(y));queries=np.zeros(len(y),bool);variances=np.zeros(len(y));lat=[];updates=[]
 rng=np.random.default_rng(seed);past=[];queried=0;remaining=0;random_positions=set();uniform_positions=set()
 for i in range(len(y)):
  pos=i%50
  if pos==0:
   block_n=min(50,len(y)-i);quota=int(round(block_n*budget));remaining=quota
   random_positions=set(rng.choice(block_n,quota,replace=False).tolist())
   uniform_positions=set(np.linspace(0,block_n-1,quota).round().astype(int).tolist()) if quota else set()
  t=time.perf_counter()
  if method=='frozen':pred=base[i];uncertainty=0.
  elif method.startswith('grape'):pred=model.predict(X[i],eqp_ch_key=str(keys[i]));uncertainty=0.
  else:
   correction,uncertainty=model.predict(Z[i],str(keys[i]));pred=base[i]+correction
  lat.append((time.perf_counter()-t)*1e3)
  preds[i]=pred;variances[i]=uncertainty
  # Decision is made before reading y[i]. Past values here are variances, not labels.
  if method=='frozen':query=False
  elif method in ['grape_uniform','bayes_uniform']:query=pos in uniform_positions
  elif method=='bayes_random':query=pos in random_positions
  else:
   needed=remaining>=block_n-pos
   threshold=np.quantile(past[-200:],1-budget) if past else -np.inf
   query=remaining>0 and (needed or uncertainty>=threshold)
  past.append(uncertainty)
  if query:
   queries[i]=True;remaining-=1;queried+=1;t=time.perf_counter()
   if method.startswith('grape'):model.update(X[i],float(y[i]),eqp_ch_key=str(keys[i]))
   else:model.update(Z[i],str(keys[i]),float(y[i]-base[i]))
   updates.append((time.perf_counter()-t)*1e3)
 # Every policy receives exactly the same per-block query quota.
 expected=sum(round(min(50,len(y)-start)*budget) for start in range(0,len(y),50))
 if method!='frozen':assert queried==expected,(queried,expected)
 out={**metrics(y,preds),'method':method,'budget':budget,'seed':seed,'n':len(y),'queries':queried,'query_fraction':queried/len(y),'predict_ms_p50':float(np.median(lat)),'predict_ms_p95':float(np.quantile(lat,.95)),'update_ms_p95':float(np.quantile(updates,.95)) if updates else 0.}
 if keep:return out,{'prediction':preds,'truth':y,'queried':queries,'variance':variances,'context':keys,'base':base}
 return out

def fit(ds):
 data=bundle(ds,['train','valid','test']);xt,yt,ctx=data['train'];mask=yt>-10;xt,yt,ctx=xt[mask],yt[mask],ctx[mask]
 scaler=StandardScaler().fit(xt);xs=scaler.transform(xt);alpha=1000 if ds==1 else 10000
 base=Ridge(alpha=alpha).fit(xs,yt)
 residual=yt-base.predict(xs);noise=float(max(np.var(residual),1e-6))
 corrs=np.abs(np.nan_to_num(np.corrcoef(np.column_stack([xs,residual]).T)[-1,:-1]))
 indices=np.argsort(corrs)[::-1]
 grape=GrapeModel(alpha=alpha,adapter='nlms',na=5 if ds==1 else 10,ema=.1,use_gpu=False);grape.set_initial_data(xs,yt)
 art={'scaler':scaler,'base':base,'indices':indices,'noise':noise,'clip':float(max(np.quantile(np.abs(residual),.99)*3,np.std(yt)*2)),'grape':grape}
 pack=tuple(np.concatenate([data['valid'][i],data['test'][i]],axis=0) for i in range(3))
 grid=[]
 for dim in [0,4,12]:
  for process in [.001,.01,.1,1.]:
   cfg={'dim':dim,'process':process};m=[experiment(pack,art,cfg,'bayes_uniform',b,11) for b in [.1,.2,.4]]
   score=float(np.mean([r['rmse'] for r in m]));grid.append({**cfg,'score':score})
 cfg=min(grid,key=lambda x:x['score']);cfg={**cfg,'grid':grid,'dataset':ds}
 with open(ROOT/f'results/stream_model_{ds}.pkl','wb') as f:pickle.dump(art,f)
 (ROOT/f'results/stream_config_{ds}.json').write_text(json.dumps(cfg,indent=2))
 rows=[]
 for method in ['frozen','grape_uniform','bayes_uniform','bayes_random','reflex']:
  for b in ([0.] if method=='frozen' else BUDGETS):
   for seed in SEEDS:rows.append(experiment(pack,art,cfg,method,b,seed))
 pd.DataFrame(rows).to_csv(ROOT/f'results/stream_dev_{ds}.csv',index=False)
 print('LOCKED dataset',ds,json.dumps({k:v for k,v in cfg.items() if k!='grid'}),flush=True)
 print(pd.DataFrame(rows).groupby(['method','budget'])[['rmse','mae','p90','queries']].mean().to_string(),flush=True)

def final(ds):
 out=ROOT/f'results/stream_unseen_{ds}.csv'
 if out.exists():raise SystemExit('Preserving locked unseen run; refusing overwrite.')
 pack=bundle(ds,['unseen'])['unseen'];cfg=json.loads((ROOT/f'results/stream_config_{ds}.json').read_text())
 with open(ROOT/f'results/stream_model_{ds}.pkl','rb') as f:art=pickle.load(f)
 rows=[];replays={}
 for method in ['frozen','grape_uniform','bayes_uniform','bayes_random','reflex']:
  for b in ([0.] if method=='frozen' else BUDGETS):
   for seed in SEEDS:
    row,replay=experiment(pack,art,cfg,method,b,seed,True);rows.append(row)
    if seed==11:replays[f'{method}_{b}']={k:np.asarray(v).tolist() for k,v in replay.items()}
 pd.DataFrame(rows).to_csv(out,index=False)
 (ROOT/f'results/stream_replay_{ds}.json').write_text(json.dumps(replays))
 print(pd.DataFrame(rows).groupby(['method','budget'])[['rmse','mae','p90','queries']].mean().to_string(),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['fit','final']);p.add_argument('--dataset',type=int,required=True);a=p.parse_args()
 import torch;torch.set_num_threads(4)
 {'fit':fit,'final':final}[a.mode](a.dataset)
