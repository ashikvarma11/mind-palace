# Session-storage contracts — 2 October 2026

This is a storage/listing prerequisite, not completed UI-to-worker integration.

Implemented strict shared session metadata/read/list/create-result schemas, generated TypeScript contracts and precompiled validators, drift checks, and sessions.list in the Python route registry. Each page is at most 50 records; inventory is bounded to 1000 records. Metadata listing reads at most 8192 bytes of each frontmatter line and does not read original conversation contents. Actual read operations continue to check immutable-source hashes. Corruption is reported without deleting, rewriting or hiding the affected files.

Initial checks: 5 generated-validator tests passed; 8 source listing tests passed, with the frozen-only case deliberately skipped until rebuilding. Rebuilt the Windows worker with PyInstaller 6.22.3 using the existing isolated environment. Final complete regression results are recorded below once finished; unrun checks are not passed.

Final worker regression: **40 tests passed, no skips**, including source-process and frozen-process create/read/reopen/list. Five standalone validator tests and contract drift check passed. Pagination is deterministic for an unchanged inventory; this offset-based foundation is not a cross-request snapshot if another process adds records between pages. The future index/cursor workflow remains separate.

Other regression checks: 9 Angular tests passed; production web build passed; Rust health test passed. Diagnostic suite: 23 passed, 3 intentionally skipped because frozen Graphify/MCP/runtime diagnostic paths were not supplied in this run (their earlier separate frozen results remain in prior verification records). Linker emitted its existing library-creation informational warning; npm emitted the existing user-config precommit warning and Node noted automatic ESM detection for generated TypeScript. None was treated as a failed feature check. Actual WebView storage and CSP integration for the new validators have not been exercised because the new storage gateway is not yet installed.

Timing caveat: a subsequent 40-test run took 121.987 seconds and hit existing 20-second recovery-process and 30-second frozen-list startup deadlines. Both unchanged tests passed in an isolated rerun (1.048 seconds total). The timeouts were not removed or increased; their root cause is unconfirmed. Preserve this observation rather than claiming stable startup performance from an earlier passing run.

Final rerun against the latest rebuilt worker: **40 passed, no skips, 15.419 seconds**. The timing caveat above remains recorded even though the final regression is green.

## Continuation after the requested push

Committed/pushed the session-contract and prior native-shell code as f65b1e5; local HEAD and GitHub main matched afterward. Continued with a fixed worker-staging helper: **9 tests passed**, actual staging/inventory check passed (**109 files, 23,673,882 bytes**), and **2 real staged-worker process tests passed** (create/read/reopen/list and offline sharing-preview preparation without sending). Changed staging inputs require explicit refresh; the old verified copy is retained in ignored development backups. Tampered/unrecognized trees are never overwritten or moved. A Windows cached-stat bug in the initial hard-link guard was caught by tests and fixed using Path.stat; the final nine checks pass. No worker files or artwork are published.

The staged runtime is still not configured as a Tauri resource or supervised by Rust. The next implementation step must pin/embed the expected inventory, resolve the fixed native resource directory, verify files before execution and test private JSONL correlation/limits/timeouts/shutdown. Only then connect native vault commands and the real session interface. Staging success does not pass this pending transport gate.

Pending: Rust trusted worker-resource resolution, framing/timeouts/shutdown, actual native app-data vault commands, create/save/list/read/close/reopen interface and isolated WebView end-to-end verification. No native storage gateway, AI provider connection, real keys, paid calls, folder picker or release installer is added in this subset.
