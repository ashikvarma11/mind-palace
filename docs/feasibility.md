# Feasibility ledger

Browser interface: verified with pinned Angular 22.2.1, Node 24.16.0 and npm 11.17.0. SQLite FTS5/UTF-8 atomic-replace probes: passed on current Windows x86_64 development machine. These measurements do not verify crash recovery or cross-process locking.

Windows diagnostic packaging subset: isolated Python 3.12.10 environment with pinned PyInstaller 6.22.3, jsonschema 4.26.0 and portalocker 4.4.0. An onedir executable passed FTS5, strict synthetic schema rejection, flushed UTF-8 replacement, and cross-process contention/release checks. Bundle: 103 files / 24,841,220 bytes. This is a diagnostic prototype, not the production memory worker or full application.

Pending: artifact hashes/release dependency notices, production frozen worker including MCP/Graphify, local-only Graphify adapter, model selection/speed/RAM/disk, Rust/MSVC native compilation, WebView2/offline packaging, Mac native tests, clean-machine and signing/distribution checks. No paid service or cloud model is a fallback.

Safe engineering default: keep developing tested local foundations; avoid global/admin machine changes or unsupported release claims. User delegated safe/no-cost choices. Use actual measurements before selecting a model or advertising platform support.
