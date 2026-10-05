# ChatGPT export sync 01 — actual verification

3 October 2026. Worktree `C:/Users/varma/.codex/worktrees/21fd/mind-palace`. Windows 10 build 19045, existing project-local Python 3.12.10/portalocker 4.4.0. No package installed or account connected. Only temporary synthetic exports/memory were read. No private transcript, cookie, credential, model or paid request used.

Latest user direction D024 subsequently replaces this active approach with Codex/Claude Code hooks and one shared inbox. Preserve the importer as a tested, independent fallback; it does not establish continuous account sync or native ingestion.

## Results, including failures

- Initial focused run: 20 tests, two failures/eight errors (1.809 seconds). Windows content-addressed paths exceeded MAX_PATH during rename.
- First attempted rename-only extended-path fix still failed (one failure/19 errors, including fixture cleanup, 1.975 seconds). File reads and cleanup also needed consistent extended paths. Did not change registry/system settings or weaken checks.
- Consistent path handling and verified-root test cleanup fixed the issue. Focused run: **20 passed**, 2.434 seconds. The helper was later shared in `memory_worker.paths`; full regression also exercised that version.
- First broader source suite: 74 tests, one pre-existing `test_source_process_list` subprocess timeout at 30 seconds, two frozen UI-worker tests skipped. Focused existing listing rerun: eight passed, one skipped, 3.110 seconds. Timeout is preserved, not attributed to a proven cause.
- Later shared-hook regression: 84 discovered, **82 passed/two skipped**, 66.524 seconds. These skips are existing frozen UI-worker checks, not successful packaging verification of that worker. Capture package has a separate actual frozen test in hook-inbox-02.md.
- Final whitespace check is recorded with hook-inbox verification. No Angular/Rust/native desktop regression was required or claimed for these separate entry points; UI resources/IPC inventories remain unchanged.

Focused command from `sidecar`:

```powershell
& D:/Projects/mind-palace/.tools/probe-venv/Scripts/python.exe -m unittest discover -s tests -p test_chatgpt_sync.py -v
```

Covered: direct JSON and partitioned ZIP, exact included-fragment UTF-8/CRLF preservation, original branch identity/current path, Unicode/inert script-like text, same-session revisions, account-label separation, no rewrite on duplicate/restart, explicit memory snapshots, exclusion without raw leakage, pause and pause during read, interruption before receipt/retry recovery, tamper preservation, malformed graphs/JSON/duplicate keys/constants, bounded reads/quota, root escape/link guard, hostile/ambiguous/duplicate ZIP paths, unsupported content warnings, empty/all-excluded states, two actual simultaneous subprocesses and redacted CLI errors.

No actual account export fixture was used. Link predicate tests are mocked and do not prove real junction integration. Windows atomic publication and real subprocess paths ran; POSIX hard-link publication remains unverified. No source is modified or erased. Ten synthetic fixture directories left by the failed long-path cleanup run were later removed only after verifying their exact temp parent, owned prefix, consent profile/source and permitted entries; no user directory was deleted.

Remaining gates: current real producer fixtures, format coverage, frozen export-entry packaging (not needed in the chosen hook scope), native consent/file selection/ingestion, indexing/retrieval and ordinary account capture. No complete/all-history or complete saved-memory claim.
