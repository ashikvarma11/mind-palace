# Step 02 — preliminary runtime checks

Date: 2 October 2026. Status: in progress, complete exit gate NOT passed.

`python tools/probe-runtime.py` returned success for an actual SQLite FTS5 insert/query and flushed UTF-8 atomic replacement in a synthetic temporary directory. Environment: Windows AMD64, Python 3.12.10, SQLite 3.49.1.

The global Python environment is unchanged. An isolated .tools/probe-venv now includes pinned jsonschema 4.26.0, portalocker 4.4.0 and PyInstaller 6.22.3; tools/requirements-probe-lock.txt records the exact resolved transitive versions. MCP/Graphify and model probes remain pending. No cloud fallback was enabled.

Rust/cargo are not currently in PATH; the Visual Studio C++ component query returned no installation. No administrator/system-wide installer ran. macOS and clean-machine packaging remain untested. Use an isolated development environment and verified pinned artifacts next; do not claim native/model feasibility from the browser build.

## Windows diagnostic bundle

Built tools/probe-runtime.py using PyInstaller onedir/noupx into ignored .tools/probe-dist/mind-palace-runtime-probe. Actual output: 103 files, 24,841,220 bytes. Both source and bundled code executed SQLite FTS5, flushed Unicode replacement, Draft202012Validator acceptance/rejection (including unexpected fields), and an independent process failing to acquire a held lock then succeeding after release. Unknown CLI options are rejected without stdout. Three unittest checks passed with the frozen executable enabled. pip check found no broken requirements.

Inspected PyInstaller warning report: optional/platform imports and optional format/network/Redis extras are absent. Required exercised SQLite, schema and Windows locking paths ran successfully; this does not establish other optional paths. No remote schema references are used. The executable is a diagnostic probe, not a production worker or installer. Versions are pinned but wheel hashes, redistribution notices and clean-machine verification are still required before release.

Final regression: 3/3 checks passed in 1.626 seconds, including frozen execution from a temporary working directory with Python-specific variables removed and PATH restricted to Windows System32. Initial isolation harness exposed case-sensitive dictionary lookup of the Windows SystemRoot variable; fixed to use Windows-aware os.environ lookup and case-insensitive variable removal. Clean-machine verification remains pending, not inferred from this local isolation test.

## Graphify diagnostic

Verified pinned 0.9.73 wheel hash and matching tagged extract.py; preserved upstream LICENSE, LICENSE-MIT and NOTICE inside the ignored extracted artifact. Installed all default dependencies from available Windows wheels in the isolated environment; pip check passed. No Graphify CLI commands, install hooks, provider extras or personal repositories were used.

Source and frozen TypeScript extraction returned 7 nodes / 9 edges with valid fixture-relative source locations, no failed_sources, zero model tokens and unchanged fixture hashes/file list. Expected .remember() → .save() cross-file call is INFERRED, with source src/auth.ts L7; it must not be changed to EXTRACTED. Validators reject out-of-fixture paths, out-of-range lines and a false confidence upgrade. Python socket/process attempts are denied by an audit hook; a real socket attempt test failed before connecting. Synthetic provider-key environment was removed and query log path was None even when logging was enabled beforehand. This is a Python diagnostic guard, not a native OS security boundary.

First freeze attempt failed because PyInstaller resolves relative add-data paths against the spec directory. Replaced with the verified absolute fixture path; build and runtime succeeded. Frozen output: 146 files / 110,026,269 bytes. Required dynamic TypeScript/JavaScript grammar imports were explicitly collected; other optional grammar/document warnings remain outside tested scope. Final regression: 8/8 diagnostic tests passed in 3.874 seconds, with both frozen executables enabled. Graphify executable ran outside the project root with Python environment removed and PATH limited to Windows System32. Production combined worker, other languages/large repositories, clean-machine, Mac, MCP, AI and desktop integration remain unverified.
