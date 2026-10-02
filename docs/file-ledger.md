# File ledger — planned before creation

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
