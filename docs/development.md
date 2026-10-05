# Development

**Updated 5 October 2026.** This guide separates the public browser setup from the prepared Windows native setup.

## Choose a path

| Goal | Requirements and result |
| --- | --- |
| Explore the interface | Node/npm and a browser. Fictional sample only. |
| Change storage/capture code | Python 3.12 and source tests with synthetic data. |
| Run the actual Codex workflow | Prepared Windows x64 native build, staged bundles, compiler/SDK resources, WebView2 and native icons. |

The public repository does not include generated executables, staged bundles, compiler resources or the supplied temporary artwork. A fresh-clone desktop setup is not yet independently verified. Do not treat the browser sample as durable storage.

## Browser development

Recorded versions: Node 24.16.0, npm 11.17.0, Angular 22.2.1 and Playwright 1.63.0. Use the lockfile.

```sh
npm ci
npm run dev:web
```

Open `http://127.0.0.1:4200`. Choose **Explore sample workspace**. Reload resets sample data.

```sh
npm run check
npx playwright install chromium
npm run test:e2e
```

Playwright can use an existing compatible Chromium binary through `MP_BROWSER_EXECUTABLE`. The install command above downloads developer browser binaries. Neither command is part of the end-user desktop workflow.

## Python source development

The worker project requires Python >=3.12,<3.13. Core dependencies are pinned in `sidecar/pyproject.toml`. The following uses a project-local environment:

```powershell
python -m venv .tools/probe-venv
./.tools/probe-venv/Scripts/Activate.ps1
python -m pip install -e ./sidecar
python -m pip install PyInstaller==6.22.3
$env:PYTHONPATH = (Resolve-Path sidecar).Path
python -m unittest discover -s sidecar/tests -v
```

These setup commands are derived from the checked project configuration; this documentation update did not create or certify a new environment. The broader historical diagnostic environment is version-locked in `tools/requirements-probe-lock.txt`; it includes extra research dependencies not needed by the core worker.

Frozen-only tests need explicitly built bundles. Expected skips are not frozen verification. Use temporary synthetic sources and vaults. Do not point tests at personal Codex data.

## Native resource staging

Build both dedicated bundles from the repository root with the project environment active:

```powershell
python -m PyInstaller --noconfirm --onedir --noupx --name mind-palace-memory-worker --distpath .tools/probe-dist --workpath .tools/probe-build --specpath .tools --paths sidecar --add-data "schemas:schemas" tools/worker-entry.py
python -m PyInstaller --noconfirm --onedir --noupx --name memory-capture --distpath .tools/capture-dist --workpath .tools/capture-build --specpath .tools --paths sidecar --add-data "schemas:schemas" tools/capture-hook.py
python tools/stage-worker.py
python tools/stage-capture.py
python tools/stage-worker.py --check
python tools/stage-capture.py --check
```

`--noconfirm` rebuilds the named generated bundle. Staging uses fixed ignored source/target paths and checks their integrity. To replace an intentionally changed verified staged bundle, use the corresponding helper's `--refresh`; it preserves the old verified tree in an ignored backup. Unknown or tampered staging is refused.

These bundles are development resources, not public installers. Frozen rebuild/staging requires actual verification after source changes.

## Prepared Windows compiler path

The existing helper uses project-local compiler resources and an already installed Windows SDK. Recorded SDK: 10.0.20348.0; MSVC tool set: 14.44.35207; Rust: 1.99.0. This is an experimental prepared-machine arrangement, not a standard redistributable toolchain.

For a new, empty `.tools/native` setup only:

```powershell
python tools/setup-local-native.py --extract
python tools/run-native.py smoke
```

The setup helper downloads locked official development archives and validates hashes. It refuses existing extraction targets. It does not run an installer or change global PATH. On the prepared workspace, skip extraction.

Native icon generation needs artwork with approved redistribution rights. The current supplied logo is excluded from public Git history. The interface has an MP fallback, but that does not supply the native icon bundle. Public-clone icon/resource setup remains a packaging task; do not invent missing assets or claim fresh-clone success.

## Build and open the desktop

With Node, Python, compiler resources, staged bundles and native icons prepared:

```powershell
npm run build:desktop
npm run open:desktop
```

The executable is `src-tauri/target/debug/mind-palace.exe`. Keep it in the project build location: debug builds resolve their resources from this tree. `open:desktop` launches the existing build; it does not rebuild it. WebView2 was available on the verified Windows machine; other-machine installation is not certified.

Follow the [user guide](user-guide.md) for vault opening, Codex source consent, hook installation, `/hooks` approval, sync, Library and Ask. Search returns exact stored quotes, not generated summaries.

## Native verification

Build first. Run checks sequentially, with no concurrent native build:

```powershell
npm run test:rust
$env:MP_PROBE_PYTHON = (Resolve-Path .tools/probe-venv/Scripts/python.exe).Path
node tools/verify-native-shell.mjs --codex-workflow
```

The probe runs the actual WebView/Tauri/frozen processes with a canonical UUID selector, isolated vault/inbox and WebView profile, synthetic data and temporary loopback debugging. Ordinary app launch does not enable that debug endpoint. The probe closes its owned app. Generated test profiles and screenshots stay ignored under `.tools/native/verification`.

Focused diagnostics:

```powershell
node tools/verify-native-shell.mjs --diagnose-vault --trace-commands
node tools/verify-native-shell.mjs --full-size-only --trace-commands
node tools/verify-native-shell.mjs --codex-workflow --docs-screenshots
```

Stage timing is opt-in and restricted to isolated debug probes. It records stages and elapsed time, not paths or transcripts. Public screenshot mode uses the actual MP fallback and synthetic sessions. Review every screenshot before copying it into tracked documentation.

## Contracts and evidence

After a schema change:

```sh
npm run generate:contracts
npm run check:contracts
```

Do not hand-edit generated types or validators. Native framing and validation remain separate boundaries.

Record real results in `docs/verification/`. Builds, browser samples, service doubles, fixed provider replies and actual native flows have different meanings. Keep earlier failures visible. The latest [native report](verification/codex-runtime-13.md) passed the complete synthetic workflow and exact 20 MiB boundary; intermittent Windows failures and the separate 18-of-20 installed-client result remain open.

Uncertain writes are never automatically retried. Inspect status and saved sessions before an explicit retry. Manual draft retry state survives only while the app stays open; durable restart recovery is pending.

## Cloud preview foundations

Offline selected-source previews, discard/expiry and targeted cancellation exist as separate foundations. Sending, real key entry and generated provider answers remain unavailable. Fake-key Windows credential tests do not prove a real provider connection. Do not put credentials in question, model or fixture fields.

[Contributing](../CONTRIBUTING.md) · [Roadmap](roadmap.md) · [Current status](implementation-status.md)
