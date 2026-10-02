# Cloud foundation 01 — offline subset

2 October 2026. No provider inference, real API key, subscription or paid service used. UI unchanged: cannot answer real questions. These are contract checks, not live API compatibility or AI quality results.

## Verified

- Credential-free OpenAI Responses/Anthropic Messages request builders, fixed endpoint values, bounded token output. No HTTP client, send method, keys, tool execution, automatic retries or fallback.
- Explicit local excerpts only: 1–5 selections, 8,000 Unicode code points each, 32,768 total UTF-8 bytes; questions at most 2,000 code points. Offsets are Python code points, not JavaScript UTF-16 units: future UI must convert/test emoji offsets. Sessions use preserved originals, never editable summaries. Decisions include manual provenance/state metadata even when the selected range omits it.
- Entire request preview (including instructions), SHA256, local references. Eight in-memory receipt limit, five-minute eligibility, single-use preparation with explicit sharing/cost acceptance and matching digest. Discard revokes consent; changed source snapshots require another preview. Expired receipts are removed on the next operation, not by a background timer. Preparation returns can_send:false; a future native sender must implement its own trusted consent boundary.
- Bounded provider parsing, incomplete/tool-call/malformed responses rejected. Quote membership checked against shared excerpts, abstention allows no citations, token usage normalized. This is NOT semantic support or approval verification: every answer still requires review and never mutates records.
- Fresh source/frozen processes create/read temporary sessions and prepare an Anthropic preview. Frozen test excludes Python environment variables and developer PATH. Invalid timestamps rejected in both source/frozen reads. Clean-machine and macOS untested.
- Real Windows Credential Manager diagnostic: fresh MindPalace/diagnostic/UUID target, random fake bytes, session-only persistence, deletion in finally and absence verified. Existing credentials neither enumerated nor changed. Temporary entry removed. Not the production credential backend, persistent-key lifecycle or encrypted vault; no blanket same-user process protection claim.

## Results

| Check | Actual result |
| --- | --- |
| Worker suite | 31/31, no skips, final rebuilt-bundle run 10.663 seconds; includes 15 offline cloud tests and selected frozen worker. |
| Diagnostic regression | 19/19, no skips, 8.190 seconds; all three existing frozen diagnostics selected. No model inference rerun. |
| Angular | 7/7 unit tests; production web build passed. No new browser/UI claim. |
| Worker packaging | PyInstaller 6.22.3, Python 3.12.10; 108 files, 23,669,772 bytes, ignored .tools/probe-dist/mind-palace-memory-worker. |

Initial relative schema packaging failed because spec paths resolve under .tools; an explicit schema path fixed it. Warnings exposed missing optional date-time format support; inspected jsonschema's active formats and confirmed invalid dates were accepted. Added a local UTC-Z calendar validator, then tested invalid calendar dates/timezones in source and frozen workers. Other warnings concern conditional POSIX/optional network/Redis imports; exercised behavior instead of inferring success from packaging.

## Remaining boundary

Rust/cargo absent from PATH; vswhere finds no installed Microsoft C++ tools component. Official Tauri Windows prerequisites require Rust/C++ tooling. No global/admin installation attempted. Native supervision, production OS credential commands, key-entry UI, HTTPS transport, cancellation, redacted errors and live verification remain pending. Do not expose real keys through the browser or add a localhost proxy workaround. Live potentially charged calls require later explicit authority.

OpenAI store:false is NOT zero provider retention. Model availability/account access/prices unverified; test model IDs fictional. No SDK dependency or cloud gateway added. Sources/implementation details: research.md, cloud-ai-plan.md and development.md.
