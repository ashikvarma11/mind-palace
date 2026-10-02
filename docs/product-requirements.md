# Product requirements and scope

The approved local-first desktop baseline and Workspace design implement the existing product requirements below. The user delegated safe/no-cost engineering choices. No claim that the complete release is a two-week guarantee; D/R/F refer to planned demo/release/future priorities, not implemented capabilities.

| ID | Feature and user benefit | Scope | Implemented in steps |
| --- | --- | --- | --- |
| R01 | Native installers bundle required runtimes so users do not install developer tools. | D: one tested Windows build; R: Windows and both Mac architectures | 02, 03, 23 |
| R02 | Local storage and no developer telemetry keep the developer from receiving personal content. | D/R | 04, 05, 22, 24 |
| R03 | Markdown notes remain readable and portable outside the app. | D/R | 06, 07 |
| R04 | Folders, tags, and attachments organize personal and work knowledge. | D: folders/tags; R: attachment handling | 07, 08 |
| R05 | Links and backlinks show related knowledge. | D/R | 09 |
| R06 | Templates and daily notes make journals and work logs quicker to write. | R | 17 |
| R07 | Typed properties and table views sort and filter notes. | R | 18 |
| R08 | Pasted conversations and tested exports preserve sessions from different assistants. | D: paste/normalized format; R: verified provider exports | 10 |
| R09 | Editable AI summaries propose useful memory while preserving the original evidence. | D/R | 11, 12 |
| R10 | Decision history distinguishes suggestions, confirmations, rejections, and replacements. | D/R | 12 |
| R11 | Keyword and semantic search find relevant passages with or without exact wording. | D/R | 13 |
| R12 | Memory questions produce simple-English answers with evidence links or an honest abstention. | D/R | 14 |
| R13 | Resume packages recover task state, approved decisions, attempts, unknowns, and next actions. | D/R | 15 |
| R14 | Claude/ChatGPT handoffs share selected context through copy/export and supported integrations. | D: copy/export; R: local MCP; F: optional remote connector | 15, 20, 26 |
| R15 | Multiple local repository connections relate code to conversations through Graphify. | D: one sample repo; R: multiple | 02, 16 |
| R16 | Freshness checks flag memories for review when supporting sources change. | R | 16, 19 |
| R17 | Three.js exploration and GSAP motion help inspect relationships and history. | D: bounded graph; R: polished timeline | 21 |
| R18 | Tasks and top-three priorities make recorded commitments actionable each day. | D: manual tasks; R: full daily view | 12, 17 |
| R19 | Default start-at-login, with an off switch, makes daily priorities available on startup. | R | 17 |
| R20 | Export, backup, and restore preserve the complete memory and its provenance. | D: portable vault; R: verified backup/restore UI | 05, 22 |
| R21 | A README and synthetic sample workspace explain setup, privacy, integrations, and the demo. | D/R | 24 |
| R22 | A distinctive brain/memory identity, logo, and native icon make the app recognizable. | D/R | 01, 21, 23 |
| R23 | Jev / Decision API may later improve classification or ranking after comparative evaluation. | F; excluded from all first-release dependencies | 26 |

First verified milestone: browser shell with explicit fictional sample opt-in, source/review/handoff interaction and unavailable native/AI capabilities. It does not satisfy durable storage or actual AI requirements. Continue the numbered plan for the real product; keep Windows testing first and macOS claims pending native evidence. Plain English is selected; no formal STE compliance is claimed. Free unsigned demo distribution is the engineering default; no purchases or paid service fallback.

Session summaries remain per-session records. Decisions can link across sessions and have independent audited approval states. User review of a summary is never approval of every candidate. No covert computer surveillance, browser scraping or automatic cloud sharing is part of the requirements. Jev stays deferred.
