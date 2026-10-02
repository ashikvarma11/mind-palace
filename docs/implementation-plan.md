# Personal memory application — detailed implementation plan

Plan revision: 1.1. Updated: 2 October 2026. Application: **Mind Palace**. Repository: `ashikvarma11/mind-palace` (public, MIT code). Status: implementation started; Workspace UI approved.

## Approved implementation update — 2 October 2026

- The user approved the **Workspace** UI after selecting it in the interactive review, then said to proceed with implementation.
- Mind Palace is the approved name; the supplied brain-and-palace image is the temporary logo, favicon/app-icon source, and opening artwork. Do not redraw it or invent an approved vector logo. Artwork redistribution licensing remains distinct from the MIT code license.
- G01: the user explicitly selected the proposed Angular + Tauri + bundled Python + local AI baseline, Windows tested first and macOS verified later.
- G10: public repository, authenticated owner ashikvarma11, local root D:/Projects/mind-palace, MIT code license. Publisher/bundle identity and signing remain unresolved release gates.
- Step 03A: implement and verify the approved Angular **browser shell / synthetic gateway** while Step 02 native/model probes are pending. This is a development subset, not the Step 03 desktop exit gate. Show unavailable native/AI capabilities explicitly, default to an empty workspace, and let users opt into labelled fictional samples. No browser localStorage is substituted for durable vault storage.
- UI prototype icons use a locally bundled Lucide Angular subset to match the reviewed design; Material/CDK remain the planned accessible interaction foundation. Do not use runtime CDN fonts or assets.
- Do not run an administrator installer or reconfigure system-wide build tooling without user direction. Read-only prerequisite checks can proceed.

Additional exact file responsibilities for Step 03A (recorded before creation):

| Path | One-line responsibility |
| --- | --- |
| docs/file-ledger.md | Record the exact scaffold and prototype paths before creation, with step, intent, and verification state. |
| docs/design-review.md | Record Workspace approval, logo selection, sample-only prototype, and remaining screen work. |
| docs/verification/step-03a.md | Record browser build/unit/end-to-end evidence separately from the pending native desktop gate. |
| src/app/core/workspace-store.ts | Own typed in-memory synthetic demo state, explicit sample activation, and safe review/handoff transitions; never claim durable vault storage. |
| src/app/core/workspace-store.spec.ts | Prove suggestions stay proposed until explicit action, handoffs reflect reviewed states, and demo reset is deterministic. |
| src/app/features/workspace/workspace-page.component.ts | Render route-specific shell prototype states from the typed store, with native/AI features visibly unavailable. |
| src/app/features/workspace/workspace-page.component.html | Render the approved Workspace Welcome/Today/Sessions/Decisions/Ask/Resume/Connections/Settings views and empty states. |
| src/app/features/workspace/workspace-page.component.scss | Style responsive view layouts using approved Workspace design tokens. |
| tests/e2e/shell.spec.ts | Verify explicit sample opt-in, navigation, evidence, decision/handoff transitions, route reload, and narrow-layout behavior. |
| tools/probe-runtime.py | Run actual Python SQLite/FTS5 and dependency-capability checks without claiming packaging/model success. |
| public/brand/logo-original.png | Preserve the user-supplied original artwork locally, pending a separate asset redistribution license decision. |
| public/brand/logo-preview.png | Bundle a mechanical display-size version of the approved artwork for the local prototype. |
| public/favicon.png | Use a size derivative of the same artwork as the browser favicon; do not redesign it. |
| design/brand/README.md | Record source provenance and keep artwork licensing separate from MIT application code. |

## 1. Intended result

An installable personal memory workspace that keeps notes, imported AI conversations, decisions, preferences, and tasks on the user's device. It helps the user find the original reasoning behind past work and continue an unfinished task with an accurate, editable handoff.

The distinctive workflow is: import a conversation → review what was actually agreed → find the source evidence → check related changes → prepare the next session. Its advantage must be demonstrated through measured accuracy and reduced setup. Graphs, Markdown, and AI chat are useful features, but are already available in Obsidian or its ecosystem.

This document is a plan, not working application code. Proposed paths below are a new repository contract because the inspected planning workspace contains no application source and is not a Git repository. The user specified `D:\Projects` as the parent folder for repository creation. It exists and contains unrelated projects; do not modify them or initialise Git in the parent folder. Create the application in `D:\Projects\<approved-repository-name>` at Step 00, after confirming the name and GitHub owner/visibility. If the selected child folder already exists, inspect it before adopting these paths. Reconcile existing conventions instead of creating a second application beside existing code.

The complete product is larger than a two-week demo. Steps 00–02 produce verified setup/prototypes; from Step 03 onward every implementation step must leave a runnable application with the features completed so far. Passing a step means meeting its recorded checks; no plan can guarantee perfect software without executing those checks.

## 2. Requirements and release scope

`D` = two-week demonstration target. `R` = complete first product release, after the demo. `F` = future work. The user must confirm the smaller demo scope in Step 01.

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

The familiar Obsidian subset above was chosen for usefulness, not from verified usage statistics. Its official documentation confirms [graph view](https://obsidian.md/help/plugins/graph), [backlinks](https://obsidian.md/help/plugins/backlinks), [Canvas](https://obsidian.md/help/plugins/canvas), and [Bases](https://obsidian.md/help/bases). Full Canvas, plugin/theme compatibility, Bases formula compatibility, mobile apps, sync, collaboration, OCR, audio capture, and a plugin marketplace are outside this first release. Preserve them in the backlog if later requested.

The current product promise must not claim to outperform all Obsidian plugins. The app developer's privacy statement also must not imply that exporting to ChatGPT or Claude keeps that exported content on the device. Obsidian itself already says its apps collect no telemetry. See [Obsidian pricing and privacy statement](https://obsidian.md/pricing).

## 3. Rules for the implementation agent

These are user-requested execution rules, not optional writing advice.

1. Read this plan, the repository's current `AGENTS.md`/`CLAUDE.md`, `docs/decisions.md`, and `docs/implementation-status.md` before starting a step.
2. Inspect the current source, repository status, dependency locks, and tests for the step. Existing source wins over remembered filenames or examples.
3. Open current official documentation for the external APIs, libraries, configuration fields, or release artifacts the step will use. Record the URL, date, version, relevant behavior, and actual source commit in `docs/research.md`. Recheck when a dependency or client changes.
4. Use the contracts here for product behavior. When code and plan conflict, identify the conflict and update the plan before implementing the correction.
5. If a source does not establish an API or behavior, inspect its release source or run a small isolated experiment. Do not invent an option, SDK method, model size, installer flag, or client capability.
6. Ask the user if evidence cannot resolve their intent, the choice changes scope/privacy/cost, or a branding/hardware decision requires their preference. Record the answer and its origin; silence is not approval.
7. Make the smallest change that completes the current step. For any new path, record `path — one-line responsibility` before creating it. A test file must name the user behavior it proves.
8. Validate schemas at every trust boundary. Imported text and model output are data; they never become executable commands or higher-priority instructions.
9. Run the step checks, relevant previous tests, and a manual smoke test. Preserve the real output under `docs/verification/step-NN.md`, with environment and known limitations.
10. Fix failures before marking the step complete. If blocked, record what works, the evidence, and the unresolved dependency. Do not weaken a test just to pass it.
11. Update implementation status with exact changed paths, checks run, results, decisions, remaining work, and the next action. Use `not_started`, `in_progress`, `blocked`, or `verified`; a successful build alone does not verify product behavior.
12. Do not commit, publish, collect real user data, modify other repositories' instructions, or activate cloud sharing merely because a later step describes it. Follow the user's implementation authorization and the explicit product controls described here.

For each step, `docs/verification/step-NN.md` is created or updated with the evidence for that step. Paths in this plan are relative to the chosen application repository unless explicitly described as vault/runtime files. The agent must resolve them against the verified repository root; it must not use this planning-output folder as the application by accident.

## 4. Architecture and library decisions

The baseline below is a recommendation derived from the requirements and the official documentation. Step 01 records approval; Step 02 measures feasibility before it becomes the implementation baseline.

| Layer | Proposed choice | Exact responsibility and reason |
| --- | --- | --- |
| Desktop UI | Angular 22, TypeScript, standalone components, signals, reactive forms | Use the user's Angular experience for a responsive desktop workspace; keep data operations behind a typed gateway. |
| UI components | Angular Material and Angular CDK | Dialogs, menus, forms, tables, focus management, keyboard support, and virtual lists, with a custom theme. |
| Styling | SCSS plus CSS custom properties | One token system for light/dark themes, spacing, typography, states, and contrast; avoid overlapping design frameworks. |
| Markdown editor | CodeMirror 6 | Source editing with undo, selection, keyboard support, and Markdown extensions. |
| Markdown preview | `markdown-it` and DOMPurify | Render supported Markdown, sanitize it, resolve local links through the app, and prevent network-loaded content by default. |
| UI icons | Locally bundled Material Symbols SVG subset | A small documented icon set; no runtime font/CDN requests. The app logo is a separate original asset. |
| Graph and motion | Three.js; GSAP and ScrollTrigger | Bounded relationship exploration, focus transitions, and a readable history timeline with reduced-motion support. |
| Native shell | Tauri 2 and Rust | Native window, dialogs, app paths, lifecycle, verified sidecar launch, startup setting, and installers. |
| Memory service | Frozen Python worker | One service layer for vault operations, ingestion, review, indexing, retrieval, and MCP adapters; reuse Graphify without a second backend framework. |
| Durable records | UTF-8 Markdown, raw imports, JSON/JSONL records | Portable user-owned records with stable identifiers and source evidence. |
| Search cache | Python SQLite with FTS5 and float32 embedding blobs | Rebuildable lexical search, bounded semantic search, typed indexes, and graph adjacency; one writer per vault. |
| Local AI runtime | Bundled, pinned `llama.cpp` server binary | Local embeddings and structured generation; no Ollama/Node/Python installation required for end users. |
| Model candidates | Official Qwen3 1.7B Q8_0 and smaller Qwen3 0.6B Q8_0; BGE small English embeddings | Candidate set for measured selection, not guaranteed accuracy or hardware support. |
| Repository understanding | `graphifyy` 0.9.73 baseline candidate, pinned artifact | Local code extraction behind a wrapper that controls inputs, outputs, credentials, and graph normalization. |
| Assistant tools | Official Python MCP SDK | A frozen stdio entry point for supported local clients, with limited tools and explicit write staging. |
| Development tests | Angular's verified test runner, pytest, Rust tests, Playwright browser tests | Use the actual scaffold's runner; browser tests exercise the UI with a synthetic gateway, plus separate real desktop smoke tests. |

[Angular's release page](https://angular.dev/reference/releases) lists 22 as actively supported when checked; [its compatibility table](https://angular.dev/reference/versions) determines the Node/TypeScript combination. Do not guess patch versions. Match Angular core, CLI, Material, and CDK, and commit generated lockfiles after the compatibility probe. Browser support in a browser does not automatically prove support in both Tauri webviews.

[Angular accessibility guidance](https://angular.dev/best-practices/a11y) supports Material/CDK for accessible behavior. [CodeMirror's Tab example](https://codemirror.net/examples/tab/) explains its keyboard escape behavior. [Three.js WebGL guidance](https://threejs.org/docs/pages/WebGL.html) provides capability detection; unsupported graphics must retain a usable relationship list. [ScrollTrigger](https://gsap.com/docs/v3/Plugins/ScrollTrigger/) provides scrolling interaction. The [GSAP license](https://gsap.com/community/standard-license/) permits no-charge commercial use under its terms; retain its notice and do not describe it as MIT.

No NgRx decision has been made for this app. Begin with feature services/signals and use the schema/gateway boundaries. Add a state-management library only if actual complexity warrants it, supported by a documented decision. No Next.js, React UI kit, LangChain, hosted vector database, or cloud inference service is required by this baseline.

### Process and ownership model

```text
Angular UI
  └─ typed Tauri calls/events
       └─ Rust supervisor
            ├─ frozen memory-worker --mode ui (JSONL over private stdio)
            │    ├─ durable vault files; single mutation lock; SQLite cache
            │    ├─ bounded Graphify child job using selected code snapshots
            │    └─ HTTP to authenticated loopback llama-server
            └─ bundled llama-server (started only when AI work needs it)

Local assistant
  └─ frozen memory-worker --mode mcp (standard MCP stdio)
       ├─ read-only cache/record access for retrieval and context
       └─ stage save_session into the vault inbox for app review
```

The memory worker owns storage. The UI cannot submit arbitrary filesystem or shell operations. Rust owns the native process lifecycle and limits commands to the bundled executables. The app keeps running when a model is unavailable: notes, manual review, tasks, keyword search, and source viewing still work.

The MCP process does not become a competing database writer or silently start another large model. Its first-release retrieval uses stored lexical/graph indexes, with a capability field that reports semantic generation unavailable when the desktop service is not providing it. If the app is closed, read tools use the last verified index and report its age; `save_session` only creates an inbox request. The app imports and indexes it when opened. Never advertise this as live automatic capture.

### Dependency and packaging policy

[Tauri sidecars](https://v2.tauri.app/develop/sidecar/) support bundled executables with target-specific names. Use a PyInstaller `onedir` worker and include its support directory as Tauri resources; prove the resulting layout on each OS before using it throughout the app. [PyInstaller](https://github.com/pyinstaller/pyinstaller) includes Python but requires platform builds. No `pip`, `uv`, compiler, or internet download runs during a user's installation.

Use CPU-compatible Windows binaries as the minimum baseline and test macOS native builds; GPU acceleration is an optimization after a tested CPU path. Choose CPU instruction requirements from measured target hardware. Record dependent DLLs/dylibs, signed-bundle placement, versions, checksums, licenses, disk size, and RAM measurements. Do not enable the inference server's agent/shell tools.

Bundle models with the full installer to meet the automatic-dependency requirement. The [official Qwen 1.7B GGUF file list](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/tree/main) reports a 1.83 GB Q8_0 asset; [the 0.6B GGUF list](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/tree/main) reports 639 MB. These are model-file sizes, not installer/RAM promises. The [ggml embedding conversion](https://huggingface.co/ggml-org/bge-small-en-v1.5-Q8_0-GGUF) derives from [BAAI BGE small](https://huggingface.co/BAAI/bge-small-en-v1.5); verify the model card's pooling, query instruction, vector dimension, and license before locking it. Select the smallest candidate that passes the evaluation gate. If none passes, ask the user about a larger local model or a reduced demo; do not silently enable paid/cloud inference.

Windows packages use NSIS and handle WebView2 automatically. The [Windows installer guide](https://v2.tauri.app/distribute/windows-installer/) documents `offlineInstaller`; include it for the full offline package and test on a clean machine with no WebView2 runtime. Mac packages use `.dmg` with separate architecture builds as described in [Tauri DMG distribution](https://v2.tauri.app/distribute/dmg/).

### Graphify source finding

On 2 October 2026, [PyPI metadata](https://pypi.org/pypi/graphifyy/json) and the [current `v8` source manifest](https://github.com/Graphify-Labs/graphify/blob/v8/pyproject.toml) report 0.9.73 and Apache-2.0. Its old `main` manifest reports 0.1.14 and different dependencies. Resolve the release to a commit and package hash before implementation. Keep all upstream license/NOTICE files.

The [official README](https://github.com/Graphify-Labs/graphify) describes local code extraction, inferred graph relations, provider auto-detection, and optional query logging. Disable query logging with the verified environment setting, remove cloud credentials from the job environment, and use only the inspected local code path. Do not call `graphify install`, which registers assistant configuration; map code through the app's adapter. Exact invocation and export schema must come from the pinned release's help/source and Step 02 experiment.

## 5. Decisions requiring evidence or user input

Routine file layout, identifiers, queue limits, and UI defaults below are proposed engineering choices, explicitly recorded here. These may be refined with tests and a decision record. The following user choices cannot be settled by guessing.

| Gate | Needed answer/evidence | Can proceed before resolved? |
| --- | --- | --- |
| G01 | Approve the baseline stack and smaller demo scope. | Complete research and prototypes; defer full product implementation. |
| G02 | Choose the public brain/memory/studious name, publisher, and stable bundle identifier. | Use neutral internal names; defer public branding and release identity. |
| G03 | Minimum user hardware, OS versions, and availability of Mac test machines. | Run local measurements; do not claim untested targets. |
| G04 | Verify Graphify artifact, local invocation, graph schema, and packaging on each target. | Build notes/import foundations; defer repository feature if probe fails. |
| G05 | Select a local model using the benchmark, RAM, speed, disk, and license results. | Implement manual memory and keyword search. |
| G06 | Confirm simple English is sufficient, or request formal ASD-STE100 compliance. | Default to plain English; formal compliance needs access to the standard and validation. |
| G07 | Choose free demo distribution with signing prompts or funded public signing/notarization. | Build local/demo artifacts; defer claims of frictionless public distribution. |
| G08 | Decide whether later direct ChatGPT/Claude cloud connectors are wanted despite data sharing. | Copy/export and supported local-client tools meet the initial handoff scope. |
| G09 | Supply anonymized real export samples and confirm supported conversation formats. | Pasted text and the app's normalized schema work first. |
| G10 | Confirm repository name, GitHub owner/account, public/private visibility, and repository license before creation under `D:\Projects`. | Finish this plan; do not invent a remote identity or publish private session material. |

The likely recalled standard is [ASD-STE100 Simplified Technical English](https://asd-ste100.org/about_STE.html). This is an inference from the user's wording. Default to short sentences, common words, active voice, and brief explanations of technical terms. Preserve code, identifiers, quotes, and required terminology exactly. Do not put “STE100 compliant” in the app or README without a validated compliance process.

## 6. Durable vault format

All runtime paths below are inside a user-selected vault. `vault_id` is a random UUID; names can change without changing identities. The hidden directory uses the neutral `.memory` name so a later product rename does not require migrating every vault.

```text
<vault>/
  index.md                          # owned index section points to scopes and entry points
  notes/<optional-folders>/<note-id>.md # canonical Markdown; folders optional, IDs stable
  scopes/<scope-id>.json             # personal/project/topic scopes and their stable identities
  projects/<scope-id>/index.md       # owned section for a project; project association optional
  sessions/<session-id>.md           # editable canonical session summary, linked to raw evidence
  records/<record-id>.json           # canonical decisions/tasks/preferences/attempts/questions
  events/<record-id>.jsonl           # validated append-only revisions and review transitions
  daily/YYYY-MM-DD.md                # local-calendar daily note, created only when opened
  templates/<template-id>.md         # user-editable safe templates
  views/<view-id>.json               # versioned saved table filter/sort/property settings
  sources/<source-id>/original.*     # immutable copy of an explicitly imported source
  sources/<source-id>/source.json    # import provenance and original/derived artifact hashes
  sources/<source-id>/messages.jsonl # normalized messages with source spans, when applicable
  sources/<source-id>/transcript.txt # immutable normalized text with stable citation byte spans
  attachments/<attachment-id>/original.* # explicitly copied file with a validated extension
  attachments/<attachment-id>/attachment.json # canonical display/MIME/hash/size metadata
  properties/<property-id>.json      # canonical typed property definitions
  handoffs/<handoff-id>.md           # explicitly saved editable context package
  handoffs/<handoff-id>.json         # canonical structured state/budget/evidence metadata
  .memory/vault.json                 # schema version, stable ID, format settings; no secrets
  .memory/settings.json              # vault preferences; no machine-specific repository roots
  .memory/cache/index.sqlite         # rebuildable FTS/records/links/graph/embedding indexes
  .memory/cache/graphs/<repo-id>/     # normalized graphs plus version/hash manifests
  .memory/inbox/<request-id>.json     # staged MCP imports, processed once after review
  .memory/journal/<operation-id>/    # durable transaction/recovery staging
  .memory/trash/<operation-id>/      # recoverable user-initiated deletion
  .memory/locks/write.lock           # OS-held exclusive mutation lock; not stale-file detection
```

User-editable note/session Markdown is authoritative for its text. Structured records and their revision events are authoritative for decision/task state. SQLite, embeddings, graphs, global/project generated index sections, and display projections are caches. A backup must contain the authoritative files, not only Markdown summaries or SQLite.

Store machine-local vault paths, repository roots, app settings, and selected bundle assets in the OS application-data location, resolved through native APIs. Models are immutable packaged resources; an optional future downloaded pack belongs in app data. Never modify the install directory to store user memory. A changed display name must not change the release bundle ID.

Use UTF-8, LF for generated text, RFC 3339 UTC timestamps, explicit local dates/timezones where needed, and relative `/` paths in portable records. Keep IDs as UUID strings generated by the application, not the LLM. Write whole files through a temporary sibling, flush, and atomic replacement. Serialise every mutation through a cross-process OS file lock. A durable journal stores intent, affected paths, old/new hashes, and staged revisions; startup completes or reports an interrupted operation before indexing. SQLite is updated after canonical files commit; a failure marks affected cache entries dirty for rebuild.

Do not overwrite a file when its expected hash changed. Preserve both versions and ask for conflict resolution. Reject traversal, device paths, reserved filenames, and symlinks that escape selected roots. Handle Windows case collisions and macOS Unicode/case behavior before rename. Do not infer that an existing lock pathname means a process is alive.

### Record contracts

All JSON contracts use `schema_version: 1`, disallow unexpected fields at external boundaries, and use discriminated `kind` fields. Exact JSON Schema definitions are implemented in Step 04. Optional facts are `null` or omitted as specified in that schema; unknown dates/speakers/owners are never invented.

| Contract | Required data and invariants |
| --- | --- |
| Source | `id`, `kind`, `source_tool`, `imported_at`, `original_path`, `sha256`, `parse_status`, optional recorded date/scope; original bytes never rewritten. |
| Message | `id`, `source_id`, `ordinal`, `role`, `text`, optional timestamp/branch parent, `source_span`; valid roles include `unknown`; preserve branches rather than silently combining them. |
| EvidenceRef | `source_id`, original source hash, `artifact_relpath`, artifact hash, message/block ID, exact span offsets, excerpt hash; offsets use UTF-8 bytes in the named immutable artifact. Derived transcripts retain pointers back to the original export fields. |
| Scope | Stable ID, kind personal/project/topic, title, optional parent, active/archive state; repository membership is optional. |
| Note/session | Frontmatter: version, ID, type, title, created/updated times, scope IDs, tags, source IDs; session summary text remains editable and carries a review status independently of any decision. |
| Memory record | `id`, `kind`, `scope_ids`, title/body, `evidence_refs`, `review_status`, created/updated times, revision; kinds are decision/task/preference/attempt/question; statements are source-grounded or explicitly user-entered. |
| Decision | `decision_state`: proposed/confirmed/rejected/superseded/unclear; rationale/alternatives may be empty; confirmation basis and supersession event IDs are explicit. Reviewing a summary does not confirm a decision. |
| Task | `status`: suggested/open/in_progress/blocked/done/cancelled; priority, due date/timezone, owner, related scope, evidence; generated tasks remain suggested until accepted. |
| Property/view | Stable property ID, safe field key/type, allowed values and validation; saved view ID, scope, columns, bounded filters/sorts; definitions live in `properties/` and views in `views/`. |
| Preference | Topic, value, applicable scopes, optional effective interval; a later preference does not silently delete history or overwrite another scope. |
| Attempt | Action, outcome: unknown/failed/succeeded/partial, recorded reason, evidence, optional linked task; the model cannot infer failure from mere absence of a success message. |
| Question | Open/resolved state, evidence and optional resolution reference; resolution requires evidence or user input. |
| Review event | Unique event/operation ID, record ID, expected revision, actor basis, event type, previous/new value, evidence, time; transitions are idempotent and audited. |
| Repo ref | Repo ID, relative path, optional symbol identity, observed commit, file hash, dirty-content indicator, extraction version; missing Git is allowed for a local folder. |
| Graph relation | From/to IDs, relation type, origin, evidence, confidence category, observed source revision; inferred/extracted/human-confirmed are distinct. |
| SearchHit | Record/source/chunk IDs, exact span, excerpt, lexical/semantic ranks, stale status, scope; numeric rank is not a probability of truth. |
| Answer | Status answered/partial/insufficient_evidence/ambiguous, ordered claims with evidence IDs, uncertainty, freshness notices; every factual memory claim requires supported evidence. |
| Handoff | Task/scope identity, state, confirmed decisions, proposed choices, recorded attempts, completed work, open questions, next actions, evidence and freshness, generated time, budget/model tokenizer ID. |

LLM extraction generates candidate fields with source references only. It never generates IDs, writes files, confirms decisions, marks tasks done, or executes code. A source's speaker label is not proof of approval. Explicit imported user approval is shown for review; the user can confirm it or mark it ambiguous. Later chronological text alone does not supersede a previous decision.

### Index design

SQLite cache tables: `documents`, `sources`, `messages`, `records`, `record_revisions`, `evidence_refs`, `scopes`, `scope_memberships`, `tasks`, `links`, `chunks`, `embeddings`, `repositories`, `repo_files`, `graph_nodes`, `graph_edges`, `freshness_checks`, and `index_jobs`. `chunks_fts` is an FTS5 table with chunk ID, title, and body. Use foreign keys, parameterized statements, schema migrations, appropriate indexes, and WAL after validating the environment.

Cache migrations live in `sidecar/memory_worker/migrations/`. Rebuilding from durable records must reproduce states and citations. Store embedding model/revision, tokenizer/pooling version, dimension, normalisation, and chunk hash. Never compare incompatible embeddings. For the initial bounded dataset, compute exact cosine ranking over cached vectors; benchmark before adding a vector extension or approximate index. [SQLite FTS5](https://sqlite.org/fts5.html) documents lexical indexing and BM25.

### IPC contract

UI-worker private stdio requests use `{protocol_version:1,id,method,params}`; responses use `{protocol_version:1,id,result}` or `{protocol_version:1,id,error:{code,message,retryable}}`; events use `{protocol_version:1,event,job_id,payload}`. One UTF-8 JSON object per line, maximum frame 1 MiB, bounded queues, matching request IDs, and no secret/content logging. Use structured errors such as `VALIDATION_ERROR`, `CONFLICT`, `BUSY`, `MODEL_UNAVAILABLE`, `SOURCE_CHANGED`, `CANCELLED`, and `UNSUPPORTED_FORMAT`.

Register allowed method names centrally. Long work returns a job ID with progress/cancel events. Bulk paste/import content is a size-checked approved input reference or bounded chunks, not an unlimited IPC line. Rust and the worker check payload shape and method permission; frontend checks typed responses. Parse partial stdout buffers correctly, keep diagnostics on stderr, and terminate child trees on app exit. MCP stdio is a separate mode using the standard SDK protocol; do not mix it with the private JSONL protocol.

## 7. Verification targets

These are proposed release thresholds, not existing measurements. Step 02 can change hardware-dependent performance budgets with recorded evidence; accuracy thresholds cannot be weakened silently.

| Area | Required evidence |
| --- | --- |
| Evidence integrity | Every displayed citation resolves to the exact preserved source span and matches its hash. |
| Approval precision | Zero suggestions promoted to confirmed decisions in the held-out ambiguous-approval cases; human review controls pass all state-transition tests. |
| Retrieval | At least 90% evidence recall@5 over 30 labelled demo questions, including changed decisions and unanswered questions; report denominator and failures. |
| Answering | At least 90% correct supported answers on answerable cases; every memory claim cited; all critical no-evidence/contradictory cases abstain or clearly report conflict. Human grading is required. |
| Handoff | All relevant confirmed decisions and open questions in at least 90% of labelled cases; zero omitted critical supersessions in the critical-case suite. |
| Privacy | No developer analytics or content upload; no outbound requests during fully offline core workflows; app-controlled network attempts traced separately from OS runtime traffic. |
| Durability | Simulated interruption at every journal stage leaves recoverable authoritative data; rebuild/restore reproduce approved states and original evidence. |
| Installer | Each advertised target tested with no Python/Node/Rust/Ollama; imports, code mapping, model inference, restart and uninstall preservation demonstrated. |
| UI | All primary workflows keyboard accessible; readable at 200% zoom; light/dark/high contrast/reduced motion; graph has equivalent list navigation. |
| Performance | Baseline target: 10,000 chunks/500 notes; keyword p95 <=300 ms, hybrid p95 <=2 s after warmup, usable shell <=3 s on recorded reference hardware. Record model time separately. |

Run deterministic tests without an LLM for storage, approvals, provenance, schema rejection, and retrieval fixtures. Run the local model on a separate held-out benchmark; do not replace it with a mocked response and call the AI feature verified. A replay used in a portfolio demo must be visibly labelled as a saved run.

## 8. Step-by-step implementation

The step order below is intentional. Each step includes prerequisites, exact proposed changes, behavior, and an exit gate. File descriptions specify purpose and content in one line; they do not pretend to be finished source code. Unverified third-party syntax is resolved in the associated experiment and recorded before use.

### Step 00 — Create the GitHub repository under the user's chosen folder

Prerequisite: implementation has started; G10 is answered. The current planning task does not create the repository now.

1. Resolve `D:\Projects\<approved-repository-name>` to an absolute path and verify it is a direct, uniquely named child of `D:\Projects`. Check for existing files and parent/repository instructions. Never initialise Git at `D:\Projects` itself, reuse an unrelated project, or delete a folder to make room.
2. Check installed Git/GitHub tooling, authenticated account, and the approved remote's existence with read-only commands. If authentication is missing, ask the user to sign in through the supported flow; do not request that a token be pasted into a document or log.
3. Create the empty child directory and initialise the local repository with a recorded default branch. Create the GitHub repository with the approved owner/name/visibility, attach `origin`, and verify both remote URL and local root. Use the current [GitHub CLI repository-creation documentation](https://cli.github.com/manual/gh_repo_create), not an invented command. Its `--source` and `--remote` options can connect an existing local repository; choose exactly the confirmed visibility flag.
4. Add the initial files below, then proceed to Step 01. Before an initial commit/push, review the exact staged paths and content for secrets, personal imports, attached transcripts, model binaries, and build outputs. Commit/push only as part of the authorised repository-creation/implementation workflow; do not stage the entire `D:\Projects` tree. No public release or package publication is implied by repository creation.

| File | One-line creation/change |
| --- | --- |
| `.gitignore` | Exclude personal vaults/imports, credentials, environments, generated builds, and downloaded runtime/model binaries before the first commit. |
| `README.md` | Add the approved project name, an honest planning-stage description, and a link to the implementation plan; expand in Step 24. |
| `docs/repository-setup.md` | Record the verified local root, owner/name, visibility, default branch, remote URL, license choice, and setup checks without tokens. |
| `LICENSE` | Add only the user-approved application license; dependency/model licenses remain separately documented. |

Exit gate: the application has its own verified local repository under `D:\Projects`, the approved GitHub remote exists, and unrelated projects remain unchanged. Record whether the initial documentation was pushed; do not claim it was pushed from remote creation alone.

### Step 01 — Confirm the contract and record implementation choices

Prerequisite: read this plan and the recovered session context; inspect the repository selected by the user.

1. Inventory source, instructions, Git status, build commands, tests, and machines available for testing. If the repository is empty, record that explicitly.
2. Confirm G01–G03 and G06–G07 with the user. Present the proposed stack and demo scope together, with the actual model/installer size and signing tradeoffs from Step 02 when available. Research/prototypes can proceed while answers are pending.
3. Keep the internal name neutral until G02 is answered. Search official registries/repositories for obvious name collisions before recommending a public name; do not claim trademark clearance from a web search.
4. Copy the reviewed plan/context into repository documentation and create the status/decision records. Do not record earlier assistant suggestions as approved decisions.

| File | One-line creation/change |
| --- | --- |
| `AGENTS.md` | Add plan-first, code-first, official-docs-first, uncertainty, step-check, and handoff rules; preserve any existing instructions. |
| `CLAUDE.md` | Add equivalent repository guidance with links to the plan/status; preserve existing text. |
| `docs/implementation-plan.md` | Store the reviewed version of this plan and its revision history. |
| `docs/product-requirements.md` | Store R01–R23, accepted release scope, excluded features, and source-of-approval references. |
| `docs/decisions.md` | Store decision ID, proposal, evidence, status, user approval when required, alternatives, and consequences. |
| `docs/implementation-status.md` | Store the step ledger, actual changed files, verification links, blockers, and next action. |
| `docs/research.md` | Store dated primary-source findings, package versions/commits, uncertainties, and tested API signatures. |
| `docs/session-context.md` | Preserve recovered requirements and distinguish approved facts from proposals. |
| `docs/branding-brief.md` | Store the naming criteria and a logo brief: recognizable memory/brain symbol with a studious character. |

Exit gate: the agent can name the repository root, approved scope, pending gates, and next step without contradiction. Full implementation starts only after G01; unresolved branding does not block foundations.

### Step 02 — Prove bundled runtimes, Graphify, and candidate models early

Prerequisite: research/prototype authorization within the chosen repository; synthetic data only.

1. Inspect current versions and compatibility; capture the exact `graphifyy` release source/artifact and its CLI help. Baseline 0.9.73 is rechecked, not automatically replaced with “latest.”
2. Build a tiny Python wrapper including SQLite FTS5, JSON Schema validation, file locking, the MCP SDK, and Graphify. Freeze it as `onedir` on each available target; record native-library collection and missing-platform results.
3. Map a tiny TypeScript fixture using the pinned code-only extraction path. Determine the exact callable/arguments and graph fields from source. The wrapper writes outputs only into its staging folder and removes provider credentials from its environment.
4. Run the exact bundled `llama-server` binary against local model files; test model loading, authenticated loopback requests, embeddings, structured JSON, timeouts, cancellation, CPU fallback, and no external requests.
5. Compare both Qwen candidates on at least ten labelled extraction/recall cases; record artifact size, peak memory, cold/warm latency, and errors. Use that result to narrow candidates; keep a separate held-out release set for Step 25.
6. Check Windows full-package size and hosted artifact limits. If the chosen release host cannot accept the full installer, record a supported alternative delivery method before promising a single download.

| File | One-line creation/change |
| --- | --- |
| `tools/probe-runtime.py` | Exercise bundled SQLite/validation/locking/MCP imports and report platform/runtime capabilities without personal content. |
| `tools/probe-graphify.py` | Run the inspected pinned local code path over a synthetic fixture and validate output/source locations. |
| `tools/probe-models.py` | Benchmark local model loading, embeddings, JSON generation, cancellation, and resource use. |
| `tools/fixtures/probe-repo/package.json` | Define a minimal synthetic TypeScript repository identity with no install scripts. |
| `tools/fixtures/probe-repo/src/auth.ts` | Define one service with known imports/calls for graph extraction checks. |
| `tools/fixtures/probe-repo/src/store.ts` | Define a related store symbol so cross-file graph evidence has a known answer. |
| `tools/fixtures/probe-cases.jsonl` | Store ten labelled approval/ambiguity/recall cases with exact source evidence. |
| `config/dependency-manifest.json` | Store selected package/runtime versions, source commits, download origins, artifact hashes, licenses, and targets. |
| `config/models.json` | Store model candidates, exact files/revisions/hashes, prompt/pooling settings, budgets, and selected status. |
| `docs/feasibility.md` | Record measured packaging/model/Graphify outcomes per target and G03–G05 resolutions. |

Exit gate: at least one native frozen worker and local-model/Graphify vertical path work on the demo target. A failed Mac probe stays explicitly pending; do not extrapolate Windows success. If the baseline cannot work, revise it with evidence before building the rest.

### Step 03 — Create a runnable Angular/Tauri shell and baseline checks

Prerequisite: G01 and a feasible demo target. Read current scaffold documentation and use locked compatible tooling.

1. Generate an Angular client-only project and initialise Tauri 2 around its built output. Inspect the generated Angular output directory before setting `frontendDist`; no SSR/server runtime is shipped.
2. Normalise scaffold filenames to the paths below and record any generator differences. Use browser-compatible routing and verify a reload on every route in the actual desktop shell.
3. Add the script contract below. The actual test command uses the runner produced by the locked Angular version; do not copy an obsolete Karma/Vitest command from memory.
4. Render a vault-open screen, empty workspace, disabled not-yet-built actions, and visible loading/error states. Add native single-instance behavior.

| File | One-line creation/change |
| --- | --- |
| `package.json` | Define exact dependency pins and the common development/build/check scripts. |
| `package-lock.json` | Commit the tested npm dependency resolution. |
| `.npmrc` | Enable exact saved versions and disable project-owned analytics/funding prompts as appropriate. |
| `angular.json` | Define the client-only build, assets, SCSS, budgets, and verified output directory. |
| `tsconfig.json` | Enable strict TypeScript and the verified Angular compiler options. |
| `tsconfig.app.json` | Define application compilation inputs without server-only modules. |
| `tsconfig.spec.json` | Define the selected frontend test environment. |
| `src/main.ts` | Bootstrap the standalone Angular application. |
| `src/index.html` | Define document metadata, root element, and local assets. |
| `src/styles.scss` | Load the initial theme and global accessibility styles. |
| `src/app/app.component.ts` | Host the application shell and route outlet. |
| `src/app/app.component.html` | Render navigation, work area, source panel, and status area. |
| `src/app/app.component.scss` | Define the initial resizable desktop layout and narrow-window behavior. |
| `src/app/app.config.ts` | Register router, providers, gateway, and required Angular infrastructure. |
| `src/app/app.routes.ts` | Define vault/home/notes/search/review/resume/settings routes with unavailable features gated. |
| `src-tauri/Cargo.toml` | Pin Tauri and only the native plugins used by the shell. |
| `src-tauri/Cargo.lock` | Commit the tested Rust dependency resolution. |
| `src-tauri/build.rs` | Run the standard Tauri build integration. |
| `src-tauri/src/main.rs` | Launch the desktop library entry point. |
| `src-tauri/src/lib.rs` | Initialise the window, state, plugin set, and command registration. |
| `src-tauri/tauri.conf.json` | Set verified dev/build paths and neutral development identity. |
| `src-tauri/capabilities/default.json` | Grant only the native capabilities actually required by the main window. |
| `.gitignore` | Exclude local vaults, model/runtime artifacts, scratch builds, environments, and private data. |
| `tools/check.mjs` | Run the available schema/frontend/Python/Rust checks in a predictable order and return failure status. |

Script contract: `dev:web`, `dev:desktop`, `build:web`, `build:desktop`, `test:web`, `test:worker`, `test:rust`, `test:e2e`, `generate:contracts`, `check`, `package:sidecar`, `package:desktop`, and `eval:memory`. Introduce scripts when their real implementation exists; an unavailable stage must be clearly skipped/pending, never reported as passed. Configure `tauri` as the local CLI script for documentation examples.

Exit gate: the browser shell and desktop shell launch, render, reload a route, and exit cleanly; build/check pass for the implemented foundations; there are no console/runtime errors.

### Step 04 — Establish schemas, typed transport, jobs, and error behavior

Prerequisite: runnable shell and frozen-worker prototype.

1. Implement the record and IPC schemas from Section 6 as the shared source of truth. Generate frontend types from schemas and fail checks if generated files differ.
2. Build the Python package and route registry. Validate incoming requests and outgoing responses; stdout contains protocol frames only.
3. Build Rust supervision with request correlation, frame limits, partial-buffer handling, timeouts, bounded jobs, cancellation, and process cleanup. Never accept executable names from the UI.
4. Add a typed frontend gateway and synthetic browser gateway. Mock mode is explicit and cannot be packaged as the real desktop data layer.

| File | One-line creation/change |
| --- | --- |
| `schemas/vault.schema.json` | Define vault configuration and format-version requirements. |
| `schemas/source.schema.json` | Define import provenance, artifact hashes, normalized messages, and EvidenceRef definitions. |
| `schemas/note.schema.json` | Define Markdown frontmatter for notes/session summaries. |
| `schemas/scope.schema.json` | Define personal/project/topic scopes and their relationships. |
| `schemas/memory-record.schema.json` | Define decision/task/preference/attempt/question variants and revision fields. |
| `schemas/review-event.schema.json` | Define auditable expected-revision transitions and idempotency keys. |
| `schemas/graph.schema.json` | Define normalized nodes/edges, provenance, and code source refs. |
| `schemas/search.schema.json` | Define queries, filters, hits, ranks, and index-freshness fields. |
| `schemas/answer.schema.json` | Define answer statuses, supported claims, and evidence references. |
| `schemas/handoff.schema.json` | Define editable context-package sections, budgets, and evidence. |
| `schemas/ipc.schema.json` | Define request/response/error/progress/cancel frame variants. |
| `schemas/settings.schema.json` | Define app/vault settings and allowed default values without secrets. |
| `tools/generate-contracts.mjs` | Generate TypeScript contracts from the locked JSON schemas. |
| `src/app/core/contracts.generated.ts` | Store generated contract types; prohibit manual edits. |
| `src/app/core/memory-gateway.ts` | Define the frontend service interface for all memory operations. |
| `src/app/core/tauri-memory-gateway.ts` | Map typed calls and job events onto verified Tauri commands. |
| `src/app/core/demo-memory-gateway.ts` | Supply labelled synthetic data for browser tests/demos. |
| `src/app/core/job-store.ts` | Track progress, cancellation, errors, and retry actions for active jobs. |
| `sidecar/pyproject.toml` | Pin worker dependencies and developer tools compatible with the packaging probe. |
| `sidecar/uv.lock` | Lock the Python environment and artifact resolution. |
| `sidecar/memory_worker/__init__.py` | Define worker package/version metadata. |
| `sidecar/memory_worker/__main__.py` | Select the private UI protocol, MCP mode, or diagnostic mode. |
| `sidecar/memory_worker/protocol.py` | Read/write bounded JSONL frames and track requests/jobs/cancellation. |
| `sidecar/memory_worker/contracts.py` | Validate canonical/external objects against bundled schemas. |
| `sidecar/memory_worker/service.py` | Register allowed methods and apply common validation/error handling. |
| `src-tauri/src/worker.rs` | Supervise the allowed worker process and correlate private requests/events. |
| `src-tauri/src/commands.rs` | Expose validated native app methods without generic filesystem/shell access. |
| `sidecar/tests/test_protocol.py` | Verify malformed/oversized/partial frames, concurrency, cancellation, and error correlation. |
| `src-tauri/tests/worker_protocol.rs` | Verify native transport buffering, timeout, and child-process cleanup behavior. |

Exit gate: a real UI→Rust→Python→UI health request and cancellable synthetic job work; invalid frames fail safely; shutdown leaves no owned child processes.

### Step 05 — Implement durable vault creation, writes, and crash recovery

Prerequisite: contracts/transport verified; temporary synthetic vaults only for development tests.

1. Offer native create/open dialogs. Validate vault format and refuse unknown future versions without altering files. Create missing app-managed directories only inside the selected vault.
2. Implement OS file locks, atomic writes, expected-hash conflicts, transaction journals, and startup recovery. Do not require Git inside a vault.
3. Store canonical records before refreshing derived caches; journal mutations across multiple files. Confirm a successfully recovered mutation is not duplicated.
4. Generate a small owned section in the global/project index, retaining user's other content. An index links to bounded entry points rather than embedding every session.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/paths.py` | Resolve safe vault/app-data paths and reject out-of-root/case/reserved-name collisions. |
| `sidecar/memory_worker/locking.py` | Hold a cross-process OS mutation lock with clear busy/timeout behavior. |
| `sidecar/memory_worker/atomic_io.py` | Write/flush/replace files safely with expected hashes. |
| `sidecar/memory_worker/journal.py` | Stage multi-file mutations and recover interrupted operations idempotently. |
| `sidecar/memory_worker/vault.py` | Create/open/validate vaults and expose canonical record operations. |
| `sidecar/memory_worker/index_markdown.py` | Update only owned index sections and preserve user-written surrounding text. |
| `src-tauri/src/paths.rs` | Resolve native resource/app-data locations and selected-vault handles. |
| `src/app/features/vault/vault-page.component.ts` | Drive create/open/recovery and display actionable format/conflict errors. |
| `src/app/features/vault/vault-page.component.html` | Render vault selection, recovery state, and safe retry actions. |
| `sidecar/tests/test_vault.py` | Verify path limits, unknown formats, locking, expected-hash conflicts, and portable records. |
| `sidecar/tests/test_recovery.py` | Interrupt each journal phase and verify no loss, duplicate revision, or silent overwrite. |

Exit gate: create a vault, write a canonical record, interrupt the worker, recover it, reopen it, and inspect portable files in a normal editor. All conflict/recovery tests pass.

### Step 06 — Build the rebuildable SQLite index

Prerequisite: durable vault and recovery gate.

1. Implement schema migrations and verify FTS5 at runtime. Use one UI worker writer and read-only MCP connections; no uncoordinated canonical writes.
2. Build caches from durable notes/records/events/sources. Track indexed hashes, revisions, and schema/model identities.
3. Add incremental jobs, complete rebuild, and progress. Watcher hints trigger reconciliation; a full startup rescan catches missed filesystem events.
4. On cache damage, preserve canonical data and rebuild. Never delete an authoritative vault because its cache cannot be opened.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/database.py` | Open configured SQLite connections, migrate, transact, and enforce read-only mode. |
| `sidecar/memory_worker/migrations/001_initial.sql` | Create the Section 6 index tables, FTS5, keys, and lookup indexes. |
| `sidecar/memory_worker/indexer.py` | Reconcile canonical files/events into cache rows using hashes and revisions. |
| `sidecar/memory_worker/watcher.py` | Coalesce selected-vault filesystem changes and request reconciliation without following escaped symlinks. |
| `sidecar/memory_worker/rebuild.py` | Recreate caches from authoritative records with progress and cancellation. |
| `src/app/features/settings/index-status.component.ts` | Show index age, rebuild progress, errors, and the rebuild action. |
| `src/app/features/settings/index-status.component.html` | Render the index-health view and explain recoverable errors. |
| `sidecar/tests/test_index_rebuild.py` | Prove fresh/rebuilt caches preserve reviewed states, search text, citations, and deletions. |

Exit gate: remove only a test vault's cache, rebuild it, and obtain the same canonical record states/search results; edit a note externally and verify reconciliation without app restart.

### Step 07 — Add Markdown notes, folders, tags, and safe preview

Prerequisite: durable storage/index; verify CodeMirror/Markdown renderer APIs and licenses.

1. Add create/open/edit/save/rename/move/trash/restore note actions. Autosave uses a proposed 750 ms debounce and expected revision/hash; crash/conflict handling preserves edits.
2. Create a CodeMirror wrapper with correct Angular lifecycle cleanup, selection/undo behavior, explicit save state, and accessible keyboard escape.
3. Render preview through sanitization with raw HTML disabled initially. Before attachment support exists, show an unavailable-attachment placeholder; enable the allowlisted native resource handler in Step 08. Scripts, remote embeds/images, and unsafe protocols do not load automatically.
4. Implement real subfolders inside `notes/` plus tag navigation over metadata. Folder moves change the document path, never its stable ID; update derived path/link indexes. Display ambiguous titles as separate IDs; a rename is not an identity change.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/notes.py` | Implement revision-checked note CRUD, rename/move, and recoverable trash. |
| `sidecar/memory_worker/markdown_metadata.py` | Parse/update safe frontmatter while preserving note body and unrecognised user properties. |
| `src/app/features/notes/notes-page.component.ts` | Coordinate active note, editor, preview, save state, and conflicts. |
| `src/app/features/notes/notes-page.component.html` | Render note tabs, editing/preview, metadata, and explicit save errors. |
| `src/app/features/notes/notes-page.component.scss` | Style reading width, editor, source panel, and small-window layout. |
| `src/app/shared/markdown-editor.component.ts` | Wrap CodeMirror setup, updates, commands, and cleanup. |
| `src/app/shared/markdown-preview.component.ts` | Render sanitized Markdown and delegate allowed link/attachment actions. |
| `src/app/shared/navigation-tree.component.ts` | Provide keyboard-accessible folder/tag navigation with virtualisation when needed. |
| `src/app/shared/navigation-tree.component.html` | Render the navigable note tree with clear selection and expand/collapse controls. |
| `sidecar/tests/test_notes.py` | Verify autosave conflicts, identity-preserving rename/move, metadata, and trash/restore. |
| `tests/e2e/notes.spec.ts` | Verify note writing, reload persistence, keyboard navigation, and blocked malicious preview content. |

Exit gate: write a note, rename/move/tag it, restart, and read the same content/identity; external-edit conflicts remain recoverable; unsafe preview content cannot execute or trigger an automatic network request.

### Step 08 — Add explicitly selected attachments and documents

Prerequisite: note editor and selected-path/resource handling.

1. Copy user-selected attachments to stable ID directories, storing the copied bytes as `original.<validated-extension>` and metadata as `attachment.json`; this prevents a JSON attachment from colliding with its own metadata. Retain original filename/MIME/size/hash metadata. Limit imports initially to 50 MiB per attachment and ask before larger files; limits are visible settings, not hidden truncation.
2. Support safe image/text/PDF viewing and download/open-in-default-app on a deliberate user action. Attachments are not executable within the app.
3. Index text/Markdown content immediately. Add text-PDF extraction only through a measured parser path; scanned PDF/OCR, Office parsing, and audio/video analysis remain labelled unsupported/backlog.
4. A delete action warns when other notes reference the attachment and uses recoverable trash. Copying imports preserves the original file outside the vault.

| File | One-line creation/change |
| --- | --- |
| `schemas/attachment.schema.json` | Define copied-file metadata, original display name, hash, MIME, size, and indexing status. |
| `sidecar/memory_worker/attachments.py` | Validate/copy/hash attachments and manage reference-aware trash/restore. |
| `sidecar/memory_worker/document_text.py` | Extract supported text and text-PDF content with bounded parsing and provenance. |
| `src-tauri/src/resources.rs` | Serve only allowlisted vault assets and open approved files through native handlers. |
| `src/app/features/notes/attachment-panel.component.ts` | Drive explicit import, preview, indexing status, and deletion review. |
| `src/app/features/notes/attachment-panel.component.html` | Render attachments with usable unsupported/too-large/failed states. |
| `sidecar/tests/test_attachments.py` | Verify size/path/MIME handling, duplicate bytes, deletion references, and unsupported documents. |

Exit gate: attach/read a supported file, view unsupported status for a scan/binary, delete/restore the copied attachment, and verify the external original remains intact.

### Step 09 — Add links, backlinks, and exact source viewing

Prerequisite: note identity/indexing and safe preview.

1. Parse supported Markdown relative links and a documented `[[title-or-id]]` subset; keep unresolved and ambiguous links visible. Do not promise complete Obsidian syntax compatibility.
2. Index forward/backlinks and update them on move/rename. For text links that become ambiguous, show choices; do not silently relink by semantic similarity.
3. Implement evidence navigation by stable source/artifact/message/span references. Verify hashes before highlighting; a mismatch produces a source-changed error.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/links.py` | Parse/resolve supported links and update the derived backlink graph. |
| `sidecar/memory_worker/evidence.py` | Validate artifact/excerpt hashes and return exact bounded source passages. |
| `src/app/features/notes/backlinks-panel.component.ts` | Load linked/unresolved references for the active note. |
| `src/app/features/notes/backlinks-panel.component.html` | Render backlinks and visible ambiguity without automatic inference. |
| `src/app/shared/source-viewer.component.ts` | Resolve and navigate cited sources/messages/spans with hash validation. |
| `src/app/shared/source-viewer.component.html` | Display original/normalized source labels and the exact highlighted evidence. |
| `sidecar/tests/test_links_evidence.py` | Verify rename/duplicate-title/unresolved links and UTF-8/CRLF citation spans. |

Exit gate: two linked notes show correct backlinks after rename; a non-ASCII source span opens the exact passage; changed/corrupt source artifacts are detected.

### Step 10 — Implement conversation imports with honest parsing

Prerequisite: canonical sources, evidence, indexing, and reviewable UI.

1. Provide paste/plain-text and normalized JSON imports first. Preview detected speakers/timestamps and let the user correct unknowns before processing.
2. Preserve original bytes, build normalized messages and an immutable transcript artifact, and calculate byte offsets as the transcript is written. Store mappings to original provider fields/branches; cite the normalized transcript explicitly when normalization occurred.
3. Use SHA-256 for exact duplicate detection and request IDs for idempotency; similar text is not auto-deduplicated. Handle conversation branches by user-selected branch or separately preserved branches.
4. Implement ChatGPT/Claude export adapters only after inspecting anonymized samples and supported official export behavior. Unsupported versions return a clear error and offer paste; they do not return an empty “successful” import.
5. Use a proposed 20 MiB conversation limit; for archives inspect file count/uncompressed sizes and reject traversal. Larger imports become bounded jobs. The original input is kept even when parsing fails.

| File | One-line creation/change |
| --- | --- |
| `schemas/import.schema.json` | Define supported import requests, normalized messages, parsing warnings, and branch selection. |
| `sidecar/memory_worker/importers/__init__.py` | Register tested formats and capability/version detection. |
| `sidecar/memory_worker/importers/plain_text.py` | Parse labelled paste conservatively and preserve uncertain roles/dates. |
| `sidecar/memory_worker/importers/normalized_json.py` | Validate the app's stable provider-independent conversation format. |
| `sidecar/memory_worker/importers/chatgpt_export.py` | Parse only fixture-verified ChatGPT export shapes/branches and reject unknown formats. |
| `sidecar/memory_worker/importers/claude_export.py` | Parse only fixture-verified Claude export shapes and reject unknown formats. |
| `sidecar/memory_worker/ingestion.py` | Preserve source bytes, create normalized transcript/evidence mappings, and queue indexing. |
| `src/app/features/import/import-page.component.ts` | Drive file/paste selection, preview corrections, scope/branch selection, and jobs. |
| `src/app/features/import/import-page.component.html` | Render import preview, unknown fields, duplicate handling, and parsing errors. |
| `sidecar/tests/fixtures/imports/normalized.json` | Store a synthetic normalized conversation with known source spans. |
| `sidecar/tests/fixtures/imports/plain-text.txt` | Store ambiguous speaker/date/approval text for conservative parsing. |
| `sidecar/tests/test_imports.py` | Verify source preservation, duplicate imports, invalid exports, branches, and Unicode provenance. |

Exit gate: import/paste a session, correct unknown roles, repeat import without duplication, restart, and inspect exact raw/normalized evidence. Provider adapters remain disabled until G09 and their fixtures are verified.

### Step 11 — Integrate local models with schema-validated candidate extraction

Prerequisite: G05 candidate narrowed by measurements; inference packaging and source imports work.

1. Launch bundled inference only when needed, with model files from verified resource paths. Bind to loopback, use a random per-process credential, and disable the web UI/tools where the pinned runtime supports verified flags.
   Rust's allowlisted AI-job dispatch ensures the approved runtime is ready before forwarding the worker request, and supplies endpoint/model identity/credential over private stdio using an internal-only configuration message. The frontend never receives the credential or chooses an arbitrary endpoint/binary; the worker cannot request an unapproved runtime.
2. Queue expensive requests one at a time initially; avoid loading both generation and embeddings simultaneously on low-memory hardware. Idle-unload after a proposed five minutes and show load/cancel progress.
3. Chunk by source message/paragraph with tokenizer-aware limits and stable offsets; preserve adjacent user/assistant turns for approval interpretation. Record model/prompt/chunk version in each extraction job.
4. Ask for structured candidates with valid evidence references. Validate JSON shape, exact excerpts, source IDs, and kind/state consistency. Retry invalid output once; then return a visible failure/manual-review path.
5. Treat embedded “ignore instructions” text as data. Do not pass generic tools to the model or allow it to execute commands. User corrections are durable and are not overwritten by re-extraction.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/model_runtime.py` | Manage approved loopback runtime requests, timeouts, credentials, and model capability checks. |
| `sidecar/memory_worker/chunking.py` | Produce tokenizer-bounded source chunks with precise evidence spans and neighboring turns. |
| `sidecar/memory_worker/extraction.py` | Generate/validate extraction candidates and preserve prompt/model provenance. |
| `sidecar/memory_worker/prompts/extract.md` | Instruct conservative extraction of suggestions/decisions/tasks/attempts/preferences/questions with evidence. |
| `sidecar/memory_worker/prompts/plain-english.md` | Define plain-English output behavior without claiming formal STE compliance. |
| `src-tauri/src/inference.rs` | Launch/stop only verified bundled inference binaries and report their real health. |
| `src/app/features/settings/model-status.component.ts` | Display selected model, local mode, memory/loading failures, and retry controls. |
| `src/app/features/settings/model-status.component.html` | Render model state and explain usable manual/keyword features during failures. |
| `sidecar/tests/test_extraction_validation.py` | Reject invented spans/IDs, unsupported transitions, injected instructions, and malformed outputs. |
| `tools/eval-extraction.py` | Run measured candidate extraction against labelled synthetic cases without changing gold labels. |

Exit gate: actual local generation produces reviewable candidates with valid citations; malformed/invented candidates are rejected; cancellation works; offline note/search workflows survive model failure.

### Step 12 — Add review, decision history, manual memory, and task states

Prerequisite: durable records, verified evidence, and extraction candidates; manual records do not require a model.

1. Show each candidate beside its exact evidence. Provide accept/edit/reject/mark-unclear actions, with summary approval separate from decision confirmation. A model's confidence is not proof of user approval.
2. Save accepted extraction as a record with an explicit review event. Imported approval is a suggested interpretation until the user confirms it. Manual entries state `user_entered` as their basis rather than pretending to have transcript evidence.
3. Require expected revision and operation ID for every state change. Apply the current record snapshot and its event under the same journaled operation; verify the snapshot matches the latest event on rebuild. If they disagree, report a conflict rather than guessing which to trust.
4. Confirming/rejecting an imported decision requires the user action and cited basis; superseding requires an explicit link to the replacement decision and its basis. Keep history. Reopening/correcting a state creates a new event, not a deleted audit line.
5. Generated tasks begin as suggested; acceptance makes them open. Only user action or reviewed explicit evidence marks work done. Preferences, attempts, and open questions have equivalent editable, provenance-aware views.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/records.py` | Create/update typed records with revision checks, source basis, and journaled snapshots. |
| `sidecar/memory_worker/review.py` | Validate review/decision/task transitions and append idempotent audit events. |
| `src/app/features/review/review-page.component.ts` | Load candidates, manage edits/actions, and handle revision conflicts. |
| `src/app/features/review/review-page.component.html` | Render candidate-versus-evidence review without combining acceptance and confirmation. |
| `src/app/features/review/review-page.component.scss` | Style readable comparison panes and distinct state labels at narrow widths. |
| `src/app/features/records/record-detail.component.ts` | Load typed record state, editable fields, related records, and revision history. |
| `src/app/features/records/record-detail.component.html` | Render decisions/tasks/preferences/attempts/questions with source and actor labels. |
| `sidecar/tests/test_review_states.py` | Verify ambiguous approval, supersession, concurrent edits, duplicate operations, and audit recovery. |
| `tests/e2e/review.spec.ts` | Prove reviewing a summary does not confirm a decision and a correction survives restart. |

Exit gate: the ambiguous-approval suite produces zero automatic confirmations; explicit confirmation/rejection/supersession is auditable; manual tasks and corrected records survive rebuild and restart.

### Step 13 — Implement lexical and semantic retrieval

Prerequisite: indexed chunks, reviewed records, and measured embedding configuration.

1. Search FTS5 with a safely constructed query and bound scope/kind/state/date filters. Escape ordinary user input; expose any advanced search syntax as a documented optional mode.
2. Generate embeddings in bounded batches and record model/chunk/pooling versions. Recompute only affected vectors. Reject dimension/version mismatches and gracefully fall back to lexical search when embeddings are missing.
3. Fuse lexical and cosine rankings using reciprocal-rank fusion with an initial constant of 60; treat this as a tunable engineering baseline, not an upstream default. Retrieve up to 20 from each route, deduplicate by stable chunk ID, then return a bounded result set.
4. Expand retrieved decisions with their explicit supersession/current-state links and nearby source messages. Do not let a high similarity score turn a proposed decision into a confirmed one. Graph expansion is added after Step 16.
5. Display exact excerpts, scope, record state, source date if known, and stale/index-age notices. Debounce UI search, cancel superseded requests, and keep clear empty/error/partial states.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/embeddings.py` | Batch local embeddings, validate model metadata, and store versioned vectors. |
| `sidecar/memory_worker/retrieval.py` | Apply filters, lexical/cosine ranking, fusion, deduplication, and evidence-linked expansion. |
| `src/app/features/search/search-page.component.ts` | Manage query/filter state, cancellation, results, and source navigation. |
| `src/app/features/search/search-page.component.html` | Show grounded results and visible state/freshness/index notices. |
| `sidecar/tests/test_retrieval.py` | Verify filters, mixed rankings, incompatible vectors, current decisions, and lexical fallback. |
| `tools/eval-retrieval.py` | Measure recall@5 and latency against labelled queries without mutating ground truth. |

Exit gate: the selected embedding model runs offline; keyword search remains usable without it; filtered retrieval and decision expansion pass tests; the recorded recall target is met on the evaluation subset available at this stage.

### Step 14 — Answer memory questions with citations and honest uncertainty

Prerequisite: verified retrieval and local generation; evidence viewer works.

1. Build a bounded context containing retrieved passages plus explicit decision states/revisions, not an unrestricted vault dump. Distinguish source text from application instructions and never give the model execution tools.
2. Request structured claims with evidence IDs and an answer status. Validate reference existence, exact excerpts, scope, and state consistency. Reject invented sources; an ID validator alone does not prove semantic support, so use labelled human evaluation as well.
3. When sources conflict, report both with dates/revisions rather than picking the newest automatically. On insufficient evidence, say what is missing. Do not fill gaps from general model knowledge as though they were personal memory.
4. Render only validated claims and citations. If streaming is used, show an uncommitted progress indicator until validation; do not expose unvalidated factual text as the final answer. Allow copy/save only through explicit actions.
5. Saving an answer creates a labelled derived note with citations and generation metadata; it does not make that answer new approval evidence for the original decision.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/answering.py` | Assemble bounded context, generate structured answers, and enforce citation/state validation. |
| `sidecar/memory_worker/prompts/answer.md` | Require source-grounded claims, simple English, conflict disclosure, and abstention. |
| `src/app/features/ask/ask-page.component.ts` | Manage question jobs, validated answers, cancellation, and explicit saving. |
| `src/app/features/ask/ask-page.component.html` | Render cited claims, uncertainty, conflicts, and model/index failures. |
| `sidecar/tests/test_answers.py` | Reject invented citations, unsupported states, injected source instructions, and evidence-free claims. |
| `tests/e2e/ask.spec.ts` | Verify question-to-answer-to-original-source navigation and insufficient-evidence behavior. |

Exit gate: a grounded question returns an inspectable answer; an unanswered/contradictory question abstains or exposes conflict; manual citation checks and model evaluation distinguish structural validity from actual correctness.

### Step 15 — Deliver the core resume and assistant-handoff workflow

Prerequisite: reviewed records, searchable evidence, and current task/scope selection.

1. Build a deterministic state bundle first: user-selected task, approved decisions, proposals, recorded completed work/attempts, unresolved questions, and next actions. A generated task can never be labelled completed merely because the conversation ended.
2. Expand linked replacements and critical unresolved questions even if they were not in the top retrieval hits. Label the bundle's scope/time/index revision and what was excluded. Show stale evidence without silently removing historical reasoning.
3. Use local generation only to compress/rephrase the validated bundle. Preserve exact IDs, source anchors, distinctions, and unknowns; fall back to a structured non-AI template if compression fails.
4. Let the user inspect/edit the package before copying or exporting. Display a warning that pasting it into a cloud assistant shares the selected content with that provider. Never copy the full vault or machine-specific paths by default.
5. Provide a character budget when the destination tokenizer is unknown; count tokens only with a verified selected tokenizer. If the budget cannot contain critical decisions/questions, tell the user and offer a larger budget or smaller scope rather than silently truncating them.
6. Save explicit handoffs as Markdown plus versioned metadata; keep citations useful inside this app. A different computer/assistant cannot be promised access to local file links: offer a self-contained quoted-evidence export and explain the portability limits.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/context.py` | Assemble current task state with reviewed decisions, replacements, attempts, questions, and evidence. |
| `sidecar/memory_worker/handoff.py` | Produce bounded editable handoffs, validate essential coverage, and save explicit exports. |
| `sidecar/memory_worker/prompts/handoff.md` | Compress the state bundle without inventing approval, completion, attempts, or next actions. |
| `src/app/features/resume/resume-page.component.ts` | Manage task selection, draft generation, edits, budgets, copy/export, and coverage warnings. |
| `src/app/features/resume/resume-page.component.html` | Render confirmed/proposed/unknown sections beside inspectable evidence and sharing notice. |
| `sidecar/tests/test_handoffs.py` | Verify essential coverage, critical replacements, budget overflow, edits, and portable evidence exports. |
| `tests/e2e/resume.spec.ts` | Recover a synthetic interrupted session and copy an accurate reviewed handoff. |

Exit gate: the stuck-session scenario recovers what was requested versus merely suggested, identifies the next unresolved action, and exports a reviewable package without false approvals or omitted critical replacements.

### Step 16 — Connect repositories and adapt verified Graphify output

Prerequisite: G04 passes; code extraction is local; vault metadata separates portable repo IDs from machine paths.

1. Add repositories only through explicit user selection. Store repo roots in machine-local app data; do not scan arbitrary drives. Show include/exclude rules before indexing; exclude credentials, `.git` internals, dependency/build folders, large binaries, and unselected files.
2. Run extraction against a bounded staged snapshot of approved code. Record file hashes, commit if available, dirty contents, extraction/version/time, and original relative paths. Never run repository install scripts, imported code, Git hooks, or assistant configuration installers.
3. Invoke only the exact pinned API/CLI established in Step 02, inside a restricted job environment with provider credentials removed and query logging disabled. Verify the output path and normalize only recognized graph fields; reject incompatible schemas explicitly.
4. Assign stable graph identities based on repo/path/symbol identity and extraction version, while retaining rename ambiguity. Distinguish syntax-derived edges from inferred claims. Link memory to code by exact references or user-reviewed suggestions, not by pretending all semantic matches are facts.
5. Support multiple repository jobs with cancellation, failure isolation, and selected reindexing. Disconnecting removes the machine connection/derived cache, not the repository or historical memory evidence.
6. Add bounded graph-neighbor retrieval to Step 13 with relation provenance visible. Preserve the last successful graph when a new extraction fails and mark it stale.

| File | One-line creation/change |
| --- | --- |
| `schemas/repository.schema.json` | Define portable repo refs, connection settings, snapshot manifests, and index-job status. |
| `sidecar/memory_worker/repositories.py` | Validate selected roots, build safe snapshots, and track commits/hashes/connections. |
| `sidecar/memory_worker/graphify_adapter.py` | Invoke the inspected local extraction path and normalize pinned output into the app contract. |
| `sidecar/memory_worker/graph_store.py` | Index versioned nodes/edges and exact memory-to-code references. |
| `src/app/features/repositories/repositories-page.component.ts` | Manage selected connections, exclusions, jobs, and reviewed memory links. |
| `src/app/features/repositories/repositories-page.component.html` | Display repo scope, extraction status, provenance, failures, and disconnect controls. |
| `sidecar/tests/test_repositories.py` | Verify exclusions, escaping symlinks, dirty files, multiple repos, schema failure, and nondestructive disconnect. |
| `sidecar/tests/test_graphify_adapter.py` | Validate the actual pinned graph fixture, extraction origins, and prohibited cloud paths. |

Exit gate: a synthetic repository maps correctly offline, connects to an evidenced decision, and survives a failed reindex; a second connection is isolated; original repository files/configuration remain unchanged.

### Step 17 — Add daily notes, templates, priorities, and default startup

Prerequisite: manual/reviewed task states and desktop settings; native startup plugin verified on the target OS.

1. Add safe templates for daily notes, meetings, decisions, and session logs. Support a documented variable allowlist such as date/title/scope; no executable expressions or shell interpolation. Create a daily note only when opened, using the user's local calendar/timezone.
2. Rank accepted unfinished tasks deterministically: user pins first, then overdue/due-today items, then priority and age, with stable ID tie-breaking. Exclude suggested/done/cancelled tasks and make blocked work visible as blocked. Show the ranking reason and let the user reorder it.
3. Show at most three priorities; if fewer valid tasks exist, show fewer. Do not invent commitments from model guesses, and do not mark old work overdue when its due date is unknown.
4. First-run setup displays start-at-login enabled by default with an immediately available off switch. Enable the actual OS registration after setup completes; persist disablement and never re-enable it during an update. Report OS/plugin failures instead of displaying a misleading enabled state.
5. On login startup, open the daily-priority view without starting expensive AI work or showing unsolicited system notifications. Use single-instance routing if already running. Do not depend on a cloud calendar or recurring external service.

Use the current [Tauri autostart plugin](https://v2.tauri.app/plugin/autostart/) and verify actual enable/disable/is-enabled behavior on each supported OS; do not assume the same implementation on Windows and Mac.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory_worker/tasks.py` | Validate task edits and calculate explained deterministic daily priorities. |
| `sidecar/memory_worker/daily_notes.py` | Create local-date daily notes and render safe user-editable templates. |
| `assets/templates/daily.md` | Define a daily journal with priorities, work log, and reflection placeholders. |
| `assets/templates/meeting.md` | Define meeting context, evidence, proposed decisions, and task fields. |
| `assets/templates/decision.md` | Define rationale/alternatives/state fields without defaulting to approval. |
| `assets/templates/session.md` | Define completed work, attempts, open questions, and next-session context. |
| `src/app/features/today/today-page.component.ts` | Load daily notes/tasks and manage pins, state changes, and ranking explanations. |
| `src/app/features/today/today-page.component.html` | Render up to three actual priorities and the editable daily note. |
| `src/app/features/settings/startup-settings.component.ts` | Reconcile desired startup preference with real native registration state. |
| `src/app/features/settings/startup-settings.component.html` | Show the default, off switch, actual status, and recoverable registration errors. |
| `src-tauri/src/autostart.rs` | Implement bounded startup commands and route login launches to the daily view. |
| `sidecar/tests/test_daily_tasks.py` | Verify task eligibility, due dates/timezones, fewer-than-three results, ties, and safe templates. |
| `src-tauri/tests/autostart_preferences.rs` | Verify explicit disablement persists through application restart/update initialization. |

Exit gate: accepted tasks produce truthful top-three reasons, daily notes survive restart, and real OS login starts the app only when enabled. Unknown dates and template code are never executed or invented.

### Step 18 — Add typed properties and saved table views

Prerequisite: portable notes/frontmatter, typed filters, and conflict-safe writes.

1. Support text/number/boolean/date/enum/text-list properties, with documented null/missing behavior. Parse YAML safely with no object constructors; preserve unknown user keys and Markdown text when updating supported fields.
2. Keep user metadata in note frontmatter, typed property definitions and saved views in durable JSON, and query indexes rebuildable. Never change a property's type silently when existing values conflict.
3. Implement column selection, sort, bounded filters, pagination/virtualization, and saved views. Use an allowlist of fields/operators and parameterized queries; no arbitrary SQL or formula execution.
4. Show invalid existing values as errors with repair choices. Base feature names on this app's documented subset, not a promise of full Obsidian Bases compatibility.

| File | One-line creation/change |
| --- | --- |
| `schemas/property-view.schema.json` | Define typed property definitions and safe saved-view filters/sorts/columns. |
| `sidecar/memory_worker/properties.py` | Validate metadata types and apply conflict-safe frontmatter edits. |
| `sidecar/memory_worker/views.py` | Save portable views and translate allowed filters to bounded parameterized queries. |
| `src/app/features/views/table-page.component.ts` | Manage table data, column selection, typed edits, and saved view state. |
| `src/app/features/views/table-page.component.html` | Render accessible sortable tables with validation and missing-value states. |
| `sidecar/tests/test_properties_views.py` | Verify type conflicts, unknown-key preservation, safe parsing, and injection-resistant filtering. |

Exit gate: a saved task/project view reconstructs after cache deletion; invalid values cannot corrupt the Markdown; sorting/filtering preserves the documented null behavior.

### Step 19 — Implement change detection and memory freshness review

Prerequisite: versioned evidence, repository manifests, reviewed records, and file watcher recovery.

1. Track explicit dependencies between memory and supporting note/document/code revisions. A file change marks affected records `needs_review`; it does not automatically invalidate, reject, or supersede a decision.
2. Keep immutable evidence snapshots for user-edited source revisions, including note-derived citations. Preserve the old cited revision while indexing the current one; show whether the citation describes historical or current content.
3. Distinguish changed/missing source, corrupted immutable artifact, unsupported re-extraction, and simply old index age. A modified preserved raw import is an integrity error, not normal freshness. Broad folder changes do not make every unrelated memory stale.
4. Offer accept-still-valid, update-with-evidence, or leave-unresolved actions. Record reviewer/time/revision; every state replacement still follows Step 12's explicit transition rules.
5. Debounce watcher events, compare hashes, handle moves and temporary editor saves, and reconcile on startup/after missed events. Never rewrite source files while investigating freshness.

| File | One-line creation/change |
| --- | --- |
| `schemas/freshness.schema.json` | Define dependency checks, changed/integrity/index-age reasons, and review resolutions. |
| `sidecar/memory_worker/source_revisions.py` | Preserve immutable cited snapshots and associate current editable source revisions. |
| `sidecar/memory_worker/freshness.py` | Compute evidence-linked change impact and persist reviewed resolution events. |
| `src/app/features/freshness/freshness-page.component.ts` | Load affected records, comparisons, and explicit resolution actions. |
| `src/app/features/freshness/freshness-page.component.html` | Show why memory needs review without labelling a changed file as automatic invalidation. |
| `sidecar/tests/test_freshness.py` | Verify narrow impact, source integrity errors, historical citations, moves, and explicit revalidation. |

Exit gate: editing linked code flags the correct memory; unrelated code does not; an old citation remains inspectable; the decision's actual state changes only through a reviewed event.

### Step 20 — Add limited local MCP tools and tested assistant setup

Prerequisite: evidence/retrieval/context contracts, packaged worker, and reviewed scope permissions. Remote/cloud transport is not enabled by this step.

1. Pin a compatible release of the [official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk), including its actual supported protocol/API version. Its current documentation includes v2; Graphify's optional MCP extra has its own constraints. Do not combine incompatible extras or copy an unverified `FastMCP`/`MCPServer` signature. The app adapter, not Graphify's own MCP server, owns this tool surface.
2. Provide `search_memory`, `get_context`, and `fetch_evidence` as bounded read tools; `save_session` stages an inbox request only. Each tool declares validated input/output contracts and accurate annotations. Tool hints never substitute for actual permission checks.
3. Configure access in the desktop UI: selected vault, allowed scopes, maximum passage/result sizes, and whether staging is allowed. Start the frozen stdio worker against a machine-local connection ID; tools cannot accept arbitrary roots, paths, executables, or permission expansions.
4. While the app writes, read a consistent SQLite transaction with an actual supported read-only connection; do not use SQLite `immutable` mode on a live changing database. If cache is missing/stale or recovery is pending, return a clear bounded status instead of rebuilding/writing from the MCP process.
5. Make `save_session` idempotent and atomically stage a schema-valid request in the inbox. Return `staged`, not `saved/indexed`; the desktop app asks the user to review/import it before canonical mutation. The payload has size limits and is data, never assistant instructions.
6. Generate setup snippets for a verified client using the resolved installed path. User-triggered setup must preserve existing configuration and preview any changes. [Claude Code's MCP documentation](https://code.claude.com/docs/en/mcp) supports local stdio tools; test the actual installed client rather than treating all Claude products as equivalent.
7. Keep copy/export available for ChatGPT. [Official OpenAI documentation](https://developers.openai.com/plugins/build/mcp-server) distinguishes private developer connections/tunnels from publicly submitted HTTPS plugins. Do not claim this stdio binary automatically connects to every ChatGPT account. A supported direct connector is Step 26 and G08; even local retrieval delivered to a cloud assistant shares the returned content with that provider.

| File | One-line creation/change |
| --- | --- |
| `schemas/mcp-tools.schema.json` | Define the four app tools, bounded results, index status, and staged-write responses. |
| `sidecar/memory_worker/mcp_server.py` | Serve the standard stdio MCP mode with compatible SDK APIs and isolated diagnostics. |
| `sidecar/memory_worker/mcp_tools.py` | Enforce per-connection scope permissions and bounded retrieval/staging behavior. |
| `sidecar/memory_worker/inbox.py` | Atomically stage/deduplicate requests and import them through desktop review. |
| `src/app/features/integrations/integrations-page.component.ts` | Manage local connections, scope access, staging controls, and tested setup snippets. |
| `src/app/features/integrations/integrations-page.component.html` | Display actual client capabilities and the cloud-sharing implications of returned memory. |
| `docs/integrations/claude-code.md` | Document the tested installed-binary setup, permissions, transport, and limitations. |
| `docs/integrations/chatgpt.md` | Document copy/export now and separately labelled future connector requirements. |
| `sidecar/tests/test_mcp_tools.py` | Verify schemas, scope isolation, unauthorized evidence, size limits, and truthful staged responses. |
| `sidecar/tests/test_mcp_stdio.py` | Test real SDK initialization/tool calls, stdout purity, cancellation, and app-closed reads. |

Exit gate: a tested local client retrieves only approved scopes and stages a session without mutating canonical decisions; app-closed/stale-cache status is truthful; unsupported ChatGPT/Claude variants are not advertised as working integrations.

### Step 21 — Build the original identity, accessible graph, and polished design

Prerequisite: G02 for final branding; existing functional flows and graph provenance. Neutral UI styling can proceed before the public name is chosen.

1. Use Angular Material/CDK with custom SCSS tokens, CodeMirror, locally bundled SVG UI icons, Three.js, and GSAP/ScrollTrigger. Do not mix React component kits into Angular. Start with system fonts (Segoe UI on Windows and the native Mac system stack), avoiding runtime font downloads.
2. Propose a quiet charcoal/off-white palette with a restrained memory-themed accent and distinct warning states; validate actual contrast before approval. Use typography, spacing, and state labels consistently. Status cannot depend on color alone.
3. Create a small set of brain/memory/studious logo concepts after name selection, then obtain the user's selection. If generating raster concepts with AI, use the available image-generation skill; do not pretend a generated bitmap is an editable SVG. Construct/review the final original vector mark and wordmark from the approved design, preserving reproducible sources.
4. Supply light/dark and monochrome versions, a square 1024×1024 RGBA icon source, and readable silhouettes at 16/32 pixels. Keep text out of tiny native icons. Use the verified [Tauri icon generator](https://v2.tauri.app/develop/icons/) to create platform formats; inspect actual generated filenames, alpha, and OS appearance.
5. Graph navigation opens a selected scope with an initial cap of 250 nodes/500 edges, a visible total/truncation label, filters, and an equivalent searchable relationship list. Select a node to open its record/evidence; display extracted versus inferred edges differently.
6. Check WebGL2 availability and gracefully switch to the list when unavailable. Pause rendering when hidden; dispose geometry/material/texture/listeners on destruction; use deterministic layout and selection state. Measure frame time on G03 hardware rather than promising universal smoothness.
7. Use GSAP for bounded focus transitions and ScrollTrigger only where a scrolling timeline improves reading. Clean up animations/triggers; respect reduced motion; never animate away source text while it is being reviewed. Literal `skrollr` integration is not approved—confirm only if the user specifically wants that library.

| File | One-line creation/change |
| --- | --- |
| `src/styles/tokens.scss` | Define reviewed color/spacing/type/radius/focus/motion tokens and light/dark variants. |
| `src/styles/material-theme.scss` | Apply the verified Angular Material theming API to the custom tokens. |
| `src/app/shared/icon-registry.ts` | Register only locally bundled sanitized UI SVG assets with consistent names. |
| `src/app/features/graph/graph-page.component.ts` | Coordinate bounded graph data, capability detection, filters, selection, and list fallback. |
| `src/app/features/graph/graph-page.component.html` | Render graph controls and equivalent keyboard-accessible relationship navigation. |
| `src/app/features/graph/graph-page.component.scss` | Style responsive graph/evidence panels and accessible selected/provenance states. |
| `src/app/features/graph/graph-renderer.ts` | Own Three.js rendering/layout/picking and deterministic resource cleanup. |
| `src/app/features/records/history-timeline.component.ts` | Coordinate evidenced chronological history and reduced-motion GSAP lifecycle. |
| `src/app/features/records/history-timeline.component.html` | Render a readable scrollable revision timeline with source links. |
| `design/brand/logo-mark.svg` | Store the approved editable original symbol without embedded remote content. |
| `design/brand/logo-lockup.svg` | Store the approved symbol/name composition with outlined or licensed typography. |
| `design/brand/logo-monochrome.svg` | Store a tested single-color mark for small/high-contrast uses. |
| `design/brand/icon-source.png` | Store the approved square 1024-pixel RGBA raster for platform icon generation. |
| `design/brand/README.md` | Record concept approval, asset provenance/licensing, palette, safe area, and export procedure. |
| `src/assets/brand/logo-mark.svg` | Bundle the approved runtime mark without external network dependencies. |
| `src-tauri/icons/icon.ico` | Generate and inspect the Windows icon from the approved source. |
| `src-tauri/icons/icon.icns` | Generate and inspect the Mac icon from the approved source. |
| `src-tauri/icons/32x32.png` | Generate the tested small PNG variant for native packaging. |
| `src-tauri/icons/128x128.png` | Generate the tested standard PNG variant for native packaging. |
| `src-tauri/icons/128x128@2x.png` | Generate the tested high-density PNG variant for native packaging. |
| `tests/e2e/graph-accessibility.spec.ts` | Verify list fallback, keyboard selection, truncation, reduced motion, and panel resizing. |

Any additional icon-generator outputs are recorded by exact path in the Step 21 ledger; they are generated assets, not guessed handwritten files. Initial app previews may use clearly labelled neutral placeholders, never a falsely approved final logo.

Exit gate: user-selected identity is recorded; icons are recognizable at native sizes; graph and list reach the same evidence; theme/keyboard/reduced-motion checks pass; repeated route changes do not leak rendering resources.

### Step 22 — Verify backup/restore, deletion, security, and privacy controls

Prerequisite: complete durable format, source revisions, and native file dialogs.

1. Export a consistent manifest-hashed archive of canonical notes/scopes/records/events/raw sources/attachments/handoffs/templates/views/settings. Exclude locks, runtime paths, credentials, model files, caches, and pending journals; pause mutations or take a verified consistent snapshot. Include trash only through an explicit option.
2. Restore to a new selected empty destination first. Validate format/version/hash/size/file-count, reject unsafe archive paths/symlinks/device names, then rebuild and compare counts/states/citations. Never silently merge into or overwrite an existing vault/repository.
3. First-release backups are ordinary unencrypted files: say so clearly. Local-first is not equivalent to application-level encryption or protection from other processes under the same account. Encryption is separately scoped future work, not a hidden promise.
4. Deletion moves selected records/files to vault trash with dependency warnings and restore metadata. Permanent deletion requires explicit user action, exact-target validation, and clear effects on sources/evidence; never recursively delete a repository or vault merely to clear a cache.
5. Restrict Tauri capabilities/CSP and approved local asset access. Disable remote Markdown images/HTML active content by default, open external links only through deliberate user action, and reject unsafe URL schemes. Worker/runtime processes accept only validated app-owned operations.
6. Keep diagnostics local with bounded retention and redacted codes/timings; no transcript/query/prompt/output/token logs by default. Inspect all bundled libraries for logging/telemetry and network behavior. A user-initiated support export must be previewable and redacted; it is not automatically uploaded.
7. Test offline workflows with traced app-controlled connections. Allow only the intended authenticated loopback inference traffic; do not describe WebView/OS network behavior as developer telemetry. Make update checks manual in this release; future auto-updates require signed artifacts and a disclosed network policy.

| File | One-line creation/change |
| --- | --- |
| `schemas/backup.schema.json` | Define portable backup manifests, integrity hashes, versions, and restore summaries. |
| `sidecar/memory_worker/backup.py` | Create consistent canonical archives and validate safe restore-to-new-folder operations. |
| `sidecar/memory_worker/deletion.py` | Implement recoverable deletion, dependency checks, restoration, and exact-target purge. |
| `sidecar/memory_worker/diagnostics.py` | Emit bounded local redacted diagnostics without content/query/credential logging. |
| `src/app/features/settings/data-settings.component.ts` | Manage export/restore/trash and preview explicit diagnostic exports. |
| `src/app/features/settings/data-settings.component.html` | Explain plaintext backups, irreversible purge, and actual data-sharing behavior. |
| `src-tauri/tauri.conf.json` | Harden CSP/resource access and keep automatic network update checks disabled. |
| `src-tauri/capabilities/default.json` | Remove unused permissions and scope remaining native operations to verified needs. |
| `docs/privacy.md` | Explain local storage, no developer collection, plaintext files, optional exports, and OS/runtime boundaries. |
| `docs/threat-model.md` | Record trust boundaries, prompt injection, loopback access, archive risks, and same-account limitations. |
| `sidecar/tests/test_backup_restore.py` | Verify consistent snapshots, corrupt/unsafe archives, interrupted restore, and rebuild equivalence. |
| `sidecar/tests/test_deletion.py` | Verify recoverable deletion and that selected external repositories/original imports stay intact. |
| `tests/e2e/privacy.spec.ts` | Verify preview blocks remote content and sensitive support/export actions require deliberate user input. |

Exit gate: a restored vault reproduces confirmed states and evidence after cache rebuild; trash restores correctly; offline tests show no app-controlled external requests; privacy text matches observed behavior.

### Step 23 — Produce native offline packages and clean-machine proof

Prerequisite: G02/G03/G05/G07 resolved for each advertised target; functional regression and privacy checks pass.

1. Lock the approved name/version/publisher/bundle ID; derive target-specific resource layouts from the Step 02 prototype. Build the frozen Python worker on each OS/architecture, collect its native dependencies, and package its support directory without assuming a cross-compiled worker is valid.
2. Package only hash-verified runtime/model assets. Record source URLs, versions, licenses/notices, CPU instruction requirements, architecture, disk sizes, and complete resource paths. Do not redownload artifacts during user installation or require Python/Node/Rust/Ollama on the user's machine.
3. Build Windows NSIS with the verified offline WebView2 installation mode. Test standard-user installation and uninstall, non-ASCII/spaced paths, missing WebView2, upgrade, app startup registration, and preservation of personal vaults. Record measured installed/installer size rather than extrapolating from model file size.
4. Build separate Mac ARM64 and Intel DMGs on supported native build environments; test resource resolution, frozen-worker startup, local inference/Graphify, signing, startup registration, and drag-install behavior. Untested targets remain unavailable, not labelled supported.
5. Follow [Windows signing guidance](https://v2.tauri.app/distribute/sign/windows/) and [Mac signing/notarization guidance](https://v2.tauri.app/distribute/sign/macos/). A ₹0 demo may require documented unsigned/ad-hoc security prompts; it cannot promise the same installation experience as a fully signed/notarized release. Do not purchase credentials or upload private signing keys without the user's decision.
6. Validate package-size/hosting limits against the real release host and installer tool. If a full model package cannot be delivered there, resolve an honest supported distribution choice with the user. Do not silently substitute a network-dependent lightweight installer for the promised offline one.
7. Make release builds manually triggered and do not publish automatically. Review CI availability, private/public billing/quotas, and model downloads before enabling hosted jobs; local/native builds are valid. Keep credentials out of repository files and personal memory out of artifacts.

| File | One-line creation/change |
| --- | --- |
| `sidecar/memory-worker.spec` | Define the tested PyInstaller onedir entry point, native collections, and support resources. |
| `tools/package-sidecar.py` | Build/validate the worker for the current approved native target and generate its layout manifest. |
| `tools/prepare-assets.py` | Resolve pinned binaries/models, verify checksums/licenses, and stage approved bundle resources. |
| `tools/package-desktop.mjs` | Validate approved identity/assets, invoke native packaging, and record artifact hashes/sizes. |
| `config/bundles/windows-x86_64.json` | Record the tested Windows Rust target, external binaries, support directories, and offline installer settings. |
| `config/bundles/macos-arm64.json` | Record the tested Apple Silicon target, resource layout, signing mode, and minimum tested OS. |
| `config/bundles/macos-x86_64.json` | Record the tested Intel Mac target, resource layout, signing mode, and minimum tested OS. |
| `src-tauri/tauri.conf.json` | Apply approved identity, explicit icon list, validated externalBin/resources, and platform settings. |
| `.github/workflows/check.yml` | Run content-safe schema/frontend/Python/Rust checks on approved pushes/PRs with pinned actions. |
| `.github/workflows/package.yml` | Manually build approved native packages without automatic publication or personal data. |
| `THIRD_PARTY_NOTICES.md` | List bundled software/model licenses and reproduce required upstream notices. |
| `docs/release-checklist.md` | Record per-target clean-machine tests, signing state, resource measurements, and release blockers. |
| `docs/installation-matrix.md` | List only verified OS/architecture/hardware combinations and their exact installation procedure. |

Generated bundle paths are not hand-authored guesses: the package manifest enumerates actual files under `src-tauri/binaries/` and `src-tauri/resources/`, including target-triple sidecar names, worker support libraries, and selected GGUF filenames. Validate each path before configuring Tauri and record exact names in the verification ledger. Keep large binary/model resources out of normal Git history; obtain them reproducibly from the locked manifest.

Exit gate: each advertised installer works offline on a clean target without developer runtimes, imports a session, performs actual local inference/code mapping, restarts correctly, and uninstalls without deleting memory. Signing prompts and untested platforms are clearly disclosed.

### Step 24 — Write usable documentation and a synthetic sample vault

Prerequisite: observed installation/integration behavior and a verified feature matrix.

1. Write the README in plain English: what the app solves, quick installation, first-run setup, demo, supported features, limitations, privacy, offline operation, model/hardware requirements, integrations, export/restore, and troubleshooting. Link only to existing documents/artifacts.
2. Clearly state that the developer does not collect personal data/telemetry and that selected exports/tool results sent to a cloud assistant leave the device. Describe plaintext storage/backups and actual updater/network behavior; do not add broad security/compliance claims.
3. Provide a small invented workspace with notes, a session containing an ambiguous proposal and a later explicit decision, tasks, and a tiny repository fixture. Give every record valid deterministic sample provenance and mark all content synthetic.
4. Generate the sample vault through a reproducible script and validate/rebuild it with the real worker. Do not copy this user's pasted conversation, local repository inventory, or private documents into public samples.
5. Document development tooling separately from end-user installation. Explain how to inspect source evidence, correct a mistaken memory, recover an interrupted task, change startup settings, and restore a backup. Include verified screenshots of the actual app, not mockups presented as shipped UI.

| File | One-line creation/change |
| --- | --- |
| `README.md` | Deliver the plain-English product/install/demo/privacy/limitations overview with verified links. |
| `docs/getting-started.md` | Explain installation, vault creation, import, review, question, and resume workflows. |
| `docs/user-guide.md` | Explain notes, evidence, record states, tasks, repositories, freshness, graphs, and backups. |
| `docs/development.md` | Record locked tooling, native build steps, checks, resource preparation, and debugging boundaries. |
| `docs/troubleshooting.md` | Map actual error codes to tested recovery actions and known platform/model limitations. |
| `docs/demo-script.md` | Define a reproducible ten-minute accurate-recovery demonstration using synthetic content. |
| `sample-workspace/README.md` | Explain synthetic content, expected answers, and safe sample import/reset behavior. |
| `sample-workspace/seed.json` | Define versioned synthetic notes/sessions/records/evidence and their expected relationships. |
| `tools/build-sample.py` | Build/validate the sample vault through canonical worker operations without real user data. |
| `docs/screenshots/README.md` | Inventory actual captured UI screenshots, scenario/target/date, and sensitive-content checks. |
| `sidecar/tests/test_sample_workspace.py` | Rebuild the generated sample and verify its expected decisions/tasks/citations. |

Generated sample vault files follow Section 6 and are enumerated by the seed/build manifest; generated screenshots are named and recorded only after capture. No imaginary screenshot or download link belongs in the README.

Exit gate: a new user can follow the README to install, inspect the synthetic decision evidence, recover the task, and restore a backup; each documented supported feature has verification evidence.

### Step 25 — Run held-out evaluation and the complete release journey

Prerequisite: a packaged candidate and complete synthetic/consented evaluation fixtures.

1. Define at least 30 held-out questions with expected evidence and a separate set of interrupted-task bundles. Include explicit/ambiguous approval, sarcasm/quoted approval, unrelated topics, supersession, rejected options, unknown outcomes, Unicode, missing evidence, code changes, and prompt injection.
2. Keep tuning cases separate from held-out cases. Gold labels are human-reviewed and never regenerated by the model under test. Synthetic cases must not be described as proving reliability on arbitrary real conversations.
3. Measure extraction precision, false confirmations, evidence recall@5, supported-answer correctness, handoff coverage/critical omissions, latency, peak RAM, package/disk size, and failures. Record denominator, hardware, runtime/model/prompt versions, and uncertainty; include failures rather than just average successes.
4. Compare lexical-only retrieval, semantic-only retrieval, hybrid retrieval, and hybrid plus explicit graph/state expansion. Compare template versus local-model handoff. Keep the same fixtures/budgets and report whether the graph actually helped; Graphify branding is not a substitute for evidence.
5. Run the complete desktop journey on each advertised target: install → first-run/startup setting → vault → paste/import → review → source → search/question → task/resume → repo change/freshness → backup/rebuild/restore → restart → uninstall preservation.
6. Run unit/integration/browser/real-desktop checks, keyboard/200%-zoom/high-contrast/reduced-motion tests, crash recovery, repeated long-session cancellation, resource cleanup, and observed offline behavior. A mocked browser test cannot certify native packaging or real LLM accuracy.
7. Fix critical failures and rerun affected plus regression checks. If a model or target fails the acceptance gate, do not lower claims or silently enable cloud AI: resolve a documented model/scope/platform change with the user.

| File | One-line creation/change |
| --- | --- |
| `schemas/evaluation.schema.json` | Define gold labels, evidence expectations, model/runtime provenance, and measured results. |
| `evals/development-cases.jsonl` | Store labelled tuning cases separate from release evaluation. |
| `evals/heldout-questions.jsonl` | Store at least 30 human-reviewed questions with exact evidence/abstention expectations. |
| `evals/heldout-handoffs.jsonl` | Store interrupted-task cases with required decisions/questions and critical replacements. |
| `tools/eval-memory.py` | Run extraction/retrieval/answer/handoff variants and produce reproducible detailed scores. |
| `tools/verify-release.py` | Check manifests, licenses, evidence links, supported-target records, and pending release gates. |
| `playwright.config.ts` | Configure the verified browser test environment with explicit synthetic/real-backend distinctions. |
| `tests/e2e/full-journey.spec.ts` | Exercise the complete synthetic UI recovery journey and persistence/error flows. |
| `docs/evaluation-report.md` | Report measured results, comparison variants, failure examples, hardware, and limitations. |
| `docs/verification/release.md` | Link all step evidence and per-target real installer/Desktop acceptance results. |

Exit gate: all applicable Section 7 thresholds pass; critical approval/integrity/privacy/durability failures are zero in their test suites; every supported-target claim is backed by actual tests. Publication still follows the user's release decision, not this checklist alone.

### Step 26 — Preserve deferred work without adding first-release dependencies

Prerequisite: the first-release scope is stable; future entries are not implementation authorization.

1. Keep Jev / Decision API as a future experiment for classification/contradiction/ranking. Before any use, recheck official API capabilities/prices/data handling, request optional cloud-mode approval, and compare with the local baseline. No Jev key, package, HTTP call, or hard dependency enters the first iteration.
2. Explore direct ChatGPT integration only after G08: verify supported client/account features, transport, authentication, scoped permissions, revocation, actual local/tunnel/remote behavior, data sharing, and costs. Do not expose the whole vault on an unauthenticated endpoint or claim a developer tunnel meets public release requirements.
3. Evaluate supported conversation-capture hooks/export adapters separately for each assistant. No browser credential scraping, hidden background capture, or assumption that an assistant memory file automatically records all conversations.
4. An optional npm package would be a CLI/launcher for a tested installed native runtime, not a claim that npm installs offline WebView2, Python bundles, or Mac signing. Verify registry naming, packaging, install paths, and limitations before proposing publication; never publish automatically.
5. Keep sync/encryption/mobile/OCR/audio/Canvas/plugin compatibility and larger vector indexes as separately estimated roadmap items with explicit privacy and storage-migration designs.

| File | One-line creation/change |
| --- | --- |
| `docs/roadmap.md` | Record deferred items, user benefit, prerequisites, uncertainty, scope, and evaluation criteria. |
| `docs/experiments/jev.md` | Record the future Jev hypothesis, optional-cloud consent gate, and local-baseline comparison design. |
| `docs/experiments/chatgpt-connector.md` | Record future official transport/auth/account constraints and privacy/cost gates. |
| `docs/experiments/npm-distribution.md` | Record the optional native-runtime launcher proposal and verified registry/OS limitations. |

Exit gate: deferred features are visible and explicitly excluded from first-release dependency/configuration files. No future connector or API is activated during roadmap writing.

## 9. Shared registration changes and file completeness

The per-step tables list feature-specific files. These existing cross-cutting files also change when the step needs them; record actual edits in that step's ledger, not as silent additions.

| File | Exact shared change when applicable |
| --- | --- |
| `sidecar/memory_worker/service.py` | Register the step's permitted UI methods, validators, jobs, and handlers; never expose arbitrary worker functions. |
| `sidecar/memory_worker/contracts.py` | Load/register added schemas and validate the step's actual external payloads. |
| `schemas/ipc.schema.json` | Add the step's permitted method/result/event variants with versioned bounded payloads. |
| `schemas/settings.schema.json` | Add only the step's typed preferences and documented defaults; distinguish vault from machine-local settings. |
| `src/app/core/contracts.generated.ts` | Regenerate schema-derived types; do not manually drift them away from schemas. |
| `src/app/core/memory-gateway.ts` | Add typed methods/capabilities for the completed feature only. |
| `src/app/core/tauri-memory-gateway.ts` | Map new methods/events to the verified native transport and normalize errors. |
| `src/app/core/demo-memory-gateway.ts` | Add labelled synthetic behavior for browser UI tests, never pretending it is actual inference. |
| `src/app/app.routes.ts` | Register completed screens and guard unavailable features. |
| `src/app/app.component.html` | Add accessible navigation/actions only for verified capabilities. |
| `src/app/app.config.ts` | Register required feature providers without global side effects or hidden network access. |
| `src-tauri/src/lib.rs` | Register actual native modules/commands/plugins with bounded application state. |
| `src-tauri/src/commands.rs` | Expose only the step's needed validated native commands. |
| `src-tauri/Cargo.toml` and `src-tauri/Cargo.lock` | Add and lock only verified native dependencies actually introduced by the step. |
| `package.json` and `package-lock.json` | Add and lock only verified UI/build dependencies actually introduced by the step. |
| `sidecar/pyproject.toml` and `sidecar/uv.lock` | Add and lock verified compatible Python dependencies, separating runtime and developer extras. |
| `sidecar/memory_worker/migrations/002_feature_indexes.sql` | Add cumulative verified cache indexes/fields for later features; use a new numbered migration if 002 already shipped. |
| `docs/decisions.md` | Record each material choice with evidence and genuine approval when needed. |
| `docs/implementation-status.md` | Record step status, exact changed/generated paths, passed/failed checks, blockers, and next action. |
| `docs/verification/step-NN.md` | Record commands/checks, environment, real outcomes, manual observations, and unresolved limits for that numbered step. |

For helper files, component unit tests, mock assets, platform packaging support, or dependency hooks not known until the scaffold/probe, first add the exact path and one-line responsibility to this plan/status before writing them. Do not invent generator outputs in advance or claim this document is a byte-for-byte implementation specification. Each `.ts` component includes its needed Angular imports, standalone/template declaration, typed state, loading/empty/error behavior, and teardown; each backend module includes validation, structured errors, and relevant tests.

## 10. Two-week demo sequence and full-release follow-through

This is a proposed prioritization, not a promise that the entire product fits two weeks. Treat it as ten focused implementation days with remaining time for evaluation; hardware/access failures can change it. G01 must confirm the scope.

| Day/block | Step subset and concrete demo result |
| --- | --- |
| 1–2 | Steps 00–02: create the approved repo under `D:\Projects`, agree scope, and prove frozen worker/model/Graphify packaging early. |
| 3–4 | Steps 03–07: runnable desktop shell, contracts, recoverable vault, rebuildable index, and basic Markdown notes. |
| 5–6 | Steps 09–12: links/evidence, paste import, local candidates, explicit decision review, and manual tasks. |
| 7–8 | Steps 13–15: grounded search/question and accurate reviewed resume/copy-export package. |
| 9 | Demo subset of Steps 16/21: one synthetic repository and bounded graph/list, plus an approved minimal logo/icon. |
| 10–14 | Demo subset of Steps 22–25: backup proof, one Windows installer, README/sample, held-out evaluation, defect buffer. |

Attachments, provider-specific exports, templates/daily startup, full table views, freshness UI, local MCP, multiple repositories, polished animation, and both Mac packages remain full-release work unless genuinely completed and tested in the demo. The demo must still preserve evidence, explicit approval, privacy, recoverable storage, and honest installer limitations. Never cut these integrity checks to make the calendar look successful.

After the demo, resume the uncompleted numbered steps with their prerequisites. Use the actual status ledger rather than pretending a demo subset marked the whole step verified. Record `demo_subset_verified` in notes while retaining the full step's `in_progress` status until its complete exit gate passes.

## 11. Implementation handoff and stop conditions

Before each step, answer: Which requirement does this change serve? What source establishes the API? Which files will change? What is the unknown? What evidence will prove the user behavior? If any answer is missing, inspect code/docs or ask the user before the affected action.

The next implementation agent begins at Step 00, not by rebuilding the plan from memory. Confirm G10 and G01, create only the approved repository child under `D:\Projects`, preserve this plan/context in its docs, and run the early feasibility checks. An unresolved name/hardware/account/privacy choice is a decision gate, not permission to choose secretly.

A step is not verified if its check was not run, a mocked component replaced the real runtime, source evidence is fabricated, target hardware is untested, or documentation promises a deferred feature. At an unavoidable blocker, stop the affected action, preserve completed work, record the exact evidence/choice needed, and ask a focused question. Do not claim “everything works perfectly” merely because all planned filenames exist.

Final product handoff includes the approved repository/commit, working installers and hashes for verified targets, README/sample, evaluation report, step/release check evidence, known limitations, backup/restore proof, and the future backlog. No app implementation, repository creation, installation, or publication was performed while preparing this plan.

## 12. Primary-source register

Checked for this plan on 2 October 2026. These are source entry points, not dependency locks. Read relevant content/current release source again at implementation and record exact versions/commits in `docs/research.md`; an unopened link is not evidence.

| Topic | Primary source and use |
| --- | --- |
| Repository creation | [GitHub CLI `repo create`](https://cli.github.com/manual/gh_repo_create): approved owner/visibility and local-source remote creation. |
| Angular | [Releases](https://angular.dev/reference/releases), [compatibility](https://angular.dev/reference/versions), [accessibility](https://angular.dev/best-practices/a11y): baseline and version/native-webview checks. |
| Native worker | [Tauri sidecars](https://v2.tauri.app/develop/sidecar/), [resources](https://v2.tauri.app/develop/resources/), [PyInstaller](https://github.com/pyinstaller/pyinstaller): native bundled runtime layout. |
| Installers | [Windows](https://v2.tauri.app/distribute/windows-installer/), [DMG](https://v2.tauri.app/distribute/dmg/): target-native offline packaging. |
| Signing/startup/icons/updates | [Windows signing](https://v2.tauri.app/distribute/sign/windows/), [Mac signing](https://v2.tauri.app/distribute/sign/macos/), [autostart](https://v2.tauri.app/plugin/autostart/), [icons](https://v2.tauri.app/develop/icons/), [updater](https://v2.tauri.app/plugin/updater/): actual platform behavior and limits. |
| Local inference | [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md): local runtime capabilities and secured process launch. |
| Generation models | [Qwen 1.7B GGUF](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/tree/main), [Qwen 0.6B GGUF](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/tree/main): official candidate files and licenses. |
| Embeddings | [BAAI BGE small](https://huggingface.co/BAAI/bge-small-en-v1.5), [ggml GGUF conversion](https://huggingface.co/ggml-org/bge-small-en-v1.5-Q8_0-GGUF): model behavior and conversion provenance. |
| Repository graph | [Graphify](https://github.com/Graphify-Labs/graphify), [v8 manifest](https://github.com/Graphify-Labs/graphify/blob/v8/pyproject.toml), [PyPI metadata](https://pypi.org/pypi/graphifyy/json): version discrepancy, code-only probe, dependencies/license. |
| Search | [SQLite FTS5](https://sqlite.org/fts5.html): lexical indexing/ranking; semantic fusion in this plan is an app decision. |
| Editor/visuals | [CodeMirror Tab behavior](https://codemirror.net/examples/tab/), [Three.js WebGL](https://threejs.org/docs/pages/WebGL.html), [ScrollTrigger](https://gsap.com/docs/v3/Plugins/ScrollTrigger/), [GSAP license](https://gsap.com/community/standard-license/): keyboard, capability, animation, and license checks. |
| MCP | [Python SDK](https://github.com/modelcontextprotocol/python-sdk), [security guidance](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices): pinned API compatibility and protocol/security boundaries. |
| Claude | [Claude Code MCP](https://code.claude.com/docs/en/mcp), [memory](https://code.claude.com/docs/en/memory): local-client integration and instruction-file behavior, not universal capture. |
| ChatGPT | [OpenAI MCP server guide](https://developers.openai.com/plugins/build/mcp-server), [quickstart](https://developers.openai.com/plugins/build/app-quickstart): actual supported integration/transport/auth constraints. |
| Plain language | [ASD-STE100 overview](https://asd-ste100.org/about_STE.html): likely recalled standard, subject to user confirmation. |
| Familiar note features | [Obsidian help](https://obsidian.md/help), [privacy/pricing](https://obsidian.md/pricing): honest baseline, not proof of exclusive differentiation. |

## 13. Plan preparation verification

This plan was checked for consecutive steps 00–26, coverage of R01–R23, explicit pending gates, per-step file responsibilities and exit checks, separation of demo/release/future scope, and the user's `D:\Projects` location instruction. The checks validate the planning document, not the unbuilt application. `SESSION_CONTEXT.md` accompanies this plan to preserve the recovered conversation and later instructions.
