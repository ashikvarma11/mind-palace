# File ledger — planned before creation

- CONTRIBUTING.md — explain contribution scope, setup, tests, privacy boundaries and review evidence.
- docs/user-guide.md — guide Codex setup, capture, Library, Ask and safe troubleshooting.
- docs/roadmap.md — separate measured capabilities, partial features and remaining acceptance work.
- docs/images/codex-setup.png — show the actual native setup checklist with synthetic data.
- docs/images/session-library.png — evaluated synthetic Library screenshot; removed from the public set because capture caught a refresh in progress.
- docs/images/ask-memory.png — show an actual native quoted answer with synthetic evidence and the public lettermark.
- .tools/native/verification/docs-*.png (ignored) — hold synthetic lettermark screenshot sources for public documentation.
- docs/verification/docs-refresh-14.md — record documentation claim/link/image checks and screenshot provenance.

- docs/verification/codex-runtime-13.md — record bounded native command timing, capture startup failures and complete Codex workflow rechecks.

- .tools/native/verification/codex-setup.png — retain the isolated native guided Codex setup screen for visual verification.
- .tools/native/verification/codex-library.png — retain the isolated native Library reading view with synthetic session evidence.
- .tools/native/verification/codex-ask.png — retain the isolated native local Ask answer and exact synthetic citations.
- .tools/native/verification/codex-setup-narrow.png — retain the isolated 390-pixel native setup layout for overflow checks.

- docs/verification/codex-ui-12.md — record guided Codex setup, Library reading, local Ask, responsive and native workflow verification.
- src/app/features/connections/capture-panel.component.spec.ts — verify UI setup gates, explicit trust uncertainty and blocked/paused capture states.

- tools/verify-codex-trust.py — prepare an isolated synthetic receiver and local provider, then verify actual Codex persisted approval and execution without a bypass.

- .tools/codex-trust-probe/ (ignored) — hold installed-client protocol schemas and isolated normal-hook-trust diagnostics with synthetic sources only.
- docs/verification/codex-trust-11.md — record actual persisted trust, fresh-client execution without bypass, change invalidation and limitations.

- docs/verification/codex-two-minute-10.md — record the user-approved two-minute installed-client test, measured duration, exact rollout and local Ask results, with explicit fixture and process topology limits.

Codex client and recovery checks (4 October 2026):
- tools/verify-codex-client.py — run the installed Codex client with isolated settings and a loopback fixture provider, then verify real hook capture and exact vault evidence without paid inference.
- docs/verification/codex-recovery-08.md — record live-client fixture delivery, recovery, retention, full-size import results and remaining product limits.
- .tools/codex-hook-probe/client-* (ignored) — keep isolated Codex homes, synthetic rollouts, capture settings and safe verification reports for the local client check.
- .tools/codex-hook-probe/client-*/hook-outcomes.jsonl (ignored) — record only hook event, start/result, elapsed milliseconds and safe failure code for deadline diagnosis.
- sidecar/memory_worker/capture_recovery.py — validate bounded Codex rollout metadata, repair known sessions, and confirm exact scoped history previews without reading unrelated stores.
- sidecar/tests/test_capture_recovery.py — verify missing-event repair, history consent/revision checks, malformed-file isolation and safe redundant-prefix retention with synthetic sources.
- Capture runtime settings/history-previews/<uuid>.json — retain a short-lived scoped history candidate manifest for explicit user confirmation.
- sidecar/memory_worker/session_text.py — extract validated Codex user/assistant text spans for local search while preserving exact raw-source evidence offsets.

Codex native workflow verification (4 October 2026):
- docs/verification/codex-workflow-07.md — record the real desktop synthetic end-to-end result, test commands, failed attempts, and remaining live-client limits.

ChatGPT export sync 01 (3 October 2026; source-only, no account/private API access):
- sidecar/memory_worker/chatgpt_sync.py — opt-in bounded ZIP/JSON history and explicit memory-text sync into immutable account-scoped inbox revisions, preserving branches and source fragments.
- sidecar/tests/test_chatgpt_sync.py — synthetic sync/restart/branch/exclusion/memory/hostile archive/consent/concurrency tests without account access or model calls.
- docs/chatgpt-sync.md — source-inspected GitHub shortlist, supported sync contract, developer usage, coverage limits and desktop integration handoff.
- docs/verification/chatgpt-sync-01.md — actual Windows source/subprocess checks, failures and unverified account/native/installer gates.

Shared user-installed hook inbox 02 (latest user direction, 3 October):
- sidecar/memory_worker/capture_inbox.py — hook wrapper, explicitly scoped Markdown memory snapshots and bounded validated JSON/Markdown indexes over immutable captures in one shared local inbox; no hook registration or network.
- sidecar/tests/test_capture_inbox.py — synthetic shared-provider, resumed-session, tampering, pause, index-rebuild and real wrapper-process checks.
- docs/hook-sync.md — approved shared-folder hook architecture, supported-client setup examples, index contract and remaining native/memory gates.
- docs/verification/hook-inbox-02.md — record actual source hook/index checks separately from installation and desktop ingestion.
- sidecar/memory_worker/paths.py — share an explicit extended Windows path helper for capture/export IO without changing machine settings.
- tools/capture-hook.py — working-directory-independent source/frozen launcher for the user-installed hook receiver and inbox index command.
- .tools/capture-dist/memory-capture/ — ignored generated Windows onedir capture executable and bundled Python/dependency support files for synthetic packaging QA only.
- .tools/capture-build/ and .tools/memory-capture.spec — ignored generated PyInstaller intermediates/spec for the dedicated capture development build; not installer/release artifacts.

Automatic capture receiver 01 (development subset; no assistant registration or private-data reads):
- sidecar/memory_worker/session_capture.py — consent-file-gated hook receiver, scoped bounded transcript reads, immutable idempotent local snapshots and redacted errors.
- sidecar/tests/test_session_capture.py — synthetic hook process/storage tests for both provider labels, append/resume, duplicates, partial writes, pause, scope escape and malformed data.
- docs/automatic-capture.md — revised priority, exact capture contract/setup prerequisites, provider coverage and remaining app/normalization/history gates.
- docs/verification/session-capture-01.md — actual receiver checks and explicit distinction from live assistant capture and AI inference.


Offline request-preview UI 01:
- schemas/native-ai-preview.schema.json — strict credential-free request/result/prompt/discard contracts, fixed provider endpoint/body shapes and can_send:false.
- tools/generate-contracts.mjs and core/contracts.generated.ts/validators.generated.ts — merge inspected preview definitions into generated types/static validators; no runtime evaluation.
- src/app/core/ai-gateway.ts/spec.ts — native-only preview/discard/cancel, validate exact selected source/question binding, expiry and safe errors; no key/send API or browser persistence.
- src/app/features/ask/ai-preview-panel.component.ts/html/scss — explicit session/range/question/provider/model selection, inert complete payload review, expiry, discard and cancellation; sending visibly disabled.
- src/app/features/workspace/workspace-page.component.ts/html — mount real preview panel on non-sample Ask route while preserving fictional sample answers.
- tools/tests/test-contracts.mjs and tools/verify-native-shell.mjs — malformed preview contracts and real desktop review/discard/cancel/reopen checks using synthetic data.
- docs/verification/ai-preview-ui-01.md — actual generated-contract/unit/build/native UI results and remaining HTTPS/key gates.

AI request boundary 01 (offline native previews; no HTTPS or key-entry UI):
- src-tauri/src/ai_requests.rs — single-flight UUID-targeted cancellation with RAII cleanup and bounded deadline, independent of worker IO locks.
- src-tauri/src/ai_requests_tests.rs — mocked pending/completed/timeout/drop/race tests proving cancellation cannot affect another request.
- src-tauri/src/commands.rs — strict typed local excerpt preview/discard commands and targeted cancellation; cancellation closes the worker connection, never retries.
- src-tauri/src/worker.rs/worker_tests.rs — allow only offline preview/prepare/discard methods and cancel-safe framing; exercise frozen-worker receipts, consent/replay and cancellation.
- src-tauri/src/lib.rs/build.rs/capabilities/default.json — enumerate only offline AI preview/discard/cancel permissions; still no key or network commands.
- docs/verification/ai-requests-01.md — record offline native request tests/build and remaining UI/HTTPS gates honestly.

Native credential foundation (internal only, fake-key tests, no WebView commands):
- src-tauri/src/credentials.rs — allowlisted provider targets, secret-redacted/zeroizing ownership, fail-closed Windows Credential Manager save/read/status/remove; no plaintext or network fallback.
- src-tauri/src/credentials_tests.rs — synthetic validation/redaction tests and fresh UUID-scoped real Windows write/read/replace/remove, with cleanup and no access to production targets.
- docs/verification/native-credentials-01.md — record native credential API and actual fake-key checks separately from pending key-entry/cancellation/HTTPS/macOS gates.

Native storage connection subset (one app-managed vault, no AI):
- src-tauri/src/paths.rs — resolve fixed native resource/vault paths and UUID-only debug test isolation, rejecting linked ancestors.
- docs/verification/native-vault-01.md — record real command/UI persistence and shutdown results, with remaining release gates.
- schemas/native-memory.schema.json — strict public session metadata/list/read/create-result and truthful vault status contracts shared by validators and generated UI types.
- tools/generate-contracts.mjs — generate schema-derived TypeScript and precompiled validators, with drift checking and no runtime schema-code evaluation.
- src/app/core/contracts.generated.ts/validators.generated.ts — generated native-session types and offline runtime validators; never hand-edit.
- tools/stage-worker.py — stage the existing frozen worker and produce a bounded SHA-256 resource manifest; refuse redirected paths.
- tools/tests/test_stage_worker.py — prove fixed staging paths, bounded inventories, tamper refusal and recoverable refresh using synthetic bundles.
- .tools/worker-stage-backups/ — ignored recoverable copies of previously verified generated staging bundles; never user vaults.
- src-tauri/resources/memory-worker/worker-manifest.json — ignored staged frozen runtime and generated integrity inventory, not source or a release package.
- src-tauri/src/worker.rs — supervise only the fixed verified worker with bounded correlated JSONL, single-flight requests, timeout and shutdown.
- src-tauri/src/worker_tests.rs — test private response framing, resource guards and real frozen-worker save/list/read/reopen/stop using synthetic vaults.
- docs/verification/native-transport-01.md — separate verified internal Rust-to-worker behavior and startup failures from the pending desktop command/UI/lifecycle gates.
- src-tauri/src/commands.rs — create/open/close/status and allowlisted session calls for one native app-data vault, never WebView-supplied paths/executables.
- src/app/core/local-vault.ts/spec.ts — validate native responses and own loading/error/connection/session state without browser persistence.
- src/app/features/vault/vault-panel.component.ts/html/scss — render explicitly real local session storage separately from fictional sample screens.
- sidecar/tests/test_session_list.py — prove bounded deterministic listing, pagination, metadata validation and persistence across reopen.
- tools/tests/test-contracts.mjs — test generated validators against malformed data and check that browser code contains no dynamic evaluation.
- docs/verification/native-storage-01.md — report actual Rust/Python/UI checks and pending folder-dialog/AI/release gates.

Native toolchain development probe (no system installer or redistribution):
- config/native-toolchain.json — lock official Rust/MSVC developer artifact URLs, SHA-256 hashes and extraction layout.
- tools/setup-local-native.py — bounded verified downloads and traversal-safe extraction into ignored project-owned tooling only.
- tools/run-native.py — run allowlisted Rust/Cargo probes with a process-local compiler/SDK environment, never global PATH changes.
- tools/fixtures/native-smoke.rs — compile and run a synthetic Rust executable to prove the native linker prerequisite.
- tools/tests/test_native_setup.py — test archive path, duplicate, bounds and hash protections without network downloads.
- docs/verification/native-toolchain-01.md — record real compiler checks separately from unbuilt Tauri/product features.

Step 03 native shell subset:
- src-tauri/Cargo.toml/Cargo.lock — pin Tauri 2.12.1 and tauri-build 2.7.1 and resolve native dependency versions.
- src-tauri/build.rs — standard Tauri build integration with one explicitly permissioned health command.
- src-tauri/src/main.rs/lib.rs — start the development desktop window and expose truthful shell-only health.
- src-tauri/tauri.conf.json — embed inspected Angular output, restrict resource/network loads with CSP, disable bundling for this probe.
- src-tauri/capabilities/default.json — allow only main-window native health using tauri-build's generated permission; no file/shell/network APIs.
- src-tauri/permissions/autogenerated/ — ignored generated allow/deny permissions for the enumerated native health command, not hand-maintained duplicate identifiers.
- src-tauri/icons/ — ignored mechanical platform icon derivatives of approved local artwork; not redistributed.
- docs/verification/step-03b.md — distinguish native compilation/launch observations from pending UI-worker integration.
- tools/verify-native-shell.mjs — launch only the locally built app with an isolated WebView profile and temporary loopback debugging, check real rendering/native health/reload, close owned process and retain ignored synthetic screenshot.
- src/app/app.config.spec.ts — verify Angular accepts the document's native style nonce and uses no fabricated nonce in browser mode.
- src/index.html/src/app/app.config.ts — add a bundled inert style marker and pass its Tauri-generated per-response nonce to Angular component styles.
- src/app/app.component.ts/html — label the actual desktop/browser presentation without claiming connected storage or AI.

Steps 00–01: root AGENTS.md/CLAUDE.md provide execution rules; .gitignore excludes private/generated data; .npmrc pins dependencies; LICENSE is approved MIT code text; README.md is the honest development overview; docs/implementation-plan.md is the revised full plan; docs/decisions.md holds evidenced choices; docs/implementation-status.md tracks real gates; docs/research.md records current primary sources; docs/repository-setup.md verifies local/remote identity; docs/design-review.md records approved UI; docs/session-context.md is a content-safe project handoff; docs/file-ledger.md is this ledger.

Step 03A scaffold: package.json/package-lock.json define and lock verified scripts/dependencies; angular.json defines client build/test targets; tsconfig.json/tsconfig.app.json/tsconfig.spec.json define strict compiler inputs; src/main.ts bootstraps Angular; src/index.html defines local metadata/favicon; src/styles.scss/styles tokens define global theme/a11y; src/app/app.component.ts/html/scss render the approved shell; src/app/app.config.ts and app.routes.ts register providers/routes; generated scaffold starter/tests are inspected and reconciled, not assumed.

Step 03A additional planned paths: src/app/core/workspace-store.ts/spec.ts own and test explicitly synthetic state; src/app/features/workspace/workspace-page.component.ts/html/scss render route views and unavailable states; tests/e2e/shell.spec.ts verifies user flows; playwright.config.ts configures scoped browser QA; tools/probe-runtime.py performs real capability checks; docs/verification/step-00.md/step-01.md/step-02.md/step-03a.md record actual results; docs/feasibility.md records missing native/model gates; docs/development.md records real launch/check instructions; design/brand/README.md records artwork provenance; public/brand/logo-original.png/logo-preview.png and public/favicon.png are local approved artwork derivatives (ignored until licensing resolved).

- src/styles/workspace-primitives.scss — reusable, root-scoped typography/forms/buttons/status primitives, separated from feature layout to stay within component style budgets.
- .editorconfig/.prettierrc — inspected scaffold formatting conventions; no system configuration changes.
- docs/product-requirements.md — complete R01–R23 matrix and honest first-milestone/demo/release boundaries.
- docs/branding-brief.md — approved Workspace typography/palette and supplied raster-artwork constraints.
- THIRD_PARTY_NOTICES.md — actual locked icon license and separation of dependency/artwork/code licensing.
- public/README.md — preserve the static-assets directory in public clones and explain omitted artwork.
- .gitattributes — keep generated/source text consistently LF across Windows/macOS without changing global Git preferences.

Step 02 packaging subset (not the complete model/Graphify gate):
- tools/requirements-probe.txt — pin the three direct dependencies for isolated validation/locking/freezing experiments.
- tools/requirements-probe-lock.txt — record exact resolved transitive versions for this Windows/Python probe environment.
- tools/tests/test_runtime_probe.py — test source and optional frozen capability results, lock contention/release and invalid schema rejection.
- tools/probe-runtime.py — extend the synthetic capability probe with real schema rejection and cross-process locking; keep it diagnostic-only, not a production worker.
- .tools/probe-venv/ and .tools/probe-dist/ — ignored isolated environment and native diagnostic bundle, never release artifacts.
- .tools/graphify-artifact/ and .tools/graphify-source/ — ignored hash-verified upstream wheel and extracted source for inspection, not user repositories.
- tools/probe-graphify.py — run only the inspected local extractor on synthetic fixtures with network denied and validate graph evidence.
- tools/fixtures/probe-repo/package.json — synthetic TypeScript fixture identity, no scripts/dependencies.
- tools/fixtures/probe-repo/src/auth.ts — synthetic auth service with a known cross-file store call.
- tools/fixtures/probe-repo/src/store.ts — synthetic store class exposing the known call target.
- tools/tests/test_graphify_probe.py — exercise fixture extraction, evidence checks and denied network attempts.
- config/dependency-manifest.json — exact upstream artifact hash/version/source and measured probe scope, not production release approval.
- tools/probe-mcp.py — synthetic local MCP stdio server exposing one diagnostic-only read tool, no vault or cloud access.
- tools/tests/test_mcp_probe.py — run real local stdio initialization/tool checks against source and optional frozen diagnostic server.
- .tools/mcp-artifact/ — ignored registry-hash-verified SDK wheel retained for diagnostic provenance, not release distribution.
- .tools/llama-b11342/ and .tools/models/ — ignored checksum-verified official CPU runtime and candidate GGUF downloads for local-only measurement.
- config/models.json — lock candidate model revisions, artifact sizes/hashes/licenses and evaluation status; no unsupported production selection.
- tools/probe-models.py — start an authenticated loopback-only CPU runtime, run labelled synthetic cases and record actual timing/results with guaranteed cleanup.
- tools/fixtures/probe-cases.jsonl — ten explicit proposal/approval/rejection/recall cases for candidate comparison, not a held-out release evaluation.
- tools/tests/test_model_probe.py — validate fixture/measurement parsing and local-runtime safety settings without treating unit tests as real inference.
- docs/verification/step-02-models.md — record runtime/model artifact verification, measured performance/quality and missing gates.
- docs/verification/model-probe-results.json — preserve exact synthetic benchmark outputs and evaluation limitations, no runtime credentials or personal data.

Steps 04A/05A foundation subset, planned before creation:
- schemas/ipc.schema.json — strict bounded private request/response envelopes and allowlisted foundation methods.
- schemas/vault.schema.json — versioned vault identity with a UUID and explicit local format.
- schemas/memory-record.schema.json — manual-only decision snapshots with proposed/confirmed states, revision and explicit provenance; other kinds remain unavailable.
- sidecar/pyproject.toml — package the worker with exact validated schema/OS-lock dependencies.
- sidecar/memory_worker/__init__.py/__main__.py — version and explicit private UI-mode launch against a trusted CLI-selected vault.
- sidecar/memory_worker/contracts.py — load local bundled schemas and reject invalid/unknown external fields without content logging.
- sidecar/memory_worker/errors.py — safe structured worker failures with no raw content/paths in messages.
- sidecar/memory_worker/paths.py — validate root and generated internal paths, rejecting traversal/reparse points and broad root targets.
- sidecar/memory_worker/atomic_io.py — flushed sibling writes with expected hashes and replace, preserving conflicts.
- sidecar/memory_worker/journal.py — persist bounded transaction intents, validate recovery targets and apply idempotently without overwriting external changes.
- sidecar/memory_worker/vault.py — create/open foundations, preserve text sources, create/read sessions and manual decisions, confirm decisions with audit events.
- sidecar/memory_worker/service.py/protocol.py — central method/parameter validation and bounded UTF-8 JSONL dispatch; no generic filesystem/shell functions.
- sidecar/tests/test_foundation.py — verify temporary-vault persistence, immutable-source checks, approval separation, revision/idempotency and interrupted recovery.
- sidecar/tests/test_protocol.py — verify real source/frozen stdio, malformed frames, UTF-8, envelope limits and safe errors.
- tools/worker-entry.py — frozen worker entry point, never a diagnostic pretending to be the app.
- docs/verification/step-04a-05a.md — record actual Python transport/storage tests separately from unimplemented native UI/cache/import/model features.
- docs/cloud-ai-plan.md — specify user-approved optional OpenAI/Anthropic API-key mode, cost disclosure, secure credentials, scoped consent and no-spend development checks.

Cloud foundation 01 (offline subset; no credentials or network):
- schemas/cloud-ai.schema.json — strict bounded preview selections, consent, and answer/citation contracts; no API-key fields.
- sidecar/memory_worker/retrieval.py — select only explicit character ranges from validated local source snapshots under the vault lock.
- sidecar/memory_worker/cloud_contracts.py — build credential-free OpenAI/Anthropic request bodies and safely parse bounded responses with exact-quote checks.
- sidecar/memory_worker/cloud_preview.py — maintain short-lived, bounded, single-use preview receipts bound to exact payload hashes; preparation is not sending.
- sidecar/tests/test_cloud_foundation.py — synthetic no-network selection/consent/provider/citation/usage/error tests, not live AI quality verification.
- docs/verification/cloud-foundation-01.md — report offline adapter and frozen-worker verification with native/key/live-call limitations.
- tools/probe-credentials.py — test Windows Credential Manager only with a fresh diagnostic target and random fake bytes, cleaning up in finally; never enumerate existing credentials.
- tools/tests/test_credential_probe.py — verify diagnostic target restrictions and real write/read/remove with fake data, no providers or production keys.

Hook desktop control 03 (planned before creation, 3 October 2026):
- sidecar/memory_worker/capture_control.py — fixed app-owned setup/status/consent/index operations, explicit source scopes, safe manual hook snippets, no assistant settings writes.
- sidecar/tests/test_capture_control.py — synthetic consent, pause, conflict, scope and actual frozen control/capture/index checks.
- src-tauri/src/capture.rs — narrow supervised capture-control gateway with fixed resource/root resolution and bounded transport.
- schemas/native-capture.schema.json — strict setup/status/index native response contracts.
- src/app/core/capture-connection.ts — validated desktop capture gateway and explicit consent state.
- src/app/core/capture-connection.spec.ts — native boundary malformed-response/consent/error tests.
- src/app/features/connections/capture-panel.component.ts — Connections setup/status component with manual installation instructions.
- src/app/features/connections/capture-panel.component.html — per-client explicit scope, consent and copyable snippet controls.
- src/app/features/connections/capture-panel.component.scss — responsive setup fields and inert snippet layout.
- tools/stage-capture.py — reuse bounded resource staging for the fixed capture receiver inventory.
- docs/verification/hook-desktop-03.md — preserve source/frozen/native/UI evidence and remaining actual-client/ingestion gates.
- src-tauri/resources/memory-capture/ (ignored) — full staged receiver support files and integrity manifest.
- node_modules/ (ignored project junction) — reuse already installed original-project dependencies without global installation.
- .tools/native/verification/ (ignored) — isolated synthetic native capture roots and WebView profiles.

Hook canonical ingestion 04 (planned before creation, 3 October 2026):
- sidecar/tests/test_capture_ingest.py — prove validated hook revisions become one canonical unreviewed Session, remain idempotent, and reject divergent or changed sources.
- docs/verification/hook-ingest-04.md — record real source/frozen/native/UI ingestion checks and the remaining live-client limitation.
- Vault runtime `imports/<provider>/<session-key>.json` — map one validated provider session to its stable canonical Session/source identifiers and imported revision set.
- Vault runtime `sources/<source-id>/revisions/<sha256>.txt` — preserve each selected canonical hook-source revision as an immutable UTF-8 file.

Hook producer contracts 05 (planned before creation, 3 October 2026):
- sidecar/tests/fixtures/codex-hook-events.json — hold synthetic Codex lifecycle event shapes and opaque JSONL lines based on the official hook contract.
- sidecar/tests/fixtures/claude-code-hook-events.json — hold synthetic Claude Code lifecycle event shapes and opaque JSONL lines based on the official hook contract.
- sidecar/tests/test_hook_contracts.py — prove both provider event fixtures pass the bounded receiver and preserve transcript bytes without parsing provider instructions.
- tools/measure-hook-deadline.py — measure frozen receiver process latency against a selected synchronous hook deadline using only temporary synthetic data.
- tools/probe-codex-hook.py — replace live Codex hook identifiers and transcript paths with synthetic values before invoking the receiver, and record only event names.
- docs/verification/hook-contracts-05.md — record provider contract fixture, installed-client probe and deadline measurement evidence with explicit limits.
- .tools/codex-hook-probe/ (ignored) — hold temporary synthetic consent, transcript, event-name marker and inbox data for the installed Codex probe.
- .codex/hooks.json (temporary probe only) — load the privacy-safe project hook during the installed Codex check, then remove it after the check.

Codex reliability 06 (planned before creation, 3 October 2026):
- docs/verification/hook-reliability-06.md — record stale-prefix regression evidence, focused checks, and the remaining spool/chunk/live-session gates.
- Capture runtime `inbox/spool/<provider>/<unique-id>.json` — hold one immutable, unique hook delivery until an app-side index operation validates and publishes its content-addressed snapshot.
- Capture runtime `inbox/objects/chunks/<sha256>.jsonl` — preserve one content-addressed transcript segment with boundaries only after complete JSONL records.
- Capture runtime `inbox/<provider>/<session-key>/<transcript-sha256>.json` schema 2 — preserve ordered chunk references and exact transcript identity without embedding the full transcript.
- Capture runtime `inbox/failures/<unique-id>.json` — record bounded hook failure code, provider, event type and time without session content, identifiers or source paths.
- Capture runtime `inbox/health.json` — cache validated local inbox usage, failure count, pending spool count and retention settings for hook preflight and the desktop status view.
- Capture runtime `inbox/imported/<provider>/<session-key>.json` — store the validated vault-import acknowledgment required before retention can remove a redundant prefix.
- Capture runtime `settings/codex-hooks-backups/<uuid>.json` — preserve exact user hook settings before each Mind Palace install or removal edit.
- Codex runtime `~/.codex/memories/mind-palace-handoff-2026-10-03.md` — retain a concise local handoff for this Mind Palace session; repository plans, decisions, status and verification remain authoritative.

Caveman side note (explicitly requested, recorded before creation, 4 October 2026):
- C:/Users/varma/.codex/skills/caveman/ — hold the pinned upstream JuliusBrussee/caveman skill for Codex discovery; installer copies only the selected skill directory.
- C:/Users/varma/.codex/hooks/caveman-context.ps1 — emit local skill context on SessionStart and SubagentStart without reading prompts or transcripts.
- C:/Users/varma/.codex/hooks.json — merge these user-level context hooks while preserving all existing hook groups.
- C:/Users/varma/.codex/AGENTS.md — retain the requested always-on response preference and pass it to delegated agents when hook trust is pending.
- C:/Users/varma/.codex/hooks/caveman-backup-<uuid>.json — preserve exact prior hooks and global instruction bytes before the authorized configuration edit.
- docs/verification/caveman-setup-09.md — record skill provenance, actual hook checks, preservation and trust limits.
- .tools/caveman-probe/ (ignored) — hold isolated synthetic Codex hook configuration and content-free delivery results without account credentials.
