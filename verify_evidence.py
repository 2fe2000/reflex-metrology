"""Independent checks from saved predictions, and content integrity for judge artifacts."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
s=json.loads((R/'results/customer/summary.json').read_text())
assert s['protocol_sha256']==hashlib.sha256((R/'protocol_customer_benchmark.json').read_bytes()).hexdigest()
for ds in [1,2]:
    a=np.load(R/f'results/customer/replays_{ds}.npz');v=np.load(R/f'results/v7/predictions_{ds}.npz');y=a['truth']
    for r in [r for r in s['frontier'] if r['dataset']==ds]:
        e=np.abs(a[f"{r['method']}_d{r['delay']}_p{r['period']}"]-y)
        np.testing.assert_allclose(np.sqrt(np.mean(e**2,axis=1)).mean(),r['rmse'],rtol=1e-12)
        np.testing.assert_allclose(np.quantile(e,.9,axis=1).mean(),r['p90'],rtol=1e-12)
        np.testing.assert_allclose(r['queries'],len(y)/r['period'])
        if r['method']=='reflex' and r['period']==5:
            for phase in range(5):np.testing.assert_allclose(a[f"reflex_d{r['delay']}_p5"][phase],v[f"delayed_ensemble_d{r['delay']}_p{phase}"],rtol=1e-10,atol=1e-10)
for r in s['conditions']:
    b,c=r['same_budget']['exceedance_rates'].values()
    np.testing.assert_allclose((1-c/b)*100,r['same_budget']['exceedance_reduction_pct'])
    for half in r['half_measurements'].values():assert half['ci_pass']==(half['ci95']['rmse'][1]<=1.02 and half['ci95']['p90'][1]<=1.05)
assert not s['primary_pass']
manifest=R/'submission_manifest.json'
if manifest.exists():
    entries=json.loads(manifest.read_text())['files']
    for entry in entries:
        p=R/entry['path'];assert p.resolve().is_relative_to(R.resolve());assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],f'Hash mismatch: {p}'
    print('Verified',len(entries),'content hashes')
inverse=R/'results/inverse/summary.json'
if inverse.exists():
    inv=json.loads(inverse.read_text())
    for t in inv['traces']:
        assert len(t['queried_indices'])==len(set(t['queried_indices']))==32
        assert max(t['queried_indices'])<192
        assert t['queried_indices'][:8]==t['initial_indices']
        best=np.array([x['best_loss'] for x in t['trace']]);assert np.all(np.diff(best)<=1e-15)
    assert inv['failed_simulations']==0
print('Verified all40 customer means,20 matching delayed replays, gates and search splits.')
