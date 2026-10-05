# Codex two-minute verification — 4 October 2026

## Authority and scope

Correction: the user did not verify or confirm step 1. The earlier user-confirmed trust statement below is withdrawn. The two-minute duration change remains valid; actual persisted trust requires a separate test without bypass.

The user confirms step 1 is OK and replaces the one-hour test with two minutes. Normal hook trust was not verified in this run; separate actual verification is recorded in codex-trust-11.md. No one-hour test runs.

The installed Codex CLI 0.160.0 uses isolated synthetic settings, source, capture and vault folders. The local SSE fixture holds the first turn open for 120 seconds, then allows resumed turns. This is one live streamed turn followed by resumed turns, not 20 turns in one continuously running interactive client. Fixed fixture replies are not model inference. The isolated probe retains its previously reviewed one-off hook-trust bypass; it does not overwrite normal user trust or use account credentials.

The required checks are actual hook completion, exact complete rollout bytes, one canonical vault Session, interrupted-prompt recovery, and quoted SQLite evidence. An additional owned native WebView check copies only this synthetic rollout into its isolated source scope, captures with Mind Palace closed, reopens the native vault, compares the complete stored source and asks through the UI. The copy does not alter the original rollout.

## Results

Installed-client probe `client-ez0ci1rs` held the first streamed turn for 120 seconds. Measured first-client wall time was **142.219 seconds**, including startup. Twenty completed turns and a further held-response forced exit produced one exact **181,413-byte** rollout. Approved-root recovery preserved the interrupted prompt, one canonical Session and quoted SQLite evidence.

The strict hook-count check **failed** (process exit 1): only 18 successful Stop and 18 SessionEnd records were observed for 20 completed turns. Nineteen SessionStart records include the forced-exit request. All recorded relay starts finished successfully, approximately 200 ms; the missing events have no relay-start records. Their cause is not established. Do not classify the installed-client run as an all-hooks pass. The complete-data recovery and Ask checks passed despite that discrepancy.

The owned native check `226ec02b-a4ef-45fe-a271-5af2bdcc8083` then **passed, exit 0** with this exact installed-client rollout: app-closed frozen capture, native restart, automatic import, one Session, exact source bytes, and SQLite evidence through the actual Ask UI. WebView console errors: zero. The native check uses a synthetic copy and a directly invoked configured handler; it does not independently prove delivery of the missing actual-client events.

Short diagnostic `client-e7kdumhc` passed three normal turns with three successful SessionStart, Stop and SessionEnd deliveries. Its later forced-exit check failed because the fixture request did not start within the existing ten-second startup wait. No fourth SessionStart was observed. The overall process exited 1, so this is not a full forced-exit pass. The previous two-minute run already proved complete interrupted-prompt recovery. No additional duration test or blind timeout increase followed these failures.

`node --check tools/verify-native-shell.mjs`, Python argument validation/help and `git diff --check` passed. Source edits affect verification tools and documentation only; the desktop binary and frozen resources remain the previously verified build. The probe now emits bounded per-turn hook observations immediately and includes an explicit all-hooks flag in completed reports. Immediate output preserves diagnostics if a later forced-exit check aborts before the report is saved. The final observation-output edit received syntax checks only, not another installed-client run. The next investigation should compare per-turn client lifecycle traces with the relay starts, or use the documented persistent app-server transport; do not repeatedly run the two-minute test until it passes.
