FINAL JUDGE ENTRY: README.md
Final video: deliverables/REFLEX_final_90s.mp4
Industry dashboard: deliverables/REFLEX_customer_benchmark.html
Device R&D extension: deliverables/REFLEX_device_research.html

LATEST: DELAYED-METROLOGY MODEL (V7)
===================================
Run the same server, then open http://127.0.0.1:8765/delay.html
Latest review: deliverables/REFLEX_delay_report.html
Latest video / deck: REFLEX_delay_90s.mp4 and REFLEX_delay_pitch.pptx / .pdf

Actual result, equal every-fifth measurement schedule, mean over five offsets:
Dataset1 / delay5: RMSE 3.53% lower; P90 absolute error 12.05% lower.
Dataset1 / delay20: RMSE 0.12% worse; P90 7.61% lower.
Dataset2 / delays5,20: RMSE 0.52%, 0.20% lower respectively.
The predefined 10% mean RMSE improvement gate FAILED (observed 1.03%).
P90 Dataset1/delay5 conditional95% interval: 1.78 to18.80% improvement.
Repeatedly inspected evaluation data; intervals do NOT correct selection bias.
All failed v4/v5/v6 revisions and development choices are preserved.

The model combines GRAPE, timestamped Kalman residuals, and a Gaussian Bayesian
regime model, with weights updated from originally saved predictions only after
requested labels arrive. Max32 regime hypotheses; not constant total UI memory.
Supports the tested fixed delays and ordered arrivals; variable/out-of-order
feedback and factory wall-clock latency have not been validated.

New test suite (research dependencies): python3 test_delay_model.py
Portable execution (NumPy only): python3 hardware_delayed.py
Full isolated v4-v7 rerun: python3 reproduce_delayed.py
Sources: Adams & MacKay arxiv.org/abs/0710.3742;
posterior-merging inspiration: arxiv.org/abs/2611.03230 (not full Bagel reproduction).
No novel-algorithm or production-qualification claim.

PREVIOUS IMMEDIATE-FEEDBACK VERSION (PRESERVED)
==============================================
REFLEX — adaptive metrology research prototype
=============================================

STATUS
Working local model, browser demo, reproducible experiments and 90-second video.
The original hypothesis DID NOT pass its predefined success criteria.
An exploratory event-triggered schedule improves Dataset 1 at equal label count,
but not convincingly Dataset 2; delayed feedback removes Dataset 1's advantage.
This is not a new foundation model or a production-qualified fab controller.

RUN THE LOCAL DEMO
  python3 -m venv .venv
  .venv/bin/pip install numpy
  .venv/bin/python server.py --port 8765
  Open http://127.0.0.1:8765

No API key, cloud account or GPU is required for the portable demo.
Input: anonymized exported feature vectors. Raw sensor feature extraction,
instrument latency and production release decisions are outside this prototype.
The page makes real local model predictions and updates; the input stream is a
public recording. Offline audit truth does not enter the request policy.

REVIEW FIRST
  deliverables/REFLEX_report.html — full evidence and limitations
  deliverables/REFLEX_pitch.pptx — editable presentation
  deliverables/REFLEX_pitch.pdf — rendered presentation
  deliverables/REFLEX_90s.mp4 — English narration and captions, 90 seconds
  results/evidence.json — machine-readable comparison
  results/delay_sensitivity.csv — deployment stress test

EXPERIMENTS
v1: PHM 2016 CMP, chronological wafer splits, frozen vs adaptive GP baselines.
    Candidate failed. See protocol.json and results/test_metrics.csv.
v2: GRAPE's public datasets, train/valid/test used for fit/development, then
    official unseen split evaluated once. Candidate failed on both datasets.
    See protocol_v2.json and results/stream_unseen_1.csv / _2.csv.
v3: Exploratory event-triggered schedule on the already inspected unseen splits.
    Reuses GRAPE equations. Schedule parameters selected on development.
    Dataset 1: 88 labels, RMSE .21866 vs same-count uniform .28560.
    Dataset 2: 342 labels, RMSE .84085 vs same-count uniform .84927.
    Exploratory block-bootstrap intervals do not remove model-selection bias.
    Five-sample metrology delay removes the Dataset 1 advantage.

BASELINE ATTRIBUTION
GRAPE: https://github.com/cheonwoolee/GRAPE
Paper: https://arxiv.org/abs/2611.00806
Pinned commit: cce2d27a092abd9e397d7739e4beb6dfe0ae145e
The portable NumPy implementation follows GRAPE's model equations and includes
a small event-triggered measurement scheduler. Novelty is not established.
We preserve exported feature column order across splits; the upstream evaluation
runner uses a different unseen column order. Published scores are NOT claimed
to be reproduced, and feature export semantics remain independently unverified.

PHM original description:
https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2016/phm-data-challenge-4/
Raw data mirror: https://github.com/akangel0307/PHM-Data-Challenge
Original archive could not be retrieved. Mirror hashes are recorded locally,
but authenticity was not established against an original checksum.

REPRODUCE
  .venv/bin/pip install -r requirements-research.txt
  .venv/bin/python setup_research.py
  .venv/bin/python reproduce.py
This creates an isolated timestamped run and preserves the original results.
The original CMP data is ~196 MB; it is not included in the portable bundle.
  .venv/bin/python test_runtime.py
  .venv/bin/python hardware_benchmark.py

BUSINESS
First customer / CMP data-access partner and prices are hypotheses, not signed
customers or validated willingness to pay. Proposed pilot KRW5–10m, integration
KRW20–50m. Value and repeatability must be demonstrated before pricing production.

HACKATHON
Built during the published 11 Nov 2026 event build window.
This package does not imply event registration, public release or submission.
Private repository access alone does not allow judges to view the code.

HARDWARE
M5 Pro MacBook: local experiments, model export, UI and video assembly.
M4 Pro Mac mini: isolated environment, independent portable execution check.
M4 Mac mini: second independent execution check; metrics agree at displayed precision.
DGX: not used; saved host was unresolved and another node rejected the saved
login user. No claim of GPU training or GMI credit usage is made.
