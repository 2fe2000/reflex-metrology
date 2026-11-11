"""Persist acquired training data and posterior parameters, excluding test labels."""
import json,sys
from pathlib import Path
import numpy as np
from inverse_design import gp
R=Path(__file__).resolve().parents[1]
s=json.loads((R/'results/inverse/summary.json').read_text());d=json.loads((R/'results/inverse/dataset.json').read_text());t=next(t for t in s['traces'] if t['method']=='expected_improvement' and t['seed']==11)
indices=t['queried_indices'];X=np.array([d['records'][i]['x'] for i in indices]);Y=np.array([d['records'][i]['log_currents'] for i in indices]);m=gp(X,Y)
a={'schema_version':1,'source':'DEVSIM2.11.2;1Dsilicondiode;simulationonly','acquired_design_indices':indices,'training_X':X.tolist(),'training_Y_log10J':Y.tolist(),'kernel':'Matern52','length_scale':m.kernel_.k2.length_scale.tolist(),'alpha':m.alpha_.tolist(),'y_mean':m._y_train_mean.tolist(),'y_std':m._y_train_std.tolist(),'input_mapping':{'log10_Na':'16+2*x0','log10_Nd':'16+2*x1','length_um':'.1+.9*x2'},'scope':'Reconstructed posterior for sampled32designs. Not trained on heldout64outputs. Predict only inside normalized[0,1]^3.'}
(R/'models/research_device_surrogate.json').write_text(json.dumps(a,indent=2))
probes=np.random.default_rng(123).random((20,3));(R/'results/inverse/surrogate_reference.json').write_text(json.dumps({'X':probes.tolist(),'predictions':m.predict(probes).tolist()},indent=2))
print('Saved32-point learned GP posterior;20 independent numerical reference probes')
