# Session capture receiver 01 — actual verification

2 October 2026. Baseline 701ab51. Source-only local receiver; no actual assistant registered, native command changed or private transcript read. No provider call, new dependency or inference. OpenAI Docs skill guided official hook/coverage lookup; capture envelopes are not assumed to guarantee all-account coverage.

## Actual results

- Initial test command from repository root failed import resolution (`memory_worker` unavailable). Corrected the working directory to `sidecar`, matching the source package layout; no global PYTHONPATH change.
- First focused run: 12 receiver tests passed, including real independent hook subprocess invocations and exact-byte preservation across restart.
- First complete source suite with two additional checks: 54 discovered, one concurrency failure, two frozen-worker tests skipped because no frozen executable was selected. Concurrent hooks exposed the 0.2-second lock timeout being shorter than the default polling interval. Failed-process cleanup also emitted unclosed-stream warnings.
- Fix: one-second bounded lock acquisition with explicit 0.05-second polling; test cleanup closes owned child streams. Existing portalocker 4.4.0 API reused. No provider retry or indefinite wait.
- Final complete source suite: **54 discovered, 52 passed, two skipped**, 14.669 seconds. All **14 capture tests** passed. No test failures or stream warnings in the final run.
- After final no-replace publication hardening (Windows rename; POSIX hard link), the focused capture suite was rerun: **14 passed**, 1.768 seconds. The Windows publication path ran; POSIX is not verified on this machine. Final `git diff --check` passed.

Actual source command, from `D:/Projects/mind-palace/sidecar`:

```powershell
../.tools/probe-venv/Scripts/python.exe -m unittest discover -s tests -v
```

Covered: provider-separated identities, resumed/appended revisions, duplicate snapshots across process restart, simultaneous hook processes, exact UTF-8/CRLF preservation, inert script-like text, incomplete tails, empty input, paused consent and pause during source read, path escape/link rejection, malformed complete records, unsupported events, missing transcripts, bounded input, tamper preservation and empty stdout/redacted diagnostics.

Synthetic transcript JSON objects are deliberately generic; this proves raw archiving, not normalization of actual Claude/Codex message roles. No tool-generated fixture is labelled a real provider transcript. Windows symlink guard test mocks the link predicate; it does not claim actual symlink/junction integration coverage. Atomic rename/fsync and owned-child subprocess paths ran on the actual Windows filesystem. No source transcript is written by the receiver.

## Remaining gates

Dedicated frozen capture entry point, desktop opt-in/pause/status UI, config-preserving hook setup, real synthetic-client probe, history scan and missed-event recovery, disk quota/delta retention, exclusions/deletion, format-specific normalization, source-provenance migration/canonical ingestion, indexing/retrieval and actual model inference remain pending. Current desktop executable is unchanged and does not start this receiver. No all-session ChatGPT/Claude coverage claim.

No Angular/Rust/native WebView regression was rerun for this source-only separate entry point; current native worker resources remain unchanged. Files/tests use only temporary synthetic data and are cleaned up by the test harness. Source-only capture is not an installable or usable end-user integration yet.
