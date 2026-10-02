# Step 02 — local model diagnostic

Date: 2 October 2026. Complete Step 02 gate NOT passed; no production model selected.

Verified official llama.cpp b11342 Windows x64 CPU ZIP against release SHA256 cc6f3ac938988f6ed4ce204b119d6d1ffe59342cb3157adef20e8132681acd8d. Executed version/help: build 11342, commit f1cee9941, Clang 20.1.8. Selected executable hash is separately locked in config/models.json. Preserved runtime support DLLs and LLVM OpenMP license in ignored .tools/llama-b11342/bin. Full release attribution remains pending.

Downloaded official Qwen Q8_0 artifacts from exact model repository revisions and checked byte sizes/SHA256 before each run. Official cards identify Apache-2.0. No login, subscription, provider key or inference service was used. Downloads use internet; inference requests use direct 127.0.0.1 HTTPConnection, which does not honor proxy environment settings. Native outbound-network auditing is still pending, not claimed proven by loopback request code.

Settings: CPU only, 4 threads, low process priority, context 2048, one slot, temperature 0, seed 42, 128 output tokens, thinking disabled, schema-constrained JSON. Random process-local authentication key passed by environment (never logged or put in command line); unauthenticated /v1/models returned 401 for both candidates. Health is public per runtime design. Web UI, agent tools and MCP proxy explicitly disabled; provider/LLAMA settings do not inherit from the developer environment. Runtime started hidden and terminated in finally with bounded kill fallback. No unrelated process was stopped.

## Repeat measurements

| Candidate       |   Model bytes | Fresh-process load seconds | Median request seconds | Peak process working-set bytes | State + substring evidence passes |
| --------------- | ------------: | -------------------------: | ---------------------: | -----------------------------: | --------------------------------: |
| Qwen3 0.6B Q8_0 |   639,446,688 |                      1.187 |                 1.0155 |                    982,011,904 |                              2/10 |
| Qwen3 1.7B Q8_0 | 1,834,426,016 |                      1.623 |                 3.0545 |                  2,176,876,544 |                              4/10 |

Initial runs had the same case scores; median times were 0.935 and 3.412 seconds. Repeat results add Windows GetProcessMemoryInfo peak working-set measurements and runtime executable checksum validation. OS disk cache was NOT cleared, so fresh-process load is not cold-disk performance. Per-request prompt caching is enabled by the inspected runtime default. Hardware has approximately 16 GB physical RAM; these are current-machine measurements, not minimum requirements or full app memory use.

Exact synthetic outputs, usage and timings are in model-probe-results.json. The scorer requires the expected state plus an exact source substring (null for missing-subject abstention), but does not prove semantic entailment. Both models cited assistant text rather than user approval in the NgRx case while receiving substring credit; this is a known optimistic scoring limitation, not acceptable production evidence. Do not advertise 20%/40% as general model accuracy. Cases are prototype development fixtures, not the held-out Step 25 evaluation set.

Observed failures include false confirmation of a proposal by 0.6B, wrong replacement/task classification, missing evidence and proposal-state confusion. Keep model selection pending, preserve failures, improve prompts/evidence checking before retesting, and never weaken the release gates to fit these results. Under G05, manual review, portable records and keyword search can proceed independently of model quality. No paid/cloud fallback or larger-model download was activated.

Still pending: embeddings with the dedicated model, request cancellation/timeouts under long generation, process/network audit, larger held-out evaluation, combined worker/runtime integration, native UI, clean-machine/Mac packaging and full-model installer delivery size. Test helper/unit success is not inference quality success.

Full diagnostic/helper regression: 16/16 tests passed in 76.552 seconds (no skips), including all three frozen diagnostics and five model-helper cases. Inference case scores remain 2/10 and 4/10; the helper suite does not convert those failures into a passed model gate. Model probe process exit 0 only indicates completed measurement, not quality approval.
