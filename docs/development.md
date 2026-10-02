# Development

Project root: `D:/Projects/mind-palace`. Browser foundation: Angular 22.2.1 with strict TypeScript and templates, standalone routes, signals, system fonts, and a local Lucide subset.

Use compatible Node (tested 24.16.0) and npm (tested 11.17.0), `npm ci`, and `npm run dev:web`. The server binds only 127.0.0.1:4200. Open Welcome and explicitly choose the fictional sample. Reload resets sample state; do not use it to store personal memory.

`npm run check` runs unit tests and production build. `npm run test:e2e` uses Playwright; first use `npx playwright install chromium` or provide a known compatible existing binary with `MP_BROWSER_EXECUTABLE`. No machine-specific browser path is hard-coded in the committed configuration. Browser tests distinguish in-memory samples from native/backend/inference verification.

`npm run probe:runtime` uses Python for actual preliminary SQLite/atomic-write capability checks. Native desktop and frozen memory-service scripts will be introduced only when their implementations exist; no placeholder successful commands are supplied.

Current public clone uses an MP fallback without the supplied binary artwork. Local artwork remains in ignored public/brand paths pending a separate asset license/provenance decision. Dependency licenses are separate from application MIT; production Angular license extraction remains enabled.

## Isolated Windows runtime probe

This diagnostic is separate from the production sidecar. Run these commands from the project root in PowerShell; all environment/build outputs stay in ignored .tools directories:

```powershell
python -m venv .tools/probe-venv
./.tools/probe-venv/Scripts/python.exe -m pip install -r tools/requirements-probe-lock.txt
./.tools/probe-venv/Scripts/python.exe -m PyInstaller --onedir --noupx --name mind-palace-runtime-probe --distpath .tools/probe-dist --workpath .tools/probe-build --specpath .tools tools/probe-runtime.py
$env:MP_FROZEN_PROBE = (Resolve-Path .tools/probe-dist/mind-palace-runtime-probe/mind-palace-runtime-probe.exe).Path
./.tools/probe-venv/Scripts/python.exe -m unittest discover -s tools/tests -v
```

If a generated output already exists, PyInstaller can request overwrite permission; inspect that exact diagnostic output before replacing it. Tests without MP_FROZEN_PROBE explicitly skip packaged execution. Frozen tests run from a temporary folder with Python-specific environment variables removed and PATH limited to Windows System32; this is stronger local isolation, not proof on a clean machine without Python installed. Production storage, transport, MCP/Graphify, AI and native UI are not implemented by this probe.

Graphify diagnostic (same environment, updated version lock):

```powershell
./.tools/probe-venv/Scripts/python.exe -m pip install --only-binary=:all: -r tools/requirements-probe-lock.txt
./.tools/probe-venv/Scripts/python.exe tools/probe-graphify.py
$graphProbeFixture = (Resolve-Path tools/fixtures/probe-repo).Path
./.tools/probe-venv/Scripts/python.exe -m PyInstaller --onedir --noupx --name mind-palace-graphify-probe --distpath .tools/probe-dist --workpath .tools/probe-build --specpath .tools --hidden-import tree_sitter_typescript --hidden-import tree_sitter_javascript --add-data "$graphProbeFixture;fixtures/probe-repo" tools/probe-graphify.py
$env:MP_FROZEN_GRAPHIFY_PROBE = (Resolve-Path .tools/probe-dist/mind-palace-graphify-probe/mind-palace-graphify-probe.exe).Path
./.tools/probe-venv/Scripts/python.exe -m unittest discover -s tools/tests -v
```

Use the direct diagnostic script, not graphify CLI: inspection found that CLI startup can refresh installed assistant skills even before help. The diagnostic maps only its bundled synthetic fixture, blocks Python network/process calls and does not enable provider paths. It is not a production repository adapter. Upstream artifact LICENSE/NOTICE files are retained locally; complete release attribution and hashes for all transitive artifacts remain pending.
