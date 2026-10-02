# Optional cloud AI — approved direction, offline foundation only

2 October 2026. User request: “we need AI model integration like chatgpt or claude … let user integrate them using api keys.” This authorizes an optional bring-your-own-key feature, not access to existing chat accounts/history or paid calls during development. Local-first remains the default; cloud inference necessarily shares selected input with the chosen provider. No automatic fallback from a failing local model.

## Implementation sequence

Engineering subset: implement provider request/response contracts and exact local excerpt previews in the Python worker first, with no credential fields, HTTP client or send method. These pure helpers prepare data for the planned native HTTPS owner; they do not replace it. Preview/preparation may be tested offline before the native prerequisite. Keys, sending, cancellation of actual HTTP and UI enablement remain blocked until the native gateway and OS-backed credentials are verified. This narrows the offline work safely rather than adding a browser proxy.

1. Complete the trusted native-to-worker gateway and request cancellation before accepting credentials. The present browser prototype must not accept or retain real keys.
2. Add provider selection in Settings: Off, OpenAI API, Anthropic API; explain external data sharing and provider charges before enabling it. Local model mode remains separately unavailable until its checks pass. API access/billing is distinct from a Claude chat subscription; do not assume any subscription includes API credits.
3. Resolve and verify OS credential-store access through the native backend on Windows/macOS. Keys must never enter localStorage, vaults, backups, Markdown, URLs, command arguments, logs, or Git. Mask input, allow removal, and fail closed if secure storage is unavailable. Do not substitute plaintext persistence.
4. Add native-only provider adapters: OpenAI Responses API and Anthropic Messages API using documented HTTPS endpoints. Inspect current request schemas and provider data controls before implementation. Allow only known endpoints; reject redirects/custom arbitrary endpoints initially. Credentials are not returned to the webview. User chooses an available model; never silently change providers/models or buy credits.
5. Retrieve locally and show a preview of the exact question and selected source excerpts before the first send. Sending is an explicit user action. Do not upload the vault, scan every file, or send repository paths/secrets by default. Provider retention differs from developer telemetry; disclose it honestly.
6. Bound input/output size, requests and concurrency; no background AI or automatic retries. Display returned token usage when available. Any displayed cost is an estimate using dated official prices, not a guaranteed account-wide billing cap. Provider billing controls remain the user's responsibility. Cancellation does not guarantee that a provider stops billing.
7. Return answers with locally verifiable source identifiers. Provider output is untrusted data, cannot execute tools, modify records or confirm decisions. Unsupported claims must be flagged, and missing evidence must yield an honest abstention.
8. Test adapters with synthetic responses and fake credentials without external inference calls: consent-off rejection, key redaction, endpoint allowlist, failures, timeouts, cancellation, malformed output and unsupported citations. Clearly label these tests as adapter checks, not live provider/quality validation. Live verification stays pending unless a later user explicitly authorizes a potentially charged call.

## Intended file changes (record in the ledger before creation)

- src-tauri/src/credentials.rs — OS-backed credential save/remove/status; never reveal keys to the webview.
- src-tauri/src/cloud_ai.rs — consent-bound, allowlisted HTTPS request ownership and cancellation, secure key lookup and redacted errors.
- schemas/cloud-ai.schema.json — strict provider/model/consent/source/request/token-usage contracts without persisted secrets.
- src/app/features/settings/ai-provider-settings.component.ts/html — show optional provider setup, masked native credential input and billing/privacy explanation.
- src/app/core/ai-gateway.ts — send only validated native requests and report unavailable capability in browser-only mode.
- sidecar/memory_worker/retrieval.py — select bounded local evidence for preview; never read credentials or make cloud calls.
- tests/cloud-ai/ — synthetic consent, credential-boundary, transport, usage and grounding checks; no real keys or paid inference.

Do not create these files yet until the applicable native APIs, repository boundaries and tests are inspected. Exact adapter/library versions remain unselected. This plan does not claim cloud AI works today.

## Official sources checked

The OpenAI Docs skill guided official documentation lookup; no API key was requested, read or used.

- https://developers.openai.com/api/reference/overview — API authentication and secret handling; fetched 2 October 2026.
- https://developers.openai.com/api/docs/pricing — API token charges; fetched 2 October 2026, no prices hardcoded.
- https://platform.claude.com/docs/en/api/overview — Messages API endpoint/authentication; fetched 2 October 2026.
- https://support.claude.com/en/articles/9876003-i-have-a-paid-claude-subscription-pro-max-team-or-enterprise-plans-why-do-i-have-to-pay-separately-to-use-the-claude-api-and-console — Claude subscription does not include API usage; fetched 2 October 2026.
