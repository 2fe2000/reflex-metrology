import json,unittest
from pathlib import Path
import numpy as np
from research.device_surrogate import DeviceSurrogate
R=Path(__file__).resolve().parent
class DeviceTests(unittest.TestCase):
 def test_exported_posterior_matches_independent_sklearn_evaluation(self):
  a=json.loads((R/'models/research_device_surrogate.json').read_text());r=json.loads((R/'results/inverse/surrogate_reference.json').read_text());m=DeviceSurrogate(a)
  np.testing.assert_allclose(m.predict(r['X']),r['predictions'],rtol=1e-10,atol=1e-10)
  self.assertEqual(len(a['training_X']),32);self.assertTrue(all(i<192 for i in a['acquired_design_indices']))
 def test_rejects_invalid_or_extrapolating_inputs(self):
  m=DeviceSurrogate(json.loads((R/'models/research_device_surrogate.json').read_text()))
  for X in [[[2,0,0]],[[float('nan'),0,0]],[[0,0]]]:
   with self.assertRaises(ValueError):m.predict(X)
if __name__=='__main__':unittest.main()
