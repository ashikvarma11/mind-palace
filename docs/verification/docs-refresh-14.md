# Public documentation refresh — 5 October 2026

## Scope and changes

The user asks for current workflow/pending work, an accessible GitHub README, screenshots, setup guidance and contribution instructions. Replaced the stale receiver-only README with the implemented Codex workflow, measured capability tables, workflow diagram, real screenshots, setup path, privacy boundaries, evidence links and explicit pending items. Added user-guide.md, roadmap.md and CONTRIBUTING.md. Rewrote development.md around browser, source and prepared-native paths instead of old disconnected-shell instructions. Added current-reader pointers to automatic-capture.md and hook-sync.md. The current AI-off label is explained rather than silently changing the app.

The public desktop build is not a published installer. Fresh-clone native prerequisites/artwork remain a real gap, now described explicitly. Current capabilities refer to this development worktree. Code, documentation and generated public assets need a reviewed checkpoint together before publication; this task did not commit or push any file to GitHub.

## Native screenshot provenance

`node tools/verify-native-shell.mjs --codex-workflow --docs-screenshots` passed the full native workflow, exit 0, isolated run `1d87de24-04f6-4c5b-ad28-0abf4dcf211b`: guided setup, hook merge/removal, app-closed capture, restart import, exact source, known-tail repair, quoted Ask and source opening, title filter, sync/history confirmation and exact 20 MiB native storage/read. The fixture uses synthetic sessions, not private conversations or paid inference.

Public screenshot mode triggers the app's actual missing-artwork error handler to show the existing MP fallback. It does not alter a saved image, use generated artwork or publish the supplied logo with unresolved redistribution provenance. The setup screenshot captures only the checklist, excluding local source paths. Ask contains only the synthetic SQLite/CopperKite evidence. Both final public images were visually inspected. Neither exposes a username, local source path, vault contents from a real user or credentials.

The evaluated Library image caught a refresh in progress and was excluded from the public set. Improved its future capture wait to require a completed reload notice and hidden working indicator. A subsequent full screenshot attempt, `0171a185-1607-4f04-857a-cb03bc96730a`, failed with `Synthetic hook timed out at 30 seconds` before producing the updated Library image. Kept the already successful setup/Ask screenshots and did not repeat the full run a third time. This retains the known intermittent runtime failure; it does not negate the earlier pass or certify all future captures.

| Public image | Bytes | SHA-256 |
| --- | ---: | --- |
| `docs/images/codex-setup.png` | 46,708 | `3d1f9d2fd516abf4a708da3dfed7ff8f25d504641c9988b012480368b98a78a7` |
| `docs/images/ask-memory.png` | 98,737 | `05167ea6b610cc181d4bbadc44e1625b185e1522344b6b04747e36b846f8bfad` |

## Checks

Initial documentation link check: **50 local links/anchors passed**. Final check after excluding the Library screenshot: **49 local links/anchors passed**, zero broken links. Public image PNG signatures/dimensions validated; setup 1440 × 643, Ask 1581 × 1604. Probe JavaScript syntax and `git diff --check` passed. Existing line-ending normalization warnings remain.

Capability/limit claims were checked against source, package scripts, staging helpers and codex-runtime-13.md, codex-trust-11.md, codex-two-minute-10.md and implementation-status.md. Latest prior suites remain **35 Angular / 19 Rust**; these were not rerun for prose-only changes. New-environment setup commands derive from inspected project configuration, not a fresh-clone installation test. No GitHub-rendering or newly provisioned machine acceptance is claimed.

The 18-of-20 delivery discrepancy, intermittent timeout cause, Claude Code end-to-end verification, generated model answers, canonical reviewed memory, fresh-clone desktop packaging/installer and Mac acceptance remain open.


Publication follow-up, 5 October: user explicitly authorizes push, then requests pending items removed from README. Removed the roadmap table and open-acceptance paragraph from that entry page; retained accurate current behavior, development-build identity and evidence scope. Pending work remains in roadmap/status/verification. The publication includes matching implementation and tests; private/generated assets remain excluded.
