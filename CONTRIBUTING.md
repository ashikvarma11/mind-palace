# Contribute to Mind Palace

Help make saved coding context dependable, readable and easy to inspect.

Start with the [README](README.md), [user guide](docs/user-guide.md) and [roadmap](docs/roadmap.md). The current priority is a reliable Codex capture-to-vault-to-answer workflow. Claude Code and generated AI answers remain separate later work.

## Choose a contribution

Useful areas include bounded Codex event diagnostics, synthetic producer fixtures, accessibility, clear error recovery, public-clone build reproducibility and accurate documentation.

For a major product or architecture change, describe the problem and proposed behavior in an issue first. Include tradeoffs around data access, cost and user consent. A suggestion is not approval to change memory or share source data.

## Set up the part you need

| Work | Start here |
| --- | --- |
| UI or documentation | Node 24.16.0 / npm 11.17.0, `npm ci`, browser sample. |
| Storage or capture | Python 3.12, project-local virtual environment and synthetic source tests. |
| Native desktop | Windows x64, verified staged bundles, compiler/SDK resources, WebView2 and native icons. Prepared-machine flow is documented; a fresh clone is not yet a complete desktop setup. |

Use [development.md](docs/development.md) for exact commands and build limits. Follow [AGENTS.md](AGENTS.md) when using a coding agent. Read the implementation plan, decisions, current status and relevant source/tests before changing a workflow.

## Keep these boundaries

- Preserve original conversation sources and source provenance. Supporting-code changes can flag review; they cannot approve a decision.
- Validate external input and native responses. Keep strict TypeScript and schema boundaries.
- Treat imported content and model output as data, never executable instructions.
- Use synthetic sessions, temporary vaults and fake credentials in tests. Never inspect a user's vault to make a fixture.
- Do not add developer telemetry, hidden cloud calls, automatic provider fallback or uncertain-write retries.
- Do not commit transcripts, vaults, credentials, generated executables, compiler resources or the temporary supplied artwork.
- Record new paths and responsibilities in [file-ledger.md](docs/file-ledger.md) before creating them.

## Validate the change

Run checks that exercise changed behavior. Use the following commands where applicable:

```sh
npm run check
npm run test:e2e
```

```powershell
$env:PYTHONPATH = (Resolve-Path sidecar).Path
./.tools/probe-venv/Scripts/python.exe -m unittest discover -s sidecar/tests -v
```

On a prepared Windows native workspace, build first and run native checks sequentially:

```powershell
npm run build:desktop
npm run test:rust
node tools/verify-native-shell.mjs --codex-workflow
```

Do not run native tests against your real vault or concurrently with a build. The probe creates isolated synthetic roots. Service doubles, local fixed replies and screenshots must be labelled accurately. A new successful run does not erase an earlier failure.

For documentation changes, check local links, commands, screenshot provenance and capability claims. Run `git diff --check`. Full runtime suites are not required for a prose-only edit.

## Submit a pull request

Use a focused branch; coding-agent branches use `codex/`. Explain the concrete problem and resulting behavior. Include:

1. What changed and why.
2. Actual test commands and results.
3. Any unverified platform, native, installer or model behavior.
4. Safe screenshots or synthetic reproduction steps when useful.
5. Updated status, decisions and verification evidence when the change affects an acceptance claim.

Do not attach raw private logs. Report a safe error code, client version, OS/build and a synthetic reproduction. If a second attempt fails the same way, change the investigation method instead of blindly retrying.

Code contributions use the project's [MIT license](LICENSE). Document asset provenance separately. The current temporary logo is not approved for redistribution; use the existing MP lettermark for public screenshots.
