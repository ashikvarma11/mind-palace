# Automatic conversation capture — active priority

2 October 2026. The user explicitly requests automatic capture of all conversation sessions in Claude, Codex and ChatGPT, including existing history and ongoing sessions. Keep the paste feature as a fallback, but do not use it to claim this requirement is complete. Other note features and paid API transport are deprioritized. Capture and model inference are distinct: storing original local transcripts does not require a model call.

## Coverage and verified connection points

- Claude Code: official hooks provide `session_id`, `transcript_path` and lifecycle events. Local capture receiver implementation starts here; actual installed-client registration and transcript-format normalization remain untested.
- Local Codex: official hooks provide equivalent fields. Transcript wire format is explicitly not stable. Local-only versus cloud-orchestrated threads have different hook support; do not advertise a local hook as all Codex coverage.
- Ordinary ChatGPT and Claude web/desktop chats: no universal live-history connection has been established. Account permission alone does not establish a supported read API. Investigate each client separately, including explicit browser-extension capture as a proposal, not a verified capability. Do not scrape cookies, tokens or undocumented account endpoints.
- MCP exposes tools, not a universal conversation subscription. Generated memory files are incomplete recall sources, not substitutes for original conversations.

Official pages opened 2 October 2026: https://code.claude.com/docs/en/hooks ; https://learn.chatgpt.com/docs/hooks ; https://learn.chatgpt.com/docs/enterprise/cloud-local-access . OpenAI Docs skill guided current source lookup. No private transcript or credential read was performed.

## Receiver 01 — implemented development contract

`memory_worker.session_capture` is a separate source-only hook entry point. It is not added to the current frozen worker, IPC method list or native app yet. No assistant configuration is changed automatically and no hook is registered in the developer's account. Test only with temporary synthetic files until desktop consent/setup is implemented.

The hook command receives an event JSON object on stdin and an absolute `--config` path. Configuration is exactly:

```json
{
  "schema_version": 1,
  "provider": "claude-code",
  "enabled": true,
  "source_root": "ABSOLUTE_APPROVED_TRANSCRIPT_DIRECTORY",
  "inbox_root": "ABSOLUTE_DEDICATED_CAPTURE_INBOX"
}
```

Both directories must be absolute, dedicated, unlinked, and non-overlapping. Provider is `claude-code` or `codex`; this does not claim real-client compatibility beyond the hook envelope. Configuration is an explicit opt-in artifact, not an authorization boundary against other programs running as the same OS user. Future UI must explain that complete raw transcripts may include sensitive prompts, tool results and paths. Capture is plaintext local storage, not encrypted. No provider key, browser token, network call or new dependency is needed.

Accepted event names are SessionStart, UserPromptSubmit, Stop, SessionEnd and Interrupt. The receiver archives the available complete JSONL prefix without interpreting roles, approvals or timestamps. It preserves its UTF-8 bytes, including CRLF, using a JSON string plus SHA-256/byte count. Incomplete final records wait for a later event. Limits: 64 KiB hook/config, 20 MiB transcript, 1 MiB record. Oversized/invalid transcripts fail visibly; no successful empty import. Transcript paths must be `.jsonl` files beneath the approved source directory; symlinks/junctions and outside paths are rejected. A changing file is reported busy, not retried implicitly.

Snapshots live at `<inbox>/<provider>/<hash(provider, session_id)>/<transcript_sha256>.json`. New content produces a new immutable revision under the same session key. Duplicate content is not rewritten, including after process restart; tampered collisions fail without overwriting them. There is no mutable latest pointer, so out-of-order hooks cannot roll it backwards. A lock serializes writes and consent is reread before transcript persistence. Pausing stops subsequent persistence; copies already saved are retained. Snapshot revisions currently duplicate unchanged prefixes, so long-term disk quotas and incremental storage are required before broad rollout.

The command emits no stdout, conversation text, full paths or exception strings. Non-content status/error codes go to stderr. These are receiver diagnostics, not yet a desktop capture-status display. Event hook success means `captured`, `duplicate`, `waiting`, `paused` or `unavailable`, not normalized, indexed or answered. A missing transcript is unavailable. JSONL object shape is syntactically checked only; unknown producer formats remain raw, `normalized:false`.

## Implementation order from here

1. Finish receiver correctness with synthetic subprocess tests. Do not call this live monitoring.
2. Package a dedicated capture entry point and desktop consent/connection controls, with provider-specific roots resolved from verified configuration, exclusions, pause and visible failures. Preserve existing assistant hooks/configuration; preview user-triggered registration and support removal.
3. Register and verify one actual local client using a synthetic conversation: user turn, assistant turn, resume, parallel sessions, pause, app background/closed and restart. Do not run paid generations without authority. Session-end is not the only trigger; capture each completed turn, and reconcile missed events.
4. Fixture-verify local transcript formats and normalize visible user/assistant messages with source offsets, branches, event identity and available timestamps. Preserve raw source revisions. Scan existing history only within explicit approved roots, with bounded jobs and progress. A missing/deleted source must not silently erase existing copies.
5. Import capture inbox through the app's single writer, into canonical sessions/source storage with provenance (not `pasted_text`). Reconcile resumptions without listing every snapshot as a different conversation; build local retrieval over the originals. Never infer an approved decision from an assistant suggestion.
6. Verify ordinary Claude and ChatGPT capture separately. A browser extension captures only supported connected browser surfaces; it must report that it cannot cover every desktop/mobile/cloud history session. Full account coverage remains a product gate, not a marketing claim.
7. Connect bounded retrieval to the existing assistants, then evaluate evidence-backed answers. Capturing transcripts alone does not provide an inference engine inside Mind Palace.

Release gate: test real session capture, original-message fidelity, no duplicate sessions, missed-event recovery, exclusions/pause/deletion, indexed retrieval and honest coverage on each claimed client. No universal/all-session claim until every claimed surface is verified.
