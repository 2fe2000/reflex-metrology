"""Aggregate complete wafer runs and freeze chronological identities before modeling."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parent
raw=ROOT/'data/raw'
signals=[];labels=[]
for f in sorted(raw.rglob('*.csv')):
    if 'removalrate' in f.name: labels.append(pd.read_csv(f))
    else: signals.append(pd.read_csv(f))
d=pd.concat(signals,ignore_index=True).drop_duplicates()
y=pd.concat(labels,ignore_index=True).drop_duplicates()
y.columns=y.columns.str.strip();d.columns=d.columns.str.strip()
keys=['WAFER_ID','STAGE']
assert not y.duplicated(keys).any(), 'Conflicting labels'
id_cols=['MACHINE_ID','MACHINE_DATA','TIMESTAMP','WAFER_ID','STAGE','CHAMBER']
sensors=[c for c in d if c not in id_cols]
g=d.groupby(keys,sort=True)
feat=g[sensors].agg(['mean','std','min','max'])
feat.columns=['__'.join(c) for c in feat.columns]
meta=g.agg(start=('TIMESTAMP','min'),end=('TIMESTAMP','max'),n_rows=('TIMESTAMP','size'),machine=('MACHINE_ID','first'),chamber=('CHAMBER','first'))
features=meta.join(feat).reset_index()
features=features.merge(y,on=keys,validate='one_to_one')
features['stage_B']=(features.STAGE=='B').astype(float)
for m in sorted(d.MACHINE_ID.unique()):features[f'machine_{m}']=(features.machine==m).astype(float)
for c in sorted(d.CHAMBER.dropna().unique()):features[f'chamber_{c}']=(features.chamber==c).astype(float)
wafer=features.groupby('WAFER_ID').agg(start=('start','min'),end=('end','max')).sort_values(['start','end'])
ordered=wafer.index.to_numpy();n=len(ordered);cut1=int(.6*n);cut2=int(.8*n)
# Embargo runs spanning either boundary to ensure strict chronological separation.
t1=float(wafer.iloc[cut1].start);t2=float(wafer.iloc[cut2].start)
splits={}
for wid,row in wafer.iterrows():
    if row.end<t1:s='train'
    elif row.start>=t1 and row.end<t2:s='dev'
    elif row.start>=t2:s='test'
    else:s='embargo'
    splits[str(int(wid))]=s
features['split']=features.WAFER_ID.map(lambda x:splits[str(int(x))])
features=features.sort_values(['start','WAFER_ID','STAGE']).reset_index(drop=True)
features.to_csv(ROOT/'data/wafer_features.csv',index=False)
(ROOT/'data/splits.json').write_text(json.dumps(splits,indent=2))
audit={'raw_rows_after_dedup':len(d),'wafer_stage_samples':len(features),'unique_wafers':n,'split_counts':features.groupby('split').size().to_dict(),'machine_stage_counts':features.groupby(['split','machine','STAGE']).size().to_dict().__str__(),'chronological_boundaries':[t1,t2],'features_sha256':hashlib.sha256((ROOT/'data/wafer_features.csv').read_bytes()).hexdigest(),'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),'label_columns':list(y),'no_maintenance_labels':True,'no_physical_units':True}
for a,b in [('train','dev'),('dev','test')]:
    assert features.loc[features.split==a,'end'].max()<features.loc[features.split==b,'start'].min()
(ROOT/'results/data_audit.json').write_text(json.dumps(audit,indent=2))
print(json.dumps(audit,indent=2))
