# What works and what comes next

**Updated 5 October 2026.** This page describes the current development build. Approved scope, implemented code and measured acceptance are separate.

## Working and measured

| Workflow | Evidence |
| --- | --- |
| Native Codex setup, vault import, Library and quoted Ask | Full synthetic native workflow passed, including app-closed capture and restart. [Report](verification/codex-runtime-13.md). |
| Exact large-source storage | Complete 20 MiB capture/import/read matched SHA-256 through the native boundary. |
| Normal Codex hook trust | Installed CLI approval persisted; fresh clients ran without bypass. Changed definitions required review. [Report](verification/codex-trust-11.md). |
| Recovery and history | Known-session missed tails and explicit history confirmation passed. |
| Manual local storage | Paste, notes, reopen and original-source checks are available. |
| Browser sample | Fictional exploration only; no personal vault persistence. |

## Next: Codex reliability

1. Diagnose the two-minute test's **18-of-20** verified Stop/SessionEnd deliveries. Preserve the failure evidence; do not repeat the duration test merely to obtain a pass.
2. Investigate intermittent Windows capture timeouts with bounded stage timing. Development hash optimization reduced measured resource cost; it did not establish every timeout's cause.
3. Verify special-path hook timing and termination before the first successful capture.
4. Complete safe hook upgrades and ambiguous partial-install repair.
5. Finish incremental large-inbox cleanup and expired history-preview cleanup.

## Product and distribution

| Area | State and remaining work |
| --- | --- |
| Public desktop setup | Prepared-machine builds work. Fresh-clone reproducibility, approved redistributable artwork and complete resource packaging are pending. |
| Windows installer | No published or verified installer. Other-machine installation remains unproved. |
| Claude Code | Shared capture foundations and controls exist. Installed-client end-to-end verification follows Codex reliability. |
| Reviewed memory | Markdown snapshots can remain unreviewed in the inbox. Canonical memory records and explicit evidence-backed proposal/review are pending. |
| Local AI | No selected production model or generated-answer feature. Model acceptance and integration remain pending. |
| Optional provider AI | Offline request preview/control and fake-key credential foundations exist. Real key entry, consented sending and generated answers are unavailable. |
| Library design | Session list/reader is implemented. Broader navigation/design work remains. |
| Today, Decisions, Resume | Sample demonstrations exist. Complete real-data workflows remain pending. |
| Mac | Native acceptance and distribution remain unverified. |
| Ordinary ChatGPT/Claude chats | Web/desktop account-history sync is deferred. Coding-client capture is the current scope. |

## Evidence rules

A build pass does not prove a user workflow. A mock reply does not prove real inference. Browser screenshots do not prove native storage. A hook file does not prove runtime approval or delivery.

Recorded checks use synthetic data. Keep failed runs and scope limits visible. The full history lives in [implementation status](implementation-status.md), [verification reports](verification/) and [decisions](decisions.md).

[User guide](user-guide.md) · [Contribute](../CONTRIBUTING.md) · [Back to README](../README.md)
