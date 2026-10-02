# Project handoff context

Mind Palace is an installable, private personal memory application. Its focus is accurate recovery of unfinished work, with exact source evidence and distinctions between proposals and user-approved decisions. Session records are individual; decisions can link across sessions and keep their history.

Approved: Mind Palace name, public MIT code repository, Workspace design, supplied temporary artwork, local-first Angular/Tauri/bundled-Python/local-AI baseline, Windows testing first. The user authorized implementation after reviewing the UI.

Scope and step checks are in `implementation-plan.md`. Use synthetic data for development. Never publish the user's attached conversation, actual imported memory, private paths, or credentials as sample data. Jev and direct cloud connectors are deferred.

Current stage: verified browser-shell foundation plus Windows frozen runtime, Graphify and MCP diagnostic probes. Graphify mapped a synthetic TypeScript fixture locally; Connections is still sample-only. MCP diagnostic returns only synthetic status over local stdio; no assistant or memory access is configured. Native/toolchain/model and production combined-worker gates remain pending; see `implementation-status.md` for actual evidence and next action. Local commits after initial publication are not automatically public releases.
