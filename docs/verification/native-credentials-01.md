# Native Windows credentials — 2 October 2026

Internal foundation only, not an enabled cloud feature. No credential Tauri command, key-entry screen, generic target input, key export, credential enumeration, plaintext file fallback or provider request is added. The existing desktop vault works separately.

## Implemented boundary

Windows Credential Manager generic entries with local-machine (not enterprise-roaming) persistence. Production development namespace is native-owned; provider enum permits only openai/anthropic. Status returns presence only; native read returns a non-Clone/non-Serialize Secret with always-redacted Debug. Secret owns Zeroizing bytes, limited to 16–2048 printable non-space ASCII bytes; no unverified provider prefix rule. Caller copies are not magically erased.

CredRead allocation is freed once and its bounded secret blob wiped first. Existing type/target/owner marker/persistence/size/ASCII format is verified. Save requires explicit replacement when an existing valid entry is found; malformed entries are preserved by both save and remove. Missing entries are handled idempotently; other OS failures fail closed. Operations share a process mutex, not a cross-process atomic compare-and-swap or app-exclusive same-user permission boundary.

Dependencies: existing windows-sys 0.61.2 now directly requests Windows Foundation/Credentials; zeroize 1.9.0 added with registry checksum and default alloc, no serde/derive feature. Cargo also resolves dirs-sys to the already-present windows-sys 0.61.2. Official API/source inspection is in research.md.

## Actual tests

- Initial focused credential run: 3 passed, 0 failed, eight unrelated tests filtered; 0.05 seconds. Then malformed-entry protection added.
- Full `npm run test:rust`: 12 passed, 0 failed, no skips, 34.11 seconds, including four credential tests and all prior transport/storage/lifecycle checks.
- Fake native OS tests use fresh MindPalace/native-test/UUID/provider targets; the production constructor does not exist in test builds. No existing real credentials are enumerated/read/modified. Two providers round-trip, another Store instance reads the same stored fake value, implicit replacement is rejected, explicit replacement succeeds, removal and repeated removal succeed, absence verified. Cleanup guards run during unwind too.
- A fresh synthetic short malformed blob is deliberately written through the test's raw adapter. Public save/remove reject it; status still reports invalid format, proving it remains. Raw cleanup deletes only this fixture and absence is verified. Temporary entries were removed; no real keys/provider calls.
- Provider allowlist, target construction, length/control/space/non-ASCII rejection, exact minimum/maximum length and debug/error redaction are checked. Owned-buffer wiping follows inspected zeroize/Win32 code; no unsafe read-after-free memory test is claimed.
- `npm run build:desktop` succeeds; verified 109-file / 23,673,882-byte staged worker unchanged. Existing AJV CommonJS optimization, linker informational and npm config warnings remain. No frontend changes; prior thirteen Angular/seven browser tests were not rerun in this credential-only slice.

Final `npm run verify:desktop` passes: native create/save/read/reopen/reload/restart, inert script-like original text, malformed/unknown commands rejected (including read_api_key), CSP nonce/styles correct, no console errors, idle/busy exit stops both owned workers. Screenshot inspected with real source/list/forms visible and unchanged branding. Preferred agent-browser executable is absent; existing Playwright verifier follows the browser skill using only an isolated synthetic vault/profile and owned processes. The browser skill prompted this actual desktop regression check; no real credential access occurs in the app.

## Remaining gates

No live provider API compatibility, AI quality, macOS Keychain, logoff/relogin/reboot persistence, hostile same-user isolation, memory-dump/swap protection or concurrent cross-process replacement guarantees. Store reconstruction is not an OS reboot test. Generic local-machine entries remain available to this user's sessions on this computer. Release identity/migration, native cancellation, masked key-entry/no-key-export UI, exact sharing consent, allowlisted HTTPS, mocks/fake credential errors and later explicitly authorized live checks remain pending. No fees, subscriptions or cloud fallback.
