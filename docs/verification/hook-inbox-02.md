# Shared user-installed hook inbox 02 — actual verification

3 October 2026. D024: user explicitly chooses **Codex + Claude Code**, lifecycle hooks and one shared per-user local inbox, setting aside other capture approaches. This verification covers the source receiver/wrapper, selected Markdown memory snapshots, indexes and Windows development onedir package. It is not installed-client/native-app verification.

## Actual source results and reliability limits

- First shared-inbox focused run: **nine passed**, 2.008 seconds. Covers shared providers, memory/source fidelity, resumed start/Stop/end revisions, rebuildable/idempotent indexes, snapshot tamper preservation, pause, selected-root/provider mismatch/link guards, memory revisions/missing roots/bounds, index scan limits and real wrapper subprocesses.
- Broader 83-test run had one existing `test_real_process_exit_recovery` subprocess timeout at 20 seconds and two existing frozen UI-worker skips; 68.562 seconds. Earlier 74-test run also had a different existing source-process timeout. These are retained startup/reliability observations, not evidence of a diagnosed cause. No timeout was relaxed and no failing check removed.
- With the dedicated capture package selected, broader regression: **84 discovered, 82 passed, two skipped**, 66.524 seconds. Includes all 14 receiver tests, 20 export tests and the actual frozen capture-process check. The two skips are legacy frozen UI-worker tests; its executable was not selected.
- An additional focused run after strengthening both source/frozen subprocess checks to launch from a different temporary working directory had one source-launcher timeout (20 seconds), while the frozen check and other eight checks passed; total 39.052 seconds. Keep startup reliability open even when a later run passes.
- Final focused check on the rebuilt artifact, with both source/frozen subprocesses launched from the temporary source directory: **10 passed**, 2.874 seconds. SHA-256/package size were confirmed after the final rebuild. `git diff --check` passed. Earlier timeouts remain reliability limitations; this pass is not complete hook-deadline or installation verification.

## Windows package

Built with existing PyInstaller 6.22.3/contrib hooks 2026.8, Python 3.12.10 and portalocker 4.4.0; Windows 10 19045 x86_64. Generated only ignored project `.tools` artifacts. No installer/global tooling install, client registration, system PATH/registry change, API key or private source read.

```powershell
& D:/Projects/mind-palace/.tools/probe-venv/Scripts/python.exe -m PyInstaller --noconfirm --onedir --name memory-capture --distpath .tools/capture-dist --workpath .tools/capture-build --specpath .tools --paths sidecar tools/capture-hook.py
```

Final development artifact: `.tools/capture-dist/memory-capture/memory-capture.exe`, with its entire `_internal` support directory. **70 files; 22,695,566 bytes**. Executable SHA-256: `c485239ae4698437dc08c681cd9792b15b55bb57221fb2bbfd6652ec3d5111ab`. This hashes the executable, not the full directory inventory, and does not establish signed distribution or clean-machine support. Rebuild changed the earlier executable hash; only this final hash identifies the current artifact.

Inspected `.tools/capture-build/memory-capture/warn-memory-capture.txt`: optional Redis, POSIX/platform and import-analysis symbols are listed. No Redis path/service is used. Actual frozen execution, not warning dismissal or build success, establishes the tested Windows path.

Focused source/frozen command from `sidecar`:

```powershell
$env:MP_CAPTURE_EXECUTABLE = (Resolve-Path ../.tools/capture-dist/memory-capture/memory-capture.exe).Path
& D:/Projects/mind-palace/.tools/probe-venv/Scripts/python.exe -m unittest discover -s tests -p test_capture_inbox.py -v
```

Real frozen probe feeds a synthetic SessionStart envelope via stdin, saves transcript and selected memory, checks empty stdout, then invokes `--rebuild-index` and verifies both objects. Source and frozen commands run from an unrelated temporary fixture working directory. This proves our launcher/packaged IO, not that installed Claude/Codex clients actually invoke it, honor this shell quoting or meet short SessionEnd deadlines.

## Remaining gates

Native Connections/setup UI, disabled consent generation, exact-client shell quoting/config-preserving installation/removal, actual synthetic client session integration, hook cold-start/end-deadline measurements, memory-root configuration overrides, missed events/retention/quota management, app restart/closed behavior, canonical provider ingestion, source-format normalization and retrieval remain pending. The current desktop UI is unchanged and does not read this inbox. No hook was added to this user's assistant configuration, and no source text from their local assistant stores was copied.

Session and memory phases publish independently; no whole-hook transaction is claimed. Derived caches are rebuildable and contain no source text. Real Windows publication ran; junction predicates are mocked in rejection tests, and POSIX/macOS are unverified. No native/model/installer/full-product gate passed because of this subset.
