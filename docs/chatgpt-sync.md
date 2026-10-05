# ChatGPT history and memory sync — 3 October 2026

Superseded active approach: the user subsequently chooses **Codex and Claude Code only**, user-installed hooks and one shared local inbox (D024). No further ordinary-account exporter/browser/source-scan work is active. Preserve this research and tested independent importer as a fallback; use hook-sync.md for current implementation and next steps.

The user requests ChatGPT history and memory sync and GitHub research, then points out that installed assistants may have local memory directories. Prefer verified direct local stores over exports where available. Ordinary ChatGPT account history, local Codex sessions, Claude Code sessions and generated memory are separate sources; do not label one as complete coverage of another.

## Local stores versus account data

Official Claude Code documentation establishes plaintext sessions under `~/.claude/projects/<project>/*.jsonl` and auto memory under `~/.claude/projects/<project>/memory/`. The latter includes `MEMORY.md` and topic Markdown files; settings may override its location. User-authored `~/.claude/CLAUDE.md` is guidance, not automatically approved decisions or a complete transcript. Sources: https://code.claude.com/docs/en/memory and https://code.claude.com/docs/en/how-claude-code-works .

Official OpenAI documentation establishes local Codex memory under `~/.codex/memories/`, separate from ChatGPT web memory: https://learn.chatgpt.com/docs/customization/memories . No such memory directory was present in the narrowly inspected default Codex home. Do not turn memory on, trigger generation or change assistant settings automatically.

Metadata-only inspection on this Windows machine found a default Claude Code projects directory with four immediate project directories, two immediate memory directories and 83 top-level session JSONL files. No private file contents or project directory names were read/exported. Claude Desktop's Store package directory also exists; its presence does not prove a complete local archive of ordinary Claude account chats or memory. No browser cookies, credentials, SQLite cache contents or undocumented account endpoints were read.

OpenAI's account export guide documents user-requested ZIP downloads, not continuous sync: https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data . Saved memories are separate from history, and the visible memory summary is not necessarily complete: https://help.openai.com/en/articles/8590148-memory-in-chatgpt . These pages do not establish a complete personal-account history/memory read API or guaranteed memory export file schema. Claude's account memory export is separately described at https://support.claude.com/en/articles/12123587-import-and-export-your-memory-from-claude .

## Source-inspected open-source shortlist

Repository metadata and pinned source were fetched on 3 October 2026; no project was installed, run against accounts, or adopted as a dependency.

| Project | License / inspected revision | Finding and fit |
| --- | --- | --- |
| [Claudescope](https://github.com/vladar107/claudescope) | MIT; `03e951709c5b97e385dec2efd5961f7c33e5e62d` | Inspected Claude Code and Codex memory connectors. Direct read-only local memory discovery is the most relevant pattern for the user's local-store suggestion. This is coding-agent coverage, not ordinary ChatGPT account coverage. |
| [Codex / ChatGPT Memory Dock](https://github.com/AnoCod/codex-chatgpt-memory-dock) | MIT; `3e926cb807827ce7f062ac4714aa877448b4651d` | Inspected `Core/MemoryService.cs`: default Codex memories plus configurable folders. ChatGPT paths in code are existence-based candidates; README explicitly describes exported files for account memory. These candidate paths are not official ChatGPT stores. Avoid its edit/delete behavior; Mind Palace sources are immutable. |
| [ChatGPT Exporter](https://github.com/pionxzh/chatgpt-exporter) | MIT; version 2.36.3; `4c8fe6ea01d58a59bc59aea9ba1421fee7d80969` | `src/api.ts` obtains an access token from `/api/auth/session`, then sends bearer-authenticated requests to ChatGPT's internal backend. Its role/branch/content types inform format research. This transport conflicts with the existing no-token/private-endpoint boundary; not adopted. |
| [ChatGPT to Markdown](https://github.com/difegam/chatgpt-to-markdown) | MIT; version 0.1.0; `db7993eee7c773c2df41a90dfc353e740d12b57c` | Offline export parser and ZIP conversion. Inspected parser and manifest: partitioned exports; Python >=3.14, whereas our worker is 3.12.10. It skips malformed entries; our sync rejects the batch before publishing content. Not installed or copied. |
| [ChatGPT Markdown Exporter](https://github.com/Nassau-1/chatgpt-markdown-exporter) | MIT; extension 1.2.2; `d34a89420a45403cab102112d8474465609a2df4` | Inspected MV3 manifest/content script: active conversation export and preparing a memory prompt without sending. Useful visible-page pattern; not all-history sync or an exact memory subscription. |
| [Claude Code Transcripts](https://github.com/simonw/claude-code-transcripts) | Apache-2.0; `316fd093aca3c9c0ad8aa70092711aee3adacc6e` | README and repository inventory inspected: local JSONL conversion, plus distinct web/publishing commands. No web, token or gist path was run. A normalization reference for local Claude work. |

The initially searched `mbr/ChatGPT-to-Markdown` URL returned 404 and is not a verified candidate. A preliminary non-terminating PowerShell loop reused the previous candidate's variables after that error; its erroneous metadata was discarded. Only subsequent successful repository requests appear above.

## Implemented export sync contract

`memory_worker.chatgpt_sync` is an independent source entry point, not the frozen UI worker, IPC method inventory, native connection or a running background monitor. It reads only explicit files beneath an opt-in source root. Configuration is exact:

```json
{
  "schema_version": 1,
  "enabled": true,
  "profile": "personal",
  "source_root": "ABSOLUTE_DEDICATED_EXPORT_DIRECTORY",
  "inbox_root": "ABSOLUTE_DEDICATED_INBOX_DIRECTORY",
  "excluded_conversation_ids": []
}
```

Source and inbox must be non-overlapping, absolute, unlinked directories. The profile is a user-chosen stable local account/workspace label; no account identity is inferred or verified. Different labels keep identical conversation IDs separate. Config is not a protection against other programs running as the same OS user.

From `sidecar`, using the existing project-local Python environment:

```powershell
python -m memory_worker.chatgpt_sync --config C:\approved\sync.json --history C:\approved\exports\export.zip
python -m memory_worker.chatgpt_sync --config C:\approved\sync.json --memory C:\approved\exports\memory.txt
```

`--history` and `--memory` can be combined. These example paths are placeholders; no live configuration or private import was created.

History accepts a root-level `conversations.json` or `conversations-<digits>.json` array, directly or inside a ZIP. Account metadata, HTML, attachments and other ZIP entries are ignored and never extracted. Ambiguous nested history paths, duplicate selected members, encrypted members, selected symlinks, unsupported compression and conflicting IDs fail. Only stored/deflated members are supported. Unknown producer variants require fixtures before claiming compatibility. This is source-informed synthetic verification, not a tested private account export.

Each included conversation retains the exact UTF-8 bytes of its JSON array item, its SHA-256 and byte count. Outer array separators/whitespace and the entire ZIP are not archived. Excluded conversations are never persisted even as part of a raw export artifact. Source references are JSON pointers relative to each retained fragment, not byte offsets. Parent graphs and all alternate branch messages are retained; active order follows `current_node`, never timestamps or array order. Absent active branch is explicitly reported. Visible user/assistant text parts are normalized; tool/system, hidden/thinking, non-final channels and unsupported content stay only in raw provenance, with count-only warnings. Attachments are not fetched. No content becomes executable instructions, approved decisions or confirmed memory.

Memory accepts only an explicitly supplied UTF-8 `.txt` or `.md` snapshot. It is separate, `user_supplied_memory_text`, `unreviewed` and `completeness:unverified`. A model's answer to a memory-export prompt is not proof of complete saved memory.

Storage layout is `<inbox>/chatgpt-sync/<hash(profile)>/{conversations/<hash(profile,conversation_id)>/<raw_sha>.json,memories/<raw_sha>.json,receipts/<receipt_sha>.json}`. Identical inputs do not rewrite files across restart; changed versions share the same session identity and preserve older versions. No mutable latest pointer or implicit timestamp selection exists. Source deletion or an older export does not erase or roll back saved copies.

The receipt lists object hashes and is written last. A consumer must validate the receipt, paths, hashes and record contracts before ingestion, and only ingest receipt-listed revisions. A interrupted batch can leave unreferenced immutable objects; retry reuses them and completes publication. External tampering is preserved and reported as conflict. Concurrent jobs serialize on an inbox lock. Consent is reread inside that lock before content publication. Pause stops the next job or a job paused during read; it does not interrupt an already publishing batch. Existing copies remain when exclusions change or sync is disabled.

Limits: 64 KiB consent file; 512 MiB input ZIP; 64 MiB selected JSON total; 100 selected ZIP members; 10,000 archive entries/conversations/nodes per conversation; 20 MiB raw conversation; 60 MiB stored revision; 256 KiB memory text; 50,000 stored filesystem entries and 512 MiB inbox quota. Decompression ratio is capped at 500. Reaching limits fails visibly; broad accounts may require a later streaming job. Same-content formatting changes may create additional revisions. No automatic pruning or source deletion is implemented. All captured content is plaintext local storage.

CLI output contains only counts/status/warning codes; errors omit source text, user paths and exception details. Windows extended paths are used consistently without registry changes. Actual macOS/POSIX publication remains unverified.

## Earlier proposed next work — superseded by D024

1. Build metadata-only native discovery for documented Claude Code/Codex stores and selection of exact read scopes; add read-only reconciliation and memory-file snapshots with synthetic fixtures. Do not treat arbitrary installed app caches as conversation stores.
2. Add native consent/pause/status and package the capture/export entry points; preserve existing assistant settings. No default enabling or token scraping.
3. Integrate validated receipts through the app's single writer into canonical provider sessions with original provenance and revision reconciliation. Do not route these records through `pasted_text`, duplicate every revision in Sessions, or infer approval.
4. Verify original-message fidelity using controlled actual-client fixtures, then indexing/retrieval. The current app does not list this inbox or answer over it.
5. Investigate ordinary ChatGPT ongoing browser capture separately. Current-page capture can cover only connected surfaces; account history and exact saved-memory coverage remain unresolved. Keep exports as a fallback rather than marking D022 complete.
