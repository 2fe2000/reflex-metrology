"""Exploratory event-triggered metrology. Unseen outcomes have already been seen in v2.
No new unbiased generalization or novelty claim. Reuses upstream GRAPE updates.
"""
import copy,json,pickle,time
import numpy as np,pandas as pd
from stream_benchmark import ROOT,bundle,metrics,experiment

def run(pack,art,cfg,delay=0):
 X,y,keys=pack;X=art['scaler'].transform(X);model=copy.deepcopy(art['grape'])
 pred=[];query=[];reason=[];interval=cfg['min_gap'];next_at=0;ema=0.;pending=[];lat=[]
 scale=np.sqrt(art['noise']);threshold=cfg['threshold']*scale
 for i in range(len(y)):
  for due,j in list(pending):
   if due<=i:
    model.update(X[j],float(y[j]),eqp_ch_key=str(keys[j]));pending.remove((due,j))
  t=time.perf_counter();p=model.predict(X[i],eqp_ch_key=str(keys[i]));lat.append((time.perf_counter()-t)*1e3);pred.append(p)
  ask=i>=next_at;query.append(ask)
  if ask:
   innovation=abs(float(y[i])-p)
   # Metrology feedback is known only after its delay; timing adaptation also waits.
   if delay==0:
    if innovation>threshold:interval=cfg['min_gap'];why='innovation burst'
    else:interval=min(cfg['max_gap'],interval+cfg['step']);why='stable: extend interval'
    model.update(X[i],float(y[i]),eqp_ch_key=str(keys[i]))
   else:
    pending.append((i+delay,i));why='feedback pending'
    # Conservative fixed cadence until delayed labels are returned; sensitivity uses unchanged interval.
   next_at=i+int(interval);reason.append(why)
  else:reason.append('predict without new measurement')
 p=np.array(pred);q=np.array(query)
 row={**metrics(y,p),'queries':int(q.sum()),'n':len(y),'query_fraction':float(q.mean()),'predict_ms_p95':float(np.quantile(lat,.95))}
 replay={'prediction':p.tolist(),'truth':y.tolist(),'queried':q.tolist(),'reason':reason,'base':art['base'].predict(X).tolist(),'context':keys.tolist()}
 return row,replay

def main():
 results=[]
 for ds in [1,2]:
  with open(ROOT/f'results/stream_model_{ds}.pkl','rb') as f:art=pickle.load(f)
  data=bundle(ds,['valid','test']);dev=tuple(np.concatenate([data['valid'][i],data['test'][i]]) for i in range(3))
  cfg2=json.loads((ROOT/f'results/stream_config_{ds}.json').read_text())
  full=experiment(dev,art,cfg2,'grape_uniform',1.,11)['rmse'];grid=[]
  for threshold in [1.,2.,3.]:
   for gap in [5,10,20]:
    cfg={'threshold':threshold,'max_gap':gap,'min_gap':1,'step':1};row,_=run(dev,art,cfg)
    # Fixed development utility, favors lower error and fewer queries equally in normalized units.
    grid.append({**cfg,**row,'objective':row['rmse']/full+.5*row['query_fraction']})
  best=min(grid,key=lambda x:x['objective']);cfg={k:best[k] for k in ['threshold','max_gap','min_gap','step']}
  (ROOT/f'results/burst_config_{ds}.json').write_text(json.dumps({'exploratory':True,'config':cfg,'development_grid':grid},indent=2))
  pack=bundle(ds,['unseen'])['unseen'];row,replay=run(pack,art,cfg);row.update(dataset=ds,method='reflex_burst',exploratory=True)
  # Closest achievable uniform quota with exact same total number of metrology requests.
  from stream_benchmark import experiment as ex
  matched=copy.deepcopy(art['grape']);X=art['scaler'].transform(pack[0]);positions=set(np.linspace(0,len(X)-1,row['queries']).round().astype(int));pred=[]
  for i,x in enumerate(X):
   pred.append(matched.predict(x,eqp_ch_key=str(pack[2][i])))
   if i in positions:matched.update(x,float(pack[1][i]),eqp_ch_key=str(pack[2][i]))
  baseline={**metrics(pack[1],np.array(pred)),'dataset':ds,'method':'grape_exact_count_uniform','queries':len(positions),'n':len(X),'exploratory':True}
  results.extend([row,baseline]);replay['matched_uniform_prediction']=pred
  (ROOT/f'results/burst_replay_{ds}.json').write_text(json.dumps(replay))
  print('DATASET',ds,'config',cfg,'burst',row,'matched',baseline,flush=True)
 pd.DataFrame(results).to_csv(ROOT/'results/burst_exploratory.csv',index=False)

if __name__=='__main__':
 import torch;torch.set_num_threads(4);main()
