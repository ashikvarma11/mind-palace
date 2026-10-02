# Step 03A — approved Angular browser shell

Date: 2 October 2026. Result: verified browser-only subset, not a desktop release.

Story: explicit sample opt-in → in-memory Angular service → source inspection → summary/decision review → current-state handoff → editable selection. No native/API/database boundary is involved yet; these capabilities are clearly marked unavailable.

## Actual checks

- `npm install --no-fund`: installed/locked 275 packages; audit reported zero vulnerabilities. npm warned about the pre-existing user `precommit` configuration and unapproved optional install scripts; no global configuration was changed. Build success verifies the needed frontend tooling worked.
- `npm run check`: **7 unit tests passed in 2 files**, followed by a successful production build. Initial browser JavaScript/CSS total 328.70 kB (estimated transfer 74.97 kB); lazy workspace chunk 70.11 kB (16.30 kB transfer). No style-budget warning after separating shared primitives from layout, without raising thresholds.
- `npm run test:e2e`: **7 browser tests passed**, one worker, 1.6 minutes. Used existing local Chromium through MP_BROWSER_EXECUTABLE; no paid browser service. Playwright 1.63.0 was pinned. The optional agent-browser launch returned nonzero without a usable browser snapshot; actual automation used the bundled Chromium/Playwright fallback, not a claim that this failed launcher passed.
- End-to-end source/review/handoff: summary review left the proposal proposed; rejection and subsequent confirmation were reflected in handoffs; original source messages stayed unchanged; text selection worked; reload reset the sample.
- Answer UI: preset responses visibly labelled, unknown/injected input abstained, injected script remained inert, original fictional evidence was inspectable; zero external HTTP requests observed in this sample test.
- All 8 routes fit at **1024, 768, 390 and 320 px** with no horizontal document overflow. Keyboard entry reached the skip link. Dark appearance worked and stayed consistent across route navigation.
- `npm audit --omit=dev`: zero vulnerabilities. Build output verified at `dist/mind-palace/browser`.

## Repair history

The first combined viewport/keyboard/theme test exhausted its 45-second budget after completing the viewport loop. Split the checks into separately scoped viewport and keyboard/theme cases, kept every assertion, and used the combobox's verified accessible role/name. All cases passed on rerun. No product check was removed or timeout increased to mask a failure.

Real browser screenshots were inspected in ignored `test-results/`: opening, handoff, sample answer, mobile opening, and dark Today. They are not presented as shipped desktop screenshots.

Final post-formatting regression: `npm run check` again passed 7 unit tests and a warning-free production build (initial 328.70 kB / 74.98 kB estimated transfer, lazy feature 70.19 kB / 16.33 kB). All 7 browser tests passed again in 48.0 seconds. Public-stage review found no credential patterns, private/generated directories, or image/model/installer binaries; Git whitespace check passed after normalizing EOF and source LF policy. Local Git author uses a GitHub no-reply identity, not a personal email.

## Limits

Samples are fictional and memory-only. No durable vault, import service, hash-verified evidence store, inference model, Graphify extraction, Three.js graph, native startup, MCP connection, backup or installer is implemented. Auto-start/Add memory are unavailable, not fake working controls. Header/footer make browser development status visible. Local artwork copies are approved for app use; public asset licensing is separately unresolved.
