# Using the REFLEX model

This is an executable research model and a streaming interface. It is not a qualified fab controller. The included models expect the exact ordered, exported GRAPE dataset features and normalized target units. Physical sensor names/units have not been independently resolved. Do not feed arbitrary equipment readings to these pretrained artifacts and interpret the outputs as nanometres or yield.

## Python: predict now, update when the measurement arrives

Run from the repository after `python -m pip install .`:

```python
import json
from reflex_sdk import ReflexModel

model = ReflexModel("models/reflex_delayed_1.json")
events = [json.loads(line) for line in open("examples/events.jsonl")]
for event in events:
    operation = event.pop("type")
    if operation == "predict":
        result = model.predict(**event)
        print(result["timestamp"], result["prediction"])
    else:
        model.observe(**event)
```

`predict(features, context, timestamp, request_measurement=False)` receives **no target**. It standardizes features with the exported training mean/scale. With `request_measurement=True`, it retains the original expert predictions and features. `observe(timestamp, target)` learns from that saved record when the measurement arrives. Measurement selection belongs to the caller; the benchmark uses every fifth sample.

The JSONL CLI uses the same keyword arguments with `"type": "predict"` or `"type": "observe"`. A complete working event stream is in `examples/events.jsonl`. Use `--input -` for streaming stdin. Output goes to stdout; failures exit 2 with error detail on stderr. Previous events may already have produced output; correct the input and replay in a fresh process rather than appending a retry to a partially processed stream.

## Input and lifecycle contract

- Python 3.11+, NumPy 2.x. `pip install .` installs the runtime; model JSON files are explicit inputs from this repository.
- Feature count is `model.feature_count`. All values must be finite and columns must match training order. Unknown context strings use existing GRAPE fallback behavior; this does not establish transfer to a new chamber.
- `timestamp` is a nonnegative **sample index**, not seconds. Predictions must strictly increase. Arrivals must be delivered in source-timestamp order. Variable wall-clock delays can be buffered externally; out-of-order updates are rejected, not silently approximated.
- One instance per independent stream. State starts fresh on construction; no persistence/checkpoint contract is implemented yet.
- Only requested measurements are retained. Default pending limit is 4,096. Full buffers reject the new sample before consuming it. `discard(timestamp)` cancels a pending request without updating the model.
- Pending records are bounded, but GRAPE context dictionaries can grow with distinct context keys. Use a bounded equipment-context vocabulary; do not claim total memory is constant.
- This interface supplies predictions only. It does not connect to a PLC, alter recipes, move a robot or bypass equipment interlocks.

## Before a factory pilot

Define the chamber-specific sensor schema, quality target and units; fit/export the base predictor on chronologically separated local training data; validate against a fresh stream; align each measurement with its original sample; establish operating bounds and a fallback. The public dataset artifacts are examples of this contract, not pretrained universal semiconductor models.

## Reproducibility

`test_sdk.py` checks exact equality with the existing delayed replay on the same machine for both datasets, plus invalid inputs, duplicate feedback and bounded buffering. Cross-platform reference comparisons allow float32-level differences (`atol=rtol=1e-6`) because the exported base predictor uses float32; RMSE must still agree to six decimal places. Causality tests remain exact. Earlier Linux CI failed at an inappropriate float64 tolerance; this correction does not change the model, saved predictions or reported scores.

## Error codes

`MODEL_VERSION`, `PENDING_LIMIT`, `TIMESTAMP`, `PREDICTION_ORDER`, `INPUT_TYPE`, `FEATURE_VALUES`, `FEATURE_SHAPE`, `PENDING_FULL`, `FEEDBACK_ORDER`, `UNKNOWN_MEASUREMENT`, `TARGET_VALUE`, `EVENT_TYPE`, `INPUT_ERROR`. SDK validation raises `ReflexError` with `code` and `fix`; the CLI adds the input line and recovery guidance. Invalid inputs and raw sensor vectors are not echoed.
