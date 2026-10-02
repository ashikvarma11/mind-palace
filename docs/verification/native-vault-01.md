# Windows local vault integration — 2 October 2026

Story: explicit desktop create/open → native allowlisted command → verified frozen Python worker → portable vault files → validated response → safely rendered conversation. No AI, API keys or paid calls.

Implemented fixed native app-local-data/vault paths, canonical UUID-only debug probe isolation, single-flight managed state, owned-child exit control registered before the first health await, explicit command permissions, generated VaultStatus contract, Angular gateway and accessible vault forms/list/source view on Welcome and Sessions. Sources remain unreviewed; manual notes infer no decisions. Other pages still show separate fictional fixtures or unavailable states.

## Actual evidence

- `npm run check`: six contract checks, thirteen Angular unit tests and production build pass. No skipped tests. Tests cover malformed responses, error redaction, no queued duplicate request, empty-draft refusal and stable explicit retry operation ID/unchanged payload.
- `npm run test:rust`: eight tests pass, no skips, initially 10.36 seconds and final sequential repeat 9.48 seconds; includes actual frozen worker save/reopen/CRLF/Tamil read/stop, independently controlled startup termination, framing/error/path guards, strict request fields and single-flight/exit state.
- `npm run build:desktop`: succeeds. Staged resource inventory matches 109 files / 23,673,882 bytes.
- `npm run verify:desktop`: real owned WebView create/save/list/read/close/reopen, route reload and second native process reopen pass. Unicode and script-like text render inertly. Invalid IDs/list limits/unknown input fields/key command are denied. Per-response CSP nonce/styles work; console errors empty. Idle exit and an exit after a lock-blocked request reports BUSY stop both owned worker processes. The script verifies their exact process IDs are no longer alive. No production app-data vault is opened.
- Native full-page screenshot inspected at ignored `.tools/native/verification/native-vault.png`: source/list/form visible, separate from sample mode. Existing Workspace layout retained, not claimed Library redesign.
- Final desktop rebuild and repeated complete WebView flow after lifecycle hardening also pass: no console errors, both owned workers stopped, storage survives reopening/restart. Synthetic vaults/profiles are retained under ignored project-owned verification directories for inspection, not deleted or published.

## Failure history and limitations

During the final lifecycle review, two overlapping Rust test/build invocations caused Windows linker LNK1104 while the earlier test executable was still open. Both invocations were allowed to finish; no process/security setting or source workaround was used. Final verification runs sequentially. Failed shutdown now retains its owned control, vault status does not report an unusable worker connected, and explicit close also confirms a child registered during failed startup before permitting another open.

Initial new retry unit test and actual desktop startup failed. Native console: `Cannot read properties of undefined (reading 'fullFormats')`, body empty. Corrected the generator's inspected CJS helper imports (not handwritten generated output), then regenerated; all thirteen unit tests and full native flow passed. No weaker validation/CSP, increased request deadlines or skipped failures.

Initial browser regression launch could not find Playwright's expected headless shell 1243; no page checks ran. Rerun selects existing Chromium 1234 with process-local MP_BROWSER_EXECUTABLE: all seven browser regressions pass in 2.2 minutes, including all routes at 1024/768/390/320 px, keyboard/theme, no external HTTP in the tested sample flow, inert input and proposal/review/handoff integrity.

UI retry drafts/op_ids persist only in current app memory, not through reload/restart. Worker mutation journals remain durable, but losing an uncertain UI draft requires inspecting existing sessions before importing again. A successfully acknowledged save can be followed by a failed list/read; the success notice is retained and no second save is sent automatically. HTML textareas may normalize pasted line endings; stored source is immutable as submitted, not a claim to recover clipboard byte encoding. The native transport CRLF test independently passes.

No custom folder dialogs, release/installer build, macOS verification, full cancellable job protocol, decision-review integration, durable UI retry recovery, credential/HTTPS integration or model-selection gate is claimed. Normal tested exit stops workers; crash/power-loss/job-object lifecycle hardening remains unverified. Prior timing variability is retained in native-transport-01.md; this flow is not a performance guarantee. AJV CommonJS optimization, informational linker and pre-existing npm config warnings remain disclosed. No user/private vaults, binaries, tooling, screenshots or artwork are included in the source push.
