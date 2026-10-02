# Implementation research

## Cloud/storage foundation — 2 October 2026

OpenAI Docs skill used to search/fetch current official text generation, response fields, token limits and data policies before the provider contracts. No platform-key tool was available and no real key was read/requested. Direct adapters fit the approved native/Python architecture; inspected the AI SDK skill but did not add its JavaScript SDK, gateway or agent loop for these pure contracts.

Fetched sources: https://developers.openai.com/api/docs/guides/text (input/instructions/output message traversal), https://developers.openai.com/api/reference/cli/resources/responses/methods/create (store, max_output_tokens, status/usage), https://developers.openai.com/api/docs/guides/token-counting (output includes hidden reasoning tokens), https://developers.openai.com/api/docs/guides/your-data (store:false is not universal zero retention). The raw HTTP reference exceeded the fetch tool's size limit; fetched official guide/CLI reference instead. No CLI/provider executable was invoked. Model IDs are synthetic in tests; actual model selection remains pending.

Fetched https://platform.claude.com/docs/en/api/messages/create and overview for messages/system/max_tokens/content/stop_reason/usage and anthropic-version 2023-06-01. Requests have no tools, cache-control directives, streaming, credentials or HTTP transport. Providers receive only explicit snippets when a later native sending implementation is enabled; tests currently send nothing.

Fetched Microsoft https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew, nf-wincred-credreadw, ns-wincred-credentialw and nf-wincred-creddeletew; inspected structure fields, generic/session constants and required CredFree cleanup. Real diagnostic touched only its newly generated target with fake random bytes, then verified removal. No credential enumeration or existing provider key access. This Python diagnostic does not replace the planned Rust production backend.

Rechecked https://v2.tauri.app/start/prerequisites/: Windows requires Rust, C++ tools and WebView2. cargo/rustc unavailable; vswhere reports no C++ tool component. No admin/global installer activated. Inspected installed jsonschema 4.26.0 FormatChecker.checks and discovered optional date-time checker absent; registered local UTC-Z validation with calendar checks. PyInstaller 6.22.3 help confirmed add-data SOURCE:DEST and source/schema bundle paths; verified frozen behavior. See verification/cloud-foundation-01.md for measured checks and pending gates.

Checked: 2 October 2026. Versions below come from registry/tool output, not memory.

| Source                                       | Finding and use                                                                                                                                                                      |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| https://cli.github.com/manual/gh_repo_create | `--public --source --remote` creates the approved public repo and connects the existing local Git root. Verified remote: https://github.com/ashikvarma11/mind-palace.git.            |
| https://angular.dev/reference/versions       | Angular 22 supports Node ^24.15.0; installed Node 24.16.0 is compatible. Registry Angular core/CLI/build report 22.2.1; inspect generated package compatibility before locking.      |
| https://angular.dev/cli/new                  | Standalone client-only scaffold with routing and SCSS; use the pinned generator and inspect actual filenames/build/test runner.                                                      |
| https://v2.tauri.app/start/prerequisites/    | Windows native builds need Rust MSVC and Microsoft C++ build tools. Rust/cargo not in PATH; vswhere C++ component probe returned no installation. Desktop readiness is not verified. |

No claim of tested model inference, worker freezing, or Graphify extraction yet. Registry and source snapshots/hashes for those dependencies are pending Step 02.

## Verified browser subset

- Pinned @angular core/CLI/build/compiler family 22.2.1; TypeScript 6.0.2, RxJS 7.8.2, tslib 2.8.1, Vitest 5.0.0, jsdom 30.0.0, @playwright/test 1.63.0, @lucide/angular 1.49.0. The installed package lock is authoritative; install and builds verified compatibility.
- https://angular.dev/guide/signals — writable/read-only/computed signals; sample state is explicit and in-memory.
- https://angular.dev/guide/routing/define-routes — typed routes, lazy component loading and route data; actual router declarations/build verified `withComponentInputBinding`.
- https://angular.dev/guide/testing — scaffold uses @angular/build:unit-test with Vitest, not Karma. `ng test --watch=false` was actually run.
- https://lucide.dev/guide/angular/getting-started — @lucide/angular is the current standalone/signal package. Legacy lucide-angular 1.0.0 peers stop at Angular 21, so it was not installed. Verified new package peer range >=17 and actual standalone/dynamic declarations in installed source.
- https://docs.github.com/en/account-and-profile/reference/email-addresses-reference — ID-based no-reply commit identity selected from verified public GitHub account ID; local repository configuration only, no personal email published or global preference changed.
- Prototype bundling uses only local assets/system fonts. No third-party runtime network requests occurred in the tested browser sample flow; this does not certify the future native runtime.

Scaffold generated safely in ignored `.tools/scaffold` because the generator refused to merge the pre-existing README; only enumerated new source/config files were adopted. Existing repository guidance/privacy exclusions were preserved.

# Step 02 diagnostic packaging research — 2 October 2026

## Local generation follow-up — 2 October 2026

Inspected official llama.cpp b11342 release API/digest and executed downloaded Windows CPU binary version/help. Pinned docs https://raw.githubusercontent.com/ggml-org/llama.cpp/b11342/tools/server/README.md establish host binding, LLAMA_API_KEY, disabled webui/agent/proxy flags, schema-constrained response_format and chat_template_kwargs.enable_thinking. No OpenAI SDK/cloud provider is used; compatible endpoint names are implemented by the local runtime. Official Qwen cards https://huggingface.co/Qwen/Qwen3-0.6B-GGUF and https://huggingface.co/Qwen/Qwen3-1.7B-GGUF identify Apache-2.0; model API blobs supply exact revisions/size/LFS SHA256, independently checked after download. Metadata/artifact locks are in config/models.json.

Windows peak working-set implementation follows https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo and https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters, with a limited-query process handle and explicit CloseHandle. Measurements/evidence grading limits are in verification/step-02-models.md; low prototype case scores are preserved and neither candidate is selected. No recommendation or release-quality claim is inferred from local runtime startup.

## MCP follow-up — 2 October 2026

Official https://github.com/modelcontextprotocol/python-sdk and https://py.sdk.modelcontextprotocol.io/run/ describe v2 MCPServer.run(transport="stdio"). https://py.sdk.modelcontextprotocol.io/client/transports/ documents Client(StdioServerParameters(...)); https://py.sdk.modelcontextprotocol.io/get-started/testing/ distinguishes in-memory tests from real stdio. Inspected installed 2.2.0 signatures and mcp_types/version.py before coding. Actual source stdio negotiations: legacy 2025-11-25, auto 2026-07-28; frozen test exercises legacy only. Registry wheel SHA256 was independently verified after download; GitHub v2.2.0 resolves to 9972c21aa42054fb1450c5fc614761ed11847ec6, without whole-tree equivalence claims. Dependencies installed as binary wheels into the isolated environment; exact versions recorded. No SDK CLI/provider/assistant install path used; OpenTelemetry disabled with exporters none. This is a synthetic compatibility probe, not Step 20 memory integration.

## Graphify follow-up — 2 October 2026

Inspected the official PyPI 0.9.73 metadata and downloaded wheel; SHA256 verified against https://pypi.org/pypi/graphifyy/0.9.73/json. GitHub tag v0.9.73 resolves to ef4450d9c28acb2b8cdc22d369c1777b77148eef. Tagged graphify/extract.py (https://raw.githubusercontent.com/Graphify-Labs/graphify/ef4450d9c28acb2b8cdc22d369c1777b77148eef/graphify/extract.py) and wheel copy have matching SHA256 3b890815cb679cbe052e74d23af20af6e38dd88fd26409f289b462d632d9fee6. Whole-tree equivalence is not asserted. Artifact provenance is recorded in config/dependency-manifest.json.

Inspected extract(paths, cache_root=None, \*, root=None, parallel=True, ...) and its returned nodes/edges/input_tokens/output_tokens/failed_sources/extracted_sources. Used parallel=False and explicit root/cache_root to avoid worker subprocesses and fixture writes. Observed source_file, source_location, \_origin and edge confidence values; retained INFERRED on the known cross-file call. Query logging source confirms GRAPHIFY_QUERY_LOG_DISABLE=1 takes precedence. CLI \_run_cli refreshes stale installed skills before even help/version; no CLI command was executed. Its help text was inspected in source, not treated as executed evidence. No assistant configs were modified. Default dependencies installed from binary wheels only; no provider/MCP extras or compilers used.

Checked PyPI metadata and installed packages for PyInstaller 6.22.3 (Python >=3.8,<3.16), jsonschema 4.26.0 (>=3.10), portalocker 4.4.0 (>=3.10). Compatible with the measured Python 3.12.10; exact transitive versions are in tools/requirements-probe-lock.txt. Official sources: https://pyinstaller.org/en/stable/operating-mode.html (onedir includes Python, platform-specific builds); https://python-jsonschema.readthedocs.io/en/stable/validate/ (Draft202012Validator.check_schema/is_valid); https://portalocker.readthedocs.io/en/latest/ (Lock timeout and contention). Inspected actual packaging warning report and ran packaged behavior rather than treating successful freezing as runtime success. No paid API, remote schema resolver, Redis lock or global Python installation was used.
