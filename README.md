# REFLEX — Semiconductor Process Intelligence

**A local, delay-aware virtual-metrology research prototype for semiconductor manufacturing.** Process results arrive after subsequent samples have already run. REFLEX stores the original prediction and timestamp, then updates a small ensemble only when the corresponding measurement arrives.

[![Evidence verification](https://github.com/2fe2000/reflex-metrology/actions/workflows/evidence.yml/badge.svg)](https://github.com/2fe2000/reflex-metrology/actions/workflows/evidence.yml)

## Judge review — start here

1. [Watch / download the 90-second final video](deliverables/REFLEX_final_90s.mp4): process → feedback delay → model → actual replay → all-condition evidence → customer value and device-R&D vision.
2. [Download the standalone industry and benchmark dashboard](deliverables/REFLEX_customer_benchmark.html). Open the downloaded HTML in a browser; interactive charts work offline.
3. [Editable pitch deck](deliverables/REFLEX_delay_pitch.pptx) · [PDF](deliverables/REFLEX_delay_pitch.pdf) · [Full model report](deliverables/REFLEX_delay_report.html).
4. [Raw customer benchmarks](results/customer/means.csv) · [locked protocol](protocol_customer_benchmark.json) · [machine-readable results and intervals](results/customer/summary.json).
5. [Build record](provenance/build_record.json) · [commit history](../../commits/main) · [GitHub verification runs](../../actions) · [content hashes](submission_manifest.json).

The repository remains **private by owner choice**. Judges need access or a later public release. No hackathon submission has been made by this repository upload.

## Why the problem matters

Virtual metrology already has industrial demand. SK hynix reported **over 50 million virtually measured wafers and 29% improvement in process variability** with Panoptes VM in February 2024. Its 2026 research with Gauss Labs extends to tool-to-tool matching, early anomaly diagnosis and explainable overlay metrology. These are **other companies' results**, not REFLEX performance or customers.

- [SK hynix, 2024 deployment evidence](https://news.skhynix.com/en/gauss-labs-and-sk-hynix-present-ai-papers-at-spie-al-2024/)
- [SK hynix, 2026 production research](https://news.skhynix.com/en/sk-hynix-and-gauss-labs-present-ai-based-semiconductor-virtual-metrology-research-at-spie-al-2026/)
- [NIST, 2025 semiconductor data-sharing and virtual-metrology workshop](https://www.nist.gov/publications/artificial-intelligence-open-and-scaled-data-sharing-semiconductor-manufacturing)

**Initial customer hypothesis:** a process/metrology team or equipment OEM with one chamber and real delayed measurements. Validate on a fresh chronological stream in shadow mode; agree physical quality tolerances and false-negative limits before changing sampling. A pilot price of KRW5–10M and integration price of KRW20–50M are unvalidated commercial hypotheses.

**Expansion vision:** use accumulated measurements and physics simulations to propose better process conditions and device structures. This requires target electrical specifications, calibrated device physics, feasible fabrication bounds, and physical validation. Cross-chamber learning and new semiconductor product improvement are not demonstrated by the metrology benchmark.

## What the benchmark actually shows

Frozen V7; equal every-fifth measurement schedule; mean over all five offsets. Large-error thresholds were fixed using development data before this additional run. Delays are sample counts, not factory wall-clock latency.

| Dataset / delay | RMSE reduction | P90 error reduction | Large-error frequency reduction |
|---|---:|---:|---:|
| 1 / 5 | 3.53% | 12.05% | 18.81% |
| 1 / 20 | **−0.12%** | 7.61% | 11.37% |
| 2 / 5 | 0.52% | 0.55% | 6.42% |
| 2 / 20 | 0.20% | 0.07% | 2.18% |

Dataset1/delay5 large-error frequency: **15.50% → 12.58%, a 2.92-percentage-point difference**. Conditional 95% interval for relative reduction: **5.42–30.88%**. This is a normalized prediction-error proxy, **not a defect or yield result**. Intervals for the delay20 conditions include zero.

The original 10% mean-RMSE target **failed**: observed mean improvement was 1.03%. A new 50%-fewer-measurements test also **failed overall**. Dataset2 met the specified noninferiority margins, but the GRAPE baseline also passed; those savings cannot be attributed to REFLEX.

The complete measurement/accuracy frontier contains **40 condition means, all sampling offsets and saved predictions**. No losing condition is removed. The evaluation streams were repeatedly inspected during development, so these are exploratory results. Block-bootstrap intervals do not correct selection or reuse bias.

## Model and actual implementation

- Public GRAPE equations as the base comparator and one expert.
- Timestamped Kalman residual estimation and bounded Gaussian regime hypotheses.
- Expert weights updated from originally saved predictions only when a requested label arrives.
- NumPy-only deployment; at most 32 regime hypotheses. Total UI history is not constant-memory.
- Fixed, ordered feedback delays validated; variable or out-of-order arrivals are not yet supported.

This is an independently implemented research combination, **not an established novel base algorithm**. The upstream exported feature-column semantics remain independently unresolved; we retain consistent column order. We do not claim reproduction of the authors' published scores.

## Run the live demo

Requires **Python 3.11 or newer**. To use the model without the dashboard:

```sh
git clone https://github.com/2fe2000/reflex-metrology.git
cd reflex-metrology
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/reflex --model models/reflex_delayed_1.json --input examples/events.jsonl
```

This executes 12 public recorded samples and delivers two delayed measurements.
The installed `reflex` command also works outside the checkout with absolute paths.
It emits JSONL; inference requires only NumPy, no API key, GPU or hosted service.
Repository access is still required while private. [Python API, event schema and integration limits](docs/SDK.md).

To run the dashboard:

```sh
python3 -m venv .venv
.venv/bin/pip install . numpy==2.4.6 pandas
.venv/bin/python server.py --port 8765
```

Open `http://127.0.0.1:8765/delay.html` for actual local inference, or `http://127.0.0.1:8765/benchmark.html` for industry evidence and complete comparisons. Input is a public recorded-feature stream. Offline audit truth is never passed to the model before its requested measurement arrives.

## Verify and reproduce

```sh
.venv/bin/python -m unittest -v test_runtime test_delay_model test_device_surrogate test_sdk
.venv/bin/python verify_evidence.py
```

Full research dependencies and pinned upstream data:

```sh
.venv/bin/pip install -r requirements-research.txt
.venv/bin/python setup_research.py
.venv/bin/python reproduce_delayed.py
.venv/bin/python reproduce_customer.py
```

Reruns are isolated under `reruns/`; original results are preserved. Earlier v1–v6 failures and sensitivity results remain available. See [README.txt](README.txt) for the complete earlier experiment record.

## Device R&D extension

[Open the standalone R&D dashboard](deliverables/REFLEX_device_research.html): actual search replay, I–V curves, data-growth comparison and live local GP posterior inference.

At 32 queried designs, standard GP expected improvement reduced mean target log-current MSE 97.19% versus paired random search, winning 5/5 seeds. This is **target matching in a basic simulated diode**, not 97% better chip performance. The32-label model improves held-out prediction RMSE 30.03% versus its 8-label version; random sampling produces a better global 32-label predictor, so the result does not establish broad model superiority.


[Research code](research/inverse_design.py) implements a small **physics simulator → data → GP surrogate → next design** loop using [DEVSIM](https://github.com/devsim/devsim). It matches a prescribed I–V curve by selecting p/n doping and length of a basic 1D silicon diode. Standard Gaussian-process expected improvement is compared with paired random search at equal data budgets. It is a separate research extension, not V7's metrology benchmark and not a fabricated or market-leading chip.

The simulator-generated pool includes a held-out surrogate test split, full query histories and a refined-mesh check. The complete pool-generation cost must be counted; offline query comparisons are not measured fab or wall-clock savings. [Protocol](protocol_inverse_design.json) · [results](results/inverse/summary.json).

Research context: [2026 HBT active-learning inverse design](https://doi.org/10.1007/s10825-026-02510-x) and [AgenticTCAD, DATE2026](https://arxiv.org/abs/2512.23742). Those papers establish related prior work; their scores are not ours.

Run the device experiment in an isolated copy to preserve results:

```sh
.venv/bin/pip install devsim==2.11.2 numpy==2.4.6 scipy==1.17.1 scikit-learn==1.9.1
.venv/bin/python research/reproduce_inverse.py
```

## Event provenance and reuse

The [published event](https://luma.com/compiled-poy7) permits existing models, APIs and libraries, requires the product to be built during the event, and requests a 90-second video and GitHub URL. Published hacking window: **2026-11-11 18:45–22:45 Taipei (UTC+8), equivalent to 10:45–14:45 UTC**. Schedule is subject to change.

GitHub reports repository creation at **2026-11-11 12:55:11 UTC**. Commit records, content hashes and GitHub CI server timestamps support the build timeline. Git timestamps and locally written metadata alone cannot prove the original authorship time of every file. No backdating or synthetic commit history is used. Earlier protocol timestamp placeholders were corrected transparently in [the correction record](results/protocol_timestamp_correction.json).

Existing resources: GRAPE code/data, scientific Python, DEVSIM and cited research. Event work: portable deployment, causal delayed-feedback replay, model combination, comparative evaluation, interface, narrative, motion graphics and device-loop prototype. All attribution and available license notices are retained under [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES).

Hardware: M5 Pro local work; M4 Pro independent V7 execution; M4 earlier-version execution. DGX was **not used** because the saved hostname did not resolve and an alternative node rejected the saved login user. No GMI credit or GPU-training claim is made.

## GStack / GBrain / Transpose consideration

GStack's `devex-review` workflow and actual `gstack-error-capture` executable were used to audit first-run setup and CLI errors. The resulting work added an installable inference SDK, an ordered-feedback JSONL example, causality/parity tests and CI execution outside the source directory. [Usage evidence and scope](provenance/gstack/README.md). GStack is development tooling, not the metrology predictor. GBrain has not been integrated. Transpose Platform is the event organizer/track, not a model runtime dependency.
