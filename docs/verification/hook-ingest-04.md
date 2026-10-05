# Hook capture canonical ingestion — 3 October 2026

Windows 10 build 19045 x64; Angular 22.2.1, Tauri 2.12.1, Rust 1.99.0, Python 3.12.10, jsonschema 4.26.0, portalocker 4.4.0 and PyInstaller 6.22.3. All capture/session content was synthetic in temporary or ignored UUID-isolated roots. No assistant settings were edited, live hooks installed, private content read, cloud request made, package installed globally, commit pushed or release published.

## Implemented boundary

The app-owned receiver rebuilds and revalidates the raw inbox before planning import. It groups snapshots by provider/session key, requires one byte-prefix chain, selects the longest bounded revision and returns at most ten candidates per page. Rust rechecks the candidate UUID, provider/session identity, SHA-256, lengths and unique revision list before invoking `captures.ingest` on the already-open sole vault worker.

The writer creates one unreviewed Session per provider/session key and records a stable receipt under `imports/<provider>/<session-key>.json`. Selected sources are immutable `sources/<source-id>/revisions/<sha256>.txt` files. Later prefix revisions update the source pointer/receipt without changing old revision bytes or creating another Session. Pasted-session storage remains compatible. Divergent or over-65,536-character captures are counted as skipped and left untouched; memory snapshots remain unreviewed in the inbox and are counted as pending.

## Actual checks

- Final source Python suite: **92 tests, 88 passed, four frozen-only skips**, 20.842 seconds. Focused ingestion/storage/control suite: **18 tests, 17 passed, one expected frozen-only skip**. Tests prove one canonical record, prefix update, idempotent operation receipt, immutable prior revision, tamper conflict, spoofed identity rejection and divergent-branch skip.
- Final frozen checks: generated Codex/Claude control plus frozen inbox checks passed; frozen storage protocol reopen and session listing passed separately (**four focused checks total**). The earlier complete frozen run reached 91/92 and retained one 30-second Codex PowerShell cold-start timeout; its immediate focused retry passed in 3.124 seconds. No timeout was extended.
- Angular: **27/27** across six files. Production build passed (419.92 kB initial raw) with the existing two Ajv CommonJS warnings. Generated contracts checked and **7/7** contract tests passed. The Connections UI validates import receipts, shows paging/skips/pending memory, requires an open vault, and refreshes Sessions. Captured providers are visible in Session list/read views.
- Rust: **19/19** serial tests, including candidate identity/hash rejection; development build passed with only the existing linker informational warning. Fixed command permissions and worker allowlists include only `capture_import` / `captures.ingest`; no generic path or executable command was added.
- Final staged receiver: **70 files / 22,705,823 bytes**. Final staged memory worker: **111 files / 23,687,747 bytes**. Both complete inventories were regenerated and embedded before the final native build.

## Real native evidence and retained failures

The first updated real WebView run (isolated UUID `f8b36c71-59e7-4ba9-99d7-aa16e8976902`) completed vault creation, Codex and Claude Code synthetic hook capture, validated index (**2 sessions / 1 memory / 5 revisions**), canonical import (**2 Sessions**), list/read of `Codex session native-synthetic`, exact final `SessionEnd` source display and provider badge. On-disk evidence contains two canonical Session files and separate Codex/Claude import receipts. That run then failed the existing post-restart paused-status assertion: zero cards appeared within 35 seconds.

A fresh isolated retry (`ed93cbea-fd4d-4801-9d66-12675bb83b2c`) failed earlier when Claude Code configuration returned the gateway's bounded unavailable state; the pause button did not appear within 35 seconds. This is consistent with the previously recorded Windows receiver cold-start/control stalls. It is not hidden or called a full end-to-end pass. Source/frozen/native compile tests pass, and the successful first run establishes the new WebView → Rust → frozen receiver/worker → canonical Session/read path before its restart failure.

## Remaining gates

Actual installed Codex and Claude Code event delivery, the three-second Codex SessionEnd budget, app-closed reliability, provider-specific real-message fixtures, retention/quota controls, canonical memory-record import, Mac, installer and clean-machine checks remain unverified. The current UI is the tested Workspace design; the latest Library preference remains pending. Rust formatting was not run because the isolated toolchain has no `rustfmt`; compilation, tests and final whitespace/diff checks are the available evidence.
