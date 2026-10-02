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
