# Project handoff context

Mind Palace is an installable, private personal memory application. Its focus is accurate recovery of unfinished work, with exact source evidence and distinctions between proposals and user-approved decisions. Session records are individual; decisions can link across sessions and keep their history.

Approved: Mind Palace name, public MIT code repository, Workspace design, supplied temporary artwork, local-first Angular/Tauri/bundled-Python/local-AI baseline, Windows testing first. The user authorized implementation after reviewing the UI.

Scope and step checks are in `implementation-plan.md`. Use synthetic data for development. Never publish attached conversations, actual imported memory or credentials. Jev remains deferred. D013 now approves optional OpenAI/Anthropic user-key inference, off by default with sharing/cost consent; not existing chat-history access and not paid development calls.

Current stage: browser shell, Windows frozen storage/JSONL worker, offline OpenAI/Anthropic request/response contracts and scoped consent previews. Windows fake credential round-trip/deletion verified, not production key backend. 31 worker tests, 19 diagnostics, 7 Angular unit tests and build pass. Two local Qwen candidates remain unselected after quality failures. UI still sample-only, no real AI or vault integration. Native Rust/C++ tools unavailable; no global/admin installer, browser key input or paid call. Next: trusted native supervision/credentials/HTTPS/cancellation under cloud-ai-plan.md, resolving prerequisites safely first. Graphify/MCP remain diagnostics. Local commits are not release publication.
