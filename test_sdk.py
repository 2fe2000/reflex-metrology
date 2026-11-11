import json
import unittest
from pathlib import Path
import numpy as np
from reflex_sdk import ReflexModel, ReflexError
from delayed_runtime import DelayedStream

ROOT = Path(__file__).resolve().parent


class SDKTest(unittest.TestCase):
    def test_saved_stream_equivalence(self):
        for ds, delay in [(1, 5), (2, 20)]:
            artifact = json.loads((ROOT / f'models/reflex_delayed_{ds}.json').read_text())
            data = np.load(ROOT / f'models/replay_{ds}.npz')
            sdk = ReflexModel(artifact)
            predictions = []
            for i, x in enumerate(data['X']):
                if i-delay in sdk.pending:
                    sdk.observe(i-delay, float(data['y'][i-delay]))
                predictions.append(sdk.predict(x, str(data['keys'][i]), i, i % 5 == 0)['prediction'])
            reference = DelayedStream(artifact, data['X'], data['y'], data['keys'], delay=delay).advance(len(data['y']))
            np.testing.assert_allclose(predictions, [r['prediction'] for r in reference['history']], rtol=0, atol=0)

    def test_invalid_feedback_does_not_consume_request(self):
        m = ReflexModel(ROOT / 'models/reflex_delayed_1.json')
        x = m.model.grape.mean.tolist()
        m.predict(x, 'unknown_context', 0, True)
        weights = m.model.weights.copy()
        with self.assertRaises(ReflexError): m.observe(0, float('nan'))
        self.assertIn(0, m.pending)
        np.testing.assert_array_equal(m.model.weights, weights)
        m.observe(0, 0.5)
        with self.assertRaises(ReflexError): m.observe(0, 0.5)

    def test_shape_order_and_bounded_buffer(self):
        m = ReflexModel(ROOT / 'models/reflex_delayed_1.json', max_pending=1)
        x = m.model.grape.mean.tolist()
        with self.assertRaises(ReflexError): m.predict(x[:-1], 'ctx', 0)
        m.predict(x, 'ctx', 0, True)
        with self.assertRaises(ReflexError): m.predict(x, 'ctx', 0)
        with self.assertRaises(ReflexError): m.predict(x, 'ctx', 1, True)
        self.assertEqual(m.last_prediction, 0)
        m.discard(0)
        m.predict(x, 'ctx', 1, True)
        m.observe(1, 0.5)
        with self.assertRaises(ReflexError): m.observe(0, 0.5)


if __name__ == '__main__': unittest.main()
