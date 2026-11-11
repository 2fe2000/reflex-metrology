# GStack usage evidence

REFLEX used the `devex-review` workflow and the real `gstack-error-capture` executable from [garrytan/gstack](https://github.com/garrytan/gstack), pinned to `f0cd9f8c4b453c1eadd714e4149174ee01179eae`.

The workflow was read from `devex-review/SKILL.md`. Its global skill-start installation was absent, so the review continued in the skill's documented degraded mode. No onboarding, telemetry, GBrain integration, or full GStack deployment is claimed. Transpose Platform is an event organizer, not a runtime component. GStack is development tooling; it is not part of the predictor.

## Work performed

- Added an installable Python package and JSONL CLI, with prediction and delayed measurement ingestion as separate operations.
- Documented units, input schema, bounded pending storage, timestamp ordering, validation errors, and deployment limits in [SDK.md](../../docs/SDK.md).
- Added SDK replay equivalence and rejected-feedback/state-integrity tests. The suite contains 15 tests.
- Ran the actual GStack error-capture executable on CLI help and an invalid invocation. The latter correctly exits 2 for missing required arguments. See [help receipt](cli_help.json) and [invalid invocation receipt](cli_invalid_flag.json); neither capture found secrets.
- Verified a fresh temporary virtual environment from a copy of versioned files plus the SDK additions: package installation, CLI invoked outside the checkout, 12 predictions, 2 delayed updates, and all 15 tests. [Machine-readable receipt](clean_install.json). Total measured command time was 27.861 seconds on this Mac, with cached package wheels; this is not a universal installation-time benchmark.
- Added the same installed-CLI and test checks to GitHub Actions. Remote CI results, rather than local passes, determine cross-platform verification.

## Review outcome: completed with limitations

This was a focused setup/API/error-message review, not a complete eight-dimension product audit. No aggregate GStack score is claimed. A prior Linux reference comparison failed at a tolerance below float32 cross-platform arithmetic precision; the reference comparison now uses `rtol=atol=1e-6`. Causality tests remain exact. This changes numerical portability tolerance, not benchmark values.

The SDK currently requires supplied preprocessing and an explicit exported model path; it does not provide raw sensor integration, equipment control, out-of-order feedback rollback, or durable state recovery. The public artifacts are research demonstrations, not factory-qualified products.

All changes retain their actual Git commit and CI timestamps; this record does not assert that later edits occurred during the event.
