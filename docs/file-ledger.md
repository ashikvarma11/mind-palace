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
