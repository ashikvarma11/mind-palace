# Shared hook inbox — approved sync approach

User-facing setup is in [the Codex guide](user-guide.md). Current capability boundaries and pending acceptance work are in [the roadmap](roadmap.md). The native full workflow passed again for public synthetic screenshots on 5 October; the 18-of-20 delivery discrepancy remains open.

## Codex desktop update — 4 October 2026

Connections can merge Mind Palace's user-level Codex hook handlers into `hooks.json`, keep an exact backup, show file status, and remove only those handlers. It refuses an ambiguous inline `config.toml` hook layer or partial exact installation. File status does not claim runtime trust. Opening/reloading a vault and asking a question sync captures through the single writer and write validated import acknowledgments. Specifically allowlisted capture failures keep stored evidence available with an explicit unsynced notice; they do not retry capture writes. Indexing repairs known sessions from the approved source root. Unknown history needs a separate metadata review and confirmation. Cleanup removes only acknowledged 30-day prefixes covered by the retained complete source; a reconstructed-source scan above 128 MiB defers without deletion. Complete sources up to 20 MiB are supported through 48 MiB serialized import pages and 64 MiB transport. Ask searches known user/assistant fields and returns exact evidence or abstains; it does not run a model.

The final real Windows WebView workflow passed app-closed capture, restart, missed-tail repair, explicit history confirmation, fresh-capture Ask, evidence navigation, full 20 MiB native import/read, no duplicate Session and hook removal. It also verified visible missing-sync warning plus stored evidence after an actual frozen-controller rejection of invalid synthetic consent. See `verification/codex-recovery-08.md` for the retained failures and final clean run. Private app control now exchanges bounded JSONL frames without waiting for pipe EOF. Installed Codex 0.160.0 passed a 20-turn loopback fixture with all 20 Stop/SessionEnd hooks, exact rollout recovery and a further forced exit. This is real client execution with fixed test replies, not real AI. Normal persisted hook trust and the continuously open one-hour acceptance gate remain open. Simple ASCII paths use the receiver directly; spaces/metacharacters use literal encoded quoting whose end-hook timing is not guaranteed. Older manual-snippet and import-limit notes below are historical implementation states.

3 October 2026. The user chooses a global-per-user folder receiving session data and indexes from user-installed hooks, then explicitly confirms **Codex and Claude Code**. Other automatic-capture approaches are set aside for now (D024). No ordinary ChatGPT/Claude account access is promised. Existing manual paste remains usable; export research/code is preserved but shelved.

## Flow

```text
User enables capture and installs a reviewed hook snippet
  Claude Code / locally orchestrated Codex
    SessionStart + Stop (completed turn) + SessionEnd
      bundled memory-capture receiver
        shared user-local inbox
          provider/session-key/immutable transcript revision
          provider/memory/file-key/immutable memory revision
  Mind Palace reads this inbox
    validates originals and rebuilds index.json + index.md
    ingests selected session revisions through its single writer
```

Engineering default: `%LOCALAPPDATA%\MindPalace\capture` on Windows, with app-owned consent files under `settings/` and immutable snapshots/indexes under `inbox/`; later use each OS's per-user application-data directory. “Global” means accessible across the user's projects, not a machine-wide administrator-owned folder or an automatically cloud-synced drive. No live folder/configuration was created at this default during development; native verification uses a debug-only UUID under the ignored worktree verification directory.

The folder is independent of whether the app is open. Each hook copies the complete available JSONL prefix into a unique spool record. The app-side index operation can separately copy explicitly selected memory Markdown. Source files remain untouched. Start/end meet the requested lifecycle model; `Stop` avoids waiting until a long session ends. Abrupt crashes and missed hooks can still leave gaps. No pre-hook historical scan or hidden watcher is enabled.

## Current working source/development package

`tools/capture-hook.py` launches `memory_worker.capture_inbox` independently of the assistant's working directory. It is also the dedicated PyInstaller onedir entry point. The hook captures sessions without an inference model, API key or network. It does not scan memory roots. An explicit app-side index operation scans separately approved memory roots. The frozen development package's result is recorded in verification/hook-inbox-02.md and verification/hook-reliability-06.md; this is not an installer claim.

Transcript config is the receiver-01 exact contract in automatic-capture.md:

```json
{
  "schema_version": 1,
  "provider": "claude-code",
  "enabled": true,
  "source_root": "ABSOLUTE_APPROVED_TRANSCRIPT_ROOT",
  "inbox_root": "ABSOLUTE_SHARED_INBOX"
}
```

Codex uses `provider:"codex"` and its explicit approved transcript root, with the same inbox. Paths must be absolute, unlinked and non-overlapping. Default Claude Code sessions live under `~/.claude/projects`; default local Codex sessions are under Codex home. Configuration/root overrides must be resolved before user setup. Unknown transcript formats stay raw `normalized:false`; syntactically valid JSONL does not prove provider message fidelity.

Optional memory consent is a separate file:

```json
{
  "schema_version": 1,
  "provider": "claude-code",
  "enabled": true,
  "inbox_root": "ABSOLUTE_SHARED_INBOX",
  "roots": ["ABSOLUTE_SELECTED_PROJECT_MEMORY_DIRECTORY"]
}
```

Supported examples are explicitly selected Claude Code project `memory/` directories and local Codex `memories/`. No default root is silently read. The receiver copies UTF-8 `.md` files within those roots, including `MEMORY.md`; non-Markdown files are not imported. It does not follow memory references, load their instructions, parse YAML into approvals or invoke a model. Scope: at most 32 non-overlapping roots, four nested directory levels, 1000 filesystem entries, 64 KiB per Markdown file and 4 MiB per invocation. A missing selected root is reported unavailable; other selected roots may still be captured. Memory is `local_assistant_memory`, `selected_files_only`, `unreviewed`, never confirmed decisions.

Sources are plaintext; snapshots may include personal information, prompts, tool results and paths. The app's future setup must show these exact scopes and allow separate memory opt-in, pause and removal of the hook. Config is not an access barrier against another process running as the same OS user.

## User-installed hook setup

Current official references checked 3 October:

- https://code.claude.com/docs/en/hooks — Claude Code user settings support lifecycle command hooks and expose session/transcript fields.
- https://learn.chatgpt.com/docs/hooks — locally orchestrated Codex supports `~/.codex/hooks.json` or inline config hooks; transcript format is not a stable API. Cloud-orchestrated Work/dots use different enterprise hooks and cannot use this local command setup.

Supply a client-specific snippet for **manual merge**, never replace the user's whole settings/hooks file. Preserve every existing hook. Use one representation per Codex config layer to avoid unintended duplicate execution. The example below is a structural template, not installed configuration: replace `CAPTURE_COMMAND` with the reviewed shell-specific invocation of the bundled executable and absolute consent paths. Paths with spaces need quoting verified in that client's actual Windows shell.

```json
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": "CAPTURE_COMMAND", "timeout": 10}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "CAPTURE_COMMAND", "timeout": 10}]}],
    "SessionEnd": [{"hooks": [{"type": "command", "command": "CAPTURE_COMMAND", "timeout": 3}]}]
  }
}
```

Codex `SessionEnd` supports at most three seconds; do not invent a larger supported timeout. Claude also has short end-hook deadlines. SessionEnd does not necessarily run when switching tabs/unsubscribing. Real-client startup/large-source latency must be measured before calling this reliable. Hooks emit **empty stdout** to avoid injecting captured text into the assistant. Only non-content statuses/errors go to stderr.

Developer source invocation from any directory (PowerShell, stdin receives a hook event):

```powershell
& 'ABSOLUTE_PROJECT_PYTHON' 'ABSOLUTE_REPO/tools/capture-hook.py' --config 'ABSOLUTE_CAPTURE_CONFIG'
```

Development frozen invocation:

```powershell
& 'ABSOLUTE_PACKAGE/memory-capture.exe' --config 'ABSOLUTE_CAPTURE_CONFIG'
& 'ABSOLUTE_PACKAGE/memory-capture.exe' --config 'ABSOLUTE_CAPTURE_CONFIG' --rebuild-index
```

End users must receive the entire packaged onedir folder; they should not install Python, pip, compiler tools or project dependencies. The development desktop now stages the entire receiver and pins/verifies its resource inventory before native launches. Installer distribution and persistent client registration remain unverified. A temporary invocation-level Codex hook delivered one real `SessionEnd` event to a synthetic receiver scope; it did not change the user's persistent Codex configuration. See verification/hook-contracts-05.md.

### Desktop Connections subset — 3 October

Connections (outside the fictional sample) now exposes read-only status, explicit scope saving, per-client pause, manual merge snippets and on-demand validated indexing. Status alone creates no files. Both clients are off until explicitly configured; transcript consent and selected Markdown memory consent are separate. No default private source path is scanned or silently selected. Hooks work independently of an open vault/app; the desktop launches the receiver only for bounded app-control operations. Pausing capture retains originals and allows the app's explicit index rebuild; the standalone index CLI continues to honor its paused gate.

Claude Code snippets use the current documented executable-plus-args form. Codex Windows snippets use a PowerShell encoded command with literal escaped paths, verified with actual frozen subprocesses and synthetic paths containing spaces/apostrophes/dollar signs. These are generated manual merge snippets, not an assurance they were installed. Source and frozen tests do not establish the client's actual event delivery, historical completeness or a dependable 3-second deadline. The UI labels installation unverified.

Each scope update supplies a revision token covering both existing consent files. Stale or malformed/conflicting settings are preserved. Under the inbox lock, the app writes paused transcript consent, then memory consent, then requested transcript consent. If interrupted, capture can remain paused or setup can be incomplete; refresh before retrying. There is no journaled repair UI yet. The controller can display/pause a missing source directory, but rebuilding indexes currently requires an available configured transcript directory. Original-content validation and canonical ingestion remain separate.

Build the capture receiver with the existing project-local PyInstaller environment, then run `tools/stage-capture.py`; use `--refresh` only for an existing verified generated bundle. `--check` checks the complete generated inventory. Native build/test scripts require both worker and capture staging. The dedicated executable supports private app-control JSON over stdin at `--app-control-root`; this is not exposed as an arbitrary executable/root WebView command.

## Index and integrity

The inbox retains existing receiver session paths `<provider>/<session_key>/<transcript_sha>.json`. Memory uses `<provider>/memory/<memory_key>/<raw_sha>.json`. File keys incorporate provider and selected root/relative path; memory names are retained only in local provenance. Changed content creates a new revision, repeat content is not rewritten, and deleting a source does not silently delete a saved copy.

`--rebuild-index` is the app-side/on-demand operation. Add `--memory-config ABSOLUTE_MEMORY_CONFIG` to this operation when the user enabled the selected Markdown memory roots. Global indexing deliberately does not run inside each short-lived hook. It validates unique spool deliveries, deduplicates them into ordered schema 2 manifests and content-addressed JSONL chunks, validates existing snapshots, and atomically replaces each derived cache file. `index.json` is the machine index; `index.md` is a readable companion. Neither contains transcript/memory text or original file paths, and neither designates a revision as latest. UI must validate indexed snapshots again before ingestion. The two cache files can differ after interruption; JSON is authoritative and both are rebuildable.

Index limits: 5000 snapshots, 15,000 walked entries, 128 MiB scanned snapshot files and 1 MiB per cache. Unexpected links, malformed records or tampering fail before cache replacement; originals are preserved. Session and memory phases are independent: a successful session snapshot can remain if memory collection fails, and retry deduplicates it. Memory snapshot batches can similarly leave valid earlier revisions after a write failure. Never call that full-job success.

`capture.lock` serializes app-side configuration, memory scans, spool draining and index replacement. The hook does not take this lock. It rereads consent before its unique atomic spool write. Disabling capture does not cancel a hook that has already passed this check. Hook preflight uses the last exact app-side scan plus pending spool bytes against 1 GiB and reserves 1 MiB for bounded content-free failure markers. The UI reports this health state. Automatic pruning is disabled until a successful vault import produces a validated inbox acknowledgment. Windows extended paths are implemented without changing machine settings; POSIX/macOS behavior remains unverified.

## Current handoff / remaining work

1. Source/frozen synthetic capture, memory, pause and index checks pass. See verification/hook-desktop-03.md for the latest desktop subset and retained failures.
2. Native setup/consent/status/pause/manual snippets and inbox indexing are implemented; actual desktop evidence is recorded separately from source/build results.
3. Complete Codex verification first. Installed Codex 0.160.0 delivered one real `SessionEnd` event to the frozen receiver under a three-second configuration, and a separate three-run probe passed the deadline. `SessionStart`, `Stop`, persistent manual installation, restart/app-closed behavior and private transcript compatibility remain unverified. Do not repeat the failed project-local startup method; use a supported diagnostic or another controlled method. Never run paid generations merely to test setup. Claude Code follows after Codex.
4. Canonical session ingestion is implemented through the existing single writer. The app revalidates indexed originals, imports bounded pages, and maps one provider/session key to one unreviewed Session. Selected source revisions are immutable and content-addressed; raw inbox snapshots remain authoritative. Divergent/oversized sessions are skipped without truncation, and memory snapshots stay unreviewed in the inbox pending a canonical memory type.
5. The Codex lifecycle fixture now verifies opaque transcript preservation for `SessionStart`, `Stop` and `SessionEnd`. Real-client coverage currently includes only the controlled Codex `SessionEnd` event. Claude Code fixtures, automatic decision extraction and inference remain outside this verified result.
6. The importer no longer selects a stale smaller prefix when a later revision exceeds its current canonical guard. It skips and reports the complete Session until ordered segmented import is implemented. See verification/hook-reliability-06.md.
