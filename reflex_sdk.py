"""V7 inference with explicit, ordered feedback; no audit labels in predictions."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from delay_model import DelayedEnsemble


class ReflexError(ValueError):
    def __init__(self, code, message, fix):
        self.code, self.fix = code, fix
        super().__init__(message)


class ReflexModel:
    """One instance per independent stream. Targets retain artifact training units.

    Predict timestamps must increase. Feedback must arrive in source-timestamp
    order. This wrapper does not add out-of-order filtering or retrain V7.
    """
    def __init__(self, artifact, max_pending=4096):
        if isinstance(artifact, (str, Path)):
            artifact = json.loads(Path(artifact).read_text())
        if artifact.get('version') != 7:
            raise ReflexError('MODEL_VERSION', 'Only V7 artifacts are supported.',
                              'Use models/reflex_delayed_1.json or reflex_delayed_2.json.')
        if isinstance(max_pending, bool) or not isinstance(max_pending, int) or max_pending < 1:
            raise ReflexError('PENDING_LIMIT', 'max_pending must be a positive integer.', 'Set max_pending=4096.')
        self.model = DelayedEnsemble(artifact['base'], artifact['spec'], artifact['config'],
                                    artifact['experts']['kalman'], artifact['experts']['regime'])
        self.feature_count = len(artifact['base']['mean'])
        self.max_pending = max_pending
        self.pending = {}
        self.last_prediction = -1
        self.last_observation = -1

    @staticmethod
    def _timestamp(t):
        if isinstance(t, bool) or not isinstance(t, int) or t < 0:
            raise ReflexError('TIMESTAMP', 'timestamp must be a nonnegative integer sample index.',
                              'Use increasing sample indices: 0, 1, 2, ...')

    def predict(self, features, context, timestamp, request_measurement=False):
        self._timestamp(timestamp)
        if timestamp <= self.last_prediction:
            raise ReflexError('PREDICTION_ORDER', 'Prediction timestamps must strictly increase.',
                              'Send each sample once, in chronological order.')
        if not isinstance(context, str) or not isinstance(request_measurement, bool):
            raise ReflexError('INPUT_TYPE', 'context must be a string and request_measurement a boolean.',
                              'Use the context encoding of the selected artifact and true/false.')
        try:
            x = np.asarray(features, dtype=float)
        except (TypeError, ValueError):
            raise ReflexError('FEATURE_VALUES', 'Features must be numeric.', 'Send a finite numeric feature vector.') from None
        if x.shape != (self.feature_count,) or not np.isfinite(x).all():
            raise ReflexError('FEATURE_SHAPE', f'Expected {self.feature_count} finite features in training column order.',
                              'Preserve the artifact feature schema; reject missing or nonfinite sensor values upstream.')
        if request_measurement and len(self.pending) >= self.max_pending:
            raise ReflexError('PENDING_FULL', 'Pending measurement buffer is full; sample was not consumed.',
                              'Deliver outstanding feedback or explicitly discard a canceled request before retrying.')
        scaled = self.model.grape.transform(x)
        prediction, experts = self.model.predict(scaled, context, timestamp)
        if request_measurement:
            self.pending[timestamp] = (scaled.copy(), context, experts.copy())
        self.last_prediction = timestamp
        return {'timestamp': timestamp, 'prediction': prediction,
                'measurement_requested': request_measurement, 'pending': len(self.pending),
                'weights': self.model.weights.tolist()}

    def observe(self, timestamp, target):
        self._timestamp(timestamp)
        if timestamp <= self.last_observation:
            raise ReflexError('FEEDBACK_ORDER', 'Feedback is duplicate or out of source-timestamp order.',
                              'Buffer arrivals upstream and deliver in source order; this runtime does not support rollback.')
        if timestamp not in self.pending:
            raise ReflexError('UNKNOWN_MEASUREMENT', 'No retained prediction exists for this timestamp.',
                              'Call predict with request_measurement=True before delivering its measured target.')
        if isinstance(target, bool) or not isinstance(target, (float, int)) or not np.isfinite(target):
            raise ReflexError('TARGET_VALUE', 'The measured target must be a finite number.',
                              'Use the same target units and preprocessing as model training.')
        x, context, original_predictions = self.pending[timestamp]
        self.model.observe(x, context, timestamp, float(target), original_predictions)
        del self.pending[timestamp]
        self.last_observation = timestamp
        return {'observed_timestamp': timestamp, 'pending': len(self.pending),
                'weights': self.model.weights.tolist()}

    def discard(self, timestamp):
        """Cancel a retained request without inventing a target or updating weights."""
        self._timestamp(timestamp)
        if timestamp not in self.pending:
            raise ReflexError('UNKNOWN_MEASUREMENT', 'No pending request exists.', 'Discard only a pending timestamp.')
        del self.pending[timestamp]


def main(argv=None):
    parser = argparse.ArgumentParser(description='REFLEX V7: ordered JSONL predict/observe events. Research runtime; no device control.')
    parser.add_argument('--model', required=True, help='V7 JSON model artifact path')
    parser.add_argument('--input', required=True, help='JSONL event file; use - for stdin')
    args = parser.parse_args(argv)
    line_no = 0
    try:
        runtime = ReflexModel(args.model)
        stream = sys.stdin if args.input == '-' else open(args.input)
        try:
            for line_no, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                event = json.loads(line)
                kind = event.pop('type')
                if kind not in ('predict', 'observe'):
                    raise ReflexError('EVENT_TYPE', 'Unknown event type.', 'Use type=predict or type=observe; see examples/events.jsonl.')
                print(json.dumps(getattr(runtime, kind)(**event), allow_nan=False), flush=True)
        finally:
            if stream is not sys.stdin:
                stream.close()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # Never echo the raw input, feature values, or arbitrary file contents.
        detail = str(exc) if isinstance(exc, ReflexError) else 'Cannot load the artifact or parse this event.'
        print(json.dumps({'error': getattr(exc, 'code', 'INPUT_ERROR'), 'line': line_no,
                          'message': detail, 'fix': getattr(exc, 'fix', 'Check --model, --input and the documented JSONL schema.'),
                          'recovery': 'Earlier output events were processed in memory. Correct input and replay from a new process.'}), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
