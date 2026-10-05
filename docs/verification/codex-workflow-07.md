# Codex desktop workflow check — 4 October 2026

This check used an isolated synthetic transcript and Codex home. It did not read a private Codex session, change the user's hook settings, send a model prompt, or call a cloud service.

## Result

`node tools/verify-native-shell.mjs --codex-workflow` passed against the built Windows desktop app. The real WebView called Tauri, the staged frozen capture receiver, and the staged frozen vault worker. The test created a vault, configured a scoped Codex source, installed Mind Palace handlers beside an existing synthetic user handler, closed the app, ran the installed `Stop` command, reopened the app, and checked automatic import. The canonical Session had provider `codex` and source bytes equal to the synthetic JSONL transcript. Ask returned a SQLite passage and displayed its stored evidence. Removing the Mind Palace handlers retained the pre-existing handler. The app emitted no WebView console errors in that run.

Returned check: `codex_workflow:true`, `app_closed_capture:true`, `automatic_import:true`, `exact_source:true`, `ask_with_evidence:true`, `hook_merge_and_remove:true`.

Source checks: 103 Python tests passed with five expected frozen-only skips. Angular: 27/27 passed. Generated contract checks: 7/7 passed after the obsolete 65,536-character expectation was changed to the current 20 MiB bound. Angular production build passed. Rust native suite: 19/19 passed. The source large-revision test imported a 280,000-character latest revision without choosing an older prefix. Frozen receiver and worker bundles were rebuilt and staged before the native run.

The first full native attempts failed at capture status. A direct command showed that cold verification of the receiver inventory could exceed the 30-second app-operation deadline. The resource verifier now checks the root ancestry once and checks each bundled entry for reparse points. A repeat direct command and the full native workflow then passed. The first full Python command lacked `PYTHONPATH=sidecar`; rerunning with it passed. `npm run check` selected an older Node 12 executable in its script environment, so the checks were run directly with installed Node 24.16.0. The initial contract check then found the obsolete length assertion; the corrected test passed. These are recorded failures, not passing evidence.

## Limits and next checks

The native workflow executed the installed command with a synthetic event. It did not prove that the installed Codex client loads this persistent user-level hook or that a real 20-turn session has complete transcript coverage. An earlier controlled installed-client probe proved one real `SessionEnd` delivery through the receiver, without a user-level persistent file or prompt; see `hook-contracts-05.md`. `Stop` and `SessionStart` delivery from the actual client remain unproved. The Ask result is exact extractive text, not an AI-generated synthesis. A nonmatching question must abstain.

One further isolated user-level Codex-home probe used the privacy-safe adapter and synthetic transcript. `codex exec --ephemeral --dangerously-bypass-hook-trust --skip-git-repo-check -` with empty stdin exited with `No prompt provided via stdin.` It created no session event, so it is not evidence of hook loading. No paid prompt was sent. The native test remains the proof of the app workflow; live user-level hook loading remains open.

The 20 MiB transport and one large source test do not prove a full-size 20 MiB import. Approved-root repair, confirmed history import, 30-day redundant-prefix pruning, and the one-hour/20-turn normal and forced-exit gate remain open under D028. No installer, Mac, or release verification was performed.
