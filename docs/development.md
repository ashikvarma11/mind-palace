# Development

## Test the already-built local app (no installer)

On this prepared machine, open `D:/Projects/mind-palace/src-tauri/target/debug/mind-palace.exe` in File Explorer. Keep it at this location: debug builds resolve the verified worker from this project, not a self-contained portable package. Choose Create local vault once or Open existing vault, save synthetic conversation text, inspect Sessions, close/reopen and verify persistence. No Node/Python/compiler command is needed just to launch the existing executable. WebView2 is already installed on this tested machine; other-machine installation is unverified. Native request previews are an offline command boundary, not an AI answer screen or enabled cloud service. No API key/payment is needed for local storage tests.

Lower sections preserve earlier development/probe history. The current local vault flow supersedes their old disconnected-storage statements; see implementation-status.md for current capability.

## Local vault development flow

After opening/saving a synthetic conversation, use Ask memory outside sample mode. Choose the conversation, click Load original conversation, enter an explicit start/end range (Unicode code points; end excluded), provider, model identifier and question, then Create local request preview. Review the exact payload; no provider call occurs and Send is disabled. Discard to edit. Cancel is available during a pending preview and closes the worker connection after confirmed cleanup; reopen on Welcome afterward. Model identifiers are not checked online. Key entry/actual AI answers remain unavailable. Do not paste API keys into the model/question fields. Receipt/draft state is in-memory only; native unused receipts expire after five minutes. Known intermittent worker startup delays remain recorded in verification/ai-preview-ui-01.md.

Use `npm run build:desktop`, then `npm run open:desktop`. On Welcome/Sessions, choose Create local vault once or Open existing vault afterward. Storage is under the device's local app-data/dev.mindpalace.local/vault directory; closing preserves it. The browser sample never writes personal memory. No AI/cloud/key integration is enabled yet.

Run `npm run test:rust` and `npm run verify:desktop` sequentially after building, not concurrently with native builds. Desktop QA accepts only a debug canonical UUID test selector and uses ignored `.tools/native/verification/vault-<UUID>/vault` plus an isolated WebView profile, never real app data. Its two app lifetimes exercise save/reopen/restart and owned-worker shutdown. Generated validators require `npm run generate:contracts` after schema changes, and `npm run check:contracts` detects drift.

An uncertain save retains an unchanged draft/operation ID only while the app remains open. Reopen and explicitly retry that draft; do not reload/restart before resolving it. If already restarted, inspect saved sessions before importing again. Original storage preserves submitted text, while HTML textareas may normalize clipboard line endings. Full recovery/dialog/job/AI gates remain pending.

## Shared session contracts

Run `npm run generate:contracts` after editing schemas/native-memory.schema.json; never hand-edit the generated types/validators. `npm run check:contracts` checks drift and runs offline validation tests; `npm run check` includes this gate. Node 24 runs the generated TypeScript validators directly for these tests. The generated browser validators use static imports, not runtime schema compilation. Native supervision and the real vault interface remain the next step.

## Development worker staging

Native compilation now embeds the staged worker manifest. Build/freeze and stage the worker before running Cargo; `npm run build:desktop` and `npm run test:rust` first check that staging matches the frozen build input. Browser development does not need these resources. Native resource packaging and real vault controls are still pending.

After building the existing frozen worker in `.tools/probe-dist/mind-palace-memory-worker`, run `npm run stage:worker`, then `npm run check:worker`. These commands only use that fixed build input and `src-tauri/resources/memory-worker`; they do not launch the worker or open a vault. Both trees are ignored generated artifacts, not public release packages.

If the build input intentionally changes, `python tools/stage-worker.py --refresh` first verifies the existing staged tree, prepares and verifies a fresh copy, and moves the previous verified tree into ignored `.tools/worker-stage-backups/<random UUID>`. Unrecognized or tampered staging content is refused, not overwritten or moved. A failed preparation may leave an ignored `.worker-stage-*` temporary directory for inspection; the helper never recursively deletes it. No global installation, credentials or provider requests are involved.

## Project-local Windows desktop development

Verified only on the current Windows x64 machine with an existing Windows SDK 10.0.20348.0. Python 3.12 is needed for development helpers; neither developer toolchains nor a Python installation will be required by the future packaged product.

First-time setup only, in a fresh `.tools/native` layout:

```powershell
python tools/setup-local-native.py --extract
python tools/run-native.py smoke
node node_modules/@tauri-apps/cli/tauri.js icon public/brand/logo-original.png --output src-tauri/icons
npm run build:desktop
npm run test:rust
npm run verify:desktop
npm run open:desktop
```

Run `npm ci` first. Icon generation needs the approved local artwork, which is deliberately omitted from public clones until redistribution provenance is resolved. Do not substitute an unapproved generated logo. Build fails if required icons/tools are absent; it does not secretly download/install an end-user runtime.

Setup downloads locked official developer archives, validates hashes and extracts into ignored project-local directories; no installers or global settings. It refuses an already-existing extraction target instead of overwriting it. On this already-prepared workspace, skip setup and icon generation; use the build/test/verify/open commands. `python tools/setup-local-native.py` without extraction rechecks cached archive integrity. An interrupted partial download/extraction is retained for inspection, not silently removed.

`build:desktop` embeds the current Angular production output in an unsigned development executable. `open:desktop` opens that existing build; changes require rebuilding (no hot reload). `verify:desktop` uses Playwright against the real app's WebView with an isolated ignored profile, temporary loopback debugging and synthetic content; it closes the owned window afterward. Debugging is not enabled on ordinary launch. Test screenshots/profiles stay local under `.tools/native/verification`, with no automatic upload or purge.

The compiler arrangement is an experimental developer workaround using the already-installed SDK, not a standard VS installation or a redistributable compiler bundle. No macOS/native installer claim. Storage and AI remain disconnected from this shell; see verification/native-toolchain-01.md and verification/step-03b.md for actual results and remaining gates.

## Storage and offline cloud contracts

Using the existing isolated diagnostic environment, from the repository root:

```powershell
$env:PYTHONPATH = (Resolve-Path sidecar).Path
./.tools/probe-venv/Scripts/python.exe -m PyInstaller --noconfirm --onedir --noupx --name mind-palace-memory-worker --distpath .tools/probe-dist --workpath .tools/probe-build --specpath .tools --paths (Resolve-Path sidecar).Path --add-data "$((Resolve-Path schemas).Path):schemas" tools/worker-entry.py
$env:MP_FROZEN_WORKER = (Resolve-Path .tools/probe-dist/mind-palace-memory-worker/mind-palace-memory-worker.exe).Path
./.tools/probe-venv/Scripts/python.exe -m unittest discover -s sidecar/tests -v
./.tools/probe-venv/Scripts/python.exe tools/probe-credentials.py
```

Environment changes above are process-local. Build outputs are ignored development artifacts, not installers. `--noconfirm` rebuilds only the named worker bundle. Worker CLI: `--mode ui --vault <dedicated-directory> --create-vault` initializes an empty directory; omit create-vault to reopen. Communicate with bounded JSONL on stdin/stdout. Never point development tests at a real personal vault. Use synthetic temporary fixtures; do not copy credentials into frames or invoke a provider API.

cloud.preview takes provider/model/question/output cap and explicit local selections; cloud.prepare consumes a matching preview digest plus sharing/cost acceptance, but returns can_send:false. No network/send/key-storage operation exists. Pure provider parsing is tested with synthetic responses, not AI generation. The Windows credential probe temporarily stores and removes only random fake data at a fresh diagnostic target. It never accepts a custom target or reads existing keys. Native Rust credentials/HTTPS/UI remain pending; see verification/cloud-foundation-01.md.

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

MCP synthetic stdio diagnostic (no external assistant setup):

```powershell
./.tools/probe-venv/Scripts/python.exe -m pip install --only-binary=:all: -r tools/requirements-probe-lock.txt
./.tools/probe-venv/Scripts/python.exe -m PyInstaller --onedir --noupx --name mind-palace-mcp-probe --distpath .tools/probe-dist --workpath .tools/probe-build --specpath .tools --copy-metadata mcp tools/probe-mcp.py
$env:MP_FROZEN_MCP_PROBE = (Resolve-Path .tools/probe-dist/mind-palace-mcp-probe/mind-palace-mcp-probe.exe).Path
./.tools/probe-venv/Scripts/python.exe -m unittest discover -s tools/tests -v
```

Enable all three MP_FROZEN_* environment variables to run all 11 checks without skips. The MCP server waits for stdio protocol messages; launching it interactively is not an app preview. It exposes no search_memory/save_session tool and does not share memory. Real permission-scoped integration is deferred until storage/evidence contracts exist.

## Local model diagnostic

The official runtime is in ignored .tools/llama-b11342/bin; candidate GGUFs are in ignored .tools/models. Exact download origins/revisions/hashes are in config/models.json. Runtime/model artifacts are development prerequisites, not bundled release assets yet. Never use an arbitrary executable/model or a cloud fallback. These model files total about 2.47 GB; verify free disk space before downloading.

```powershell
./.tools/probe-venv/Scripts/python.exe tools/probe-models.py --candidate qwen3-0.6b-q8
./.tools/probe-venv/Scripts/python.exe tools/probe-models.py --candidate qwen3-1.7b-q8
./.tools/probe-venv/Scripts/python.exe -m unittest discover -s tools/tests -v
```

Run candidates sequentially to limit memory/CPU use. The diagnostic validates artifact bytes/hashes, starts a hidden CPU-only authenticated loopback process and cleans it up in finally; it emits synthetic benchmark JSON only. Its successful process exit means the measurement ran, NOT that model quality passed. Inspect passed_cases; neither candidate passed the initial ten-case checks. All 16 helper/transport tests can pass while model quality still fails. Dedicated embedding/cancellation/native-network tests remain pending. The browser still has preset sample answers, not this runtime.
