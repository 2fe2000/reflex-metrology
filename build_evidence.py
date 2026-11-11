from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
rows=[]
burst=pd.read_csv(ROOT/'results/burst_exploratory.csv')
for ds in [1,2]:
 d=pd.read_csv(ROOT/f'results/stream_unseen_{ds}.csv')
 for method,budget,label in [('frozen',0.,'Frozen'),('grape_uniform',1.,'GRAPE · every sample'),('grape_uniform',.2,'GRAPE · 20% labels')]:
  r=d[(d.method==method)&(d.budget==budget)].iloc[0]
  rows.append({'dataset':ds,'method':label,**{k:float(r[k]) for k in ['rmse','p90']},'queries':int(r.queries),'n':int(r.n)})
 for method,label in [('grape_exact_count_uniform','GRAPE · same-count uniform'),('reflex_burst','REFLEX event-triggered')]:
  r=burst[(burst.dataset==ds)&(burst.method==method)].iloc[0]
  rows.append({'dataset':ds,'method':label,**{k:float(r[k]) for k in ['rmse','p90']},'queries':int(r.queries),'n':int(r.n)})
e={'rows':rows,'verdict':'Original locked success gate failed on both datasets. Exploratory event-triggered revision shows a signal on Dataset 1 only.','bootstrap':json.loads((ROOT/'results/burst_bootstrap.json').read_text()),'protocols':['protocol.json','protocol_v2.json'],'source':'https://github.com/cheonwoolee/GRAPE','novelty':'Not established. Uses upstream GRAPE model equations plus a simple event-triggered measurement schedule.'}
(ROOT/'results/evidence.json').write_text(json.dumps(e,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f7f8f5','axes.facecolor':'#f7f8f5','axes.edgecolor':'#cbd4da','text.color':'#17202b','axes.labelcolor':'#17202b','xtick.color':'#647680','ytick.color':'#647680','font.size':11})
fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for ax,ds in zip(axs,[1,2]):
 data=[r for r in rows if r['dataset']==ds and r['method'] in ['GRAPE · every sample','GRAPE · same-count uniform','REFLEX event-triggered']]
 labels=['Every sample','Same-count uniform','REFLEX burst'];vals=[r['rmse'] for r in data]
 ax.barh(labels,vals,color=['#8798a3','#c4cdd2','#2563eb'],height=.55)
 for i,r in enumerate(data):ax.text(r['rmse']+.015*max(vals),i,f"{r['rmse']:.3f}  / {r['queries']} labels",va='center',fontsize=10)
 ax.set_xlim(0,max(vals)*1.48);ax.invert_yaxis();ax.set_title(f'Dataset {ds} · exploratory',loc='left',pad=22,fontweight='bold');ax.set_xlabel('RMSE — lower is better')
fig.suptitle('Measurement timing helps Dataset 1; general advantage unproven',fontsize=15,x=.01,ha='left')
fig.savefig(ROOT/'results/benchmark_comparison.png',dpi=170)
fig.savefig(ROOT/'results/benchmark_comparison.pdf')
print(json.dumps(e,indent=2))
