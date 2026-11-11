"""Meaningful invariants: causal label access, portable equality, live API replay."""
import json,unittest
from pathlib import Path
import numpy as np
from portable_runtime import LiveStream
ROOT=Path(__file__).resolve().parent
class CausalityTests(unittest.TestCase):
 def test_unmeasured_labels_cannot_change_predictions_or_requests(self):
  a=json.loads((ROOT/'models/reflex_1.json').read_text());d=np.load(ROOT/'models/replay_1.npz',allow_pickle=False)
  first=LiveStream(a,d['X'],d['y'],d['keys']).advance(len(d['y']))
  mask=np.array([h['query'] for h in first['history']]);changed=d['y'].copy();changed[~mask]+=10000
  second=LiveStream(a,d['X'],changed,d['keys']).advance(len(changed))
  np.testing.assert_array_equal(mask,[h['query'] for h in second['history']])
  np.testing.assert_array_equal([h['prediction'] for h in first['history']],[h['prediction'] for h in second['history']])
 def test_prediction_precedes_own_measurement(self):
  a=json.loads((ROOT/'models/reflex_1.json').read_text());d=np.load(ROOT/'models/replay_1.npz',allow_pickle=False);changed=d['y'].copy();changed[0]+=10000
  first=LiveStream(a,d['X'],d['y'],d['keys']).advance(1);second=LiveStream(a,d['X'],changed,d['keys']).advance(1)
  self.assertEqual(first['history'][0]['prediction'],second['history'][0]['prediction'])
 def test_portable_matches_recorded_upstream_equations(self):
  for ds in [1,2]:
   a=json.loads((ROOT/f'models/reflex_{ds}.json').read_text());d=np.load(ROOT/f'models/replay_{ds}.npz',allow_pickle=False);out=LiveStream(a,d['X'],d['y'],d['keys']).advance(len(d['y']));ref=json.loads((ROOT/f'results/burst_replay_{ds}.json').read_text())
   np.testing.assert_allclose([h['prediction'] for h in out['history']],ref['prediction'],atol=1e-6,rtol=1e-6)
   np.testing.assert_array_equal([h['query'] for h in out['history']],ref['queried'])
if __name__=='__main__':unittest.main()
