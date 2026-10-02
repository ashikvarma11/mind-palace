# Project handoff context

Mind Palace is an installable, private personal memory application. Its focus is accurate recovery of unfinished work, with exact source evidence and distinctions between proposals and user-approved decisions. Session records are individual; decisions can link across sessions and keep their history.

Approved: Mind Palace name, public MIT code repository, Workspace design, supplied temporary artwork, local-first Angular/Tauri/bundled-Python/local-AI baseline, Windows testing first. The user authorized implementation after reviewing the UI.

Scope and step checks are in `implementation-plan.md`. Use synthetic data for development. Never publish the user's attached conversation, actual imported memory, private paths, or credentials as sample data. Jev and direct cloud connectors are deferred.

Current stage: verified browser shell and Windows frozen runtime/Graphify/MCP diagnostics. Two checksum-verified Qwen models run on authenticated loopback CPU inference but failed the first ten-case quality probe; no production model selected. Continue model-independent foundations under G05, not paid/cloud fallback. Graphify/MCP remain diagnostics, not Connections or assistant integration. Native and combined-worker gates remain pending. See implementation-status.md and verification/step-02-models.md. Local commits after initial publication are not automatically public releases.
