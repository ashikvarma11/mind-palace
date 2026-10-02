# Native shell subset — 2 October 2026

Story: the locally built Windows desktop app loads bundled Angular assets, renders the approved sample-only interface, answers a permitted native health call, reloads a route and exits cleanly. This does not connect a vault or AI.

## Actual results

- Pinned **Tauri 2.12.1**, **tauri-build 2.7.1**, npm CLI **2.12.1**; Rust transitive resolution recorded in a source lockfile, not a distribution approval.
- `cargo build --locked --manifest-path src-tauri/Cargo.toml --features custom-protocol` through `tools/run-native.py`: passes. Initial full compile **5m 37s**; final incremental compile **12.72s**. Final development executable **14,911,488 bytes**, not installer size.
- One Rust health-state test passes; explicitly returns `desktop_shell_only: storage_disconnected, ai_disabled`.
- Final `npm run check`: **9 Angular unit tests pass**, production browser build passes, initial JS/CSS total **328.92 kB**.
- Existing worker source/frozen regression: **31/31 pass**, no skips, **10.723s**.
- Diagnostics plus new archive safeguards: **26/26 pass**, no skips, **8.346s**. Fake credential tests use fresh temporary diagnostic entries and remove them. This does not use actual API keys or rerun AI inference.
- Total **67 unit/integration checks**, plus separate real native WebView smoke. Counts are software checks, not AI-answer quality.

Native smoke output:

```json
{"rendered":true,"native_health":"desktop_shell_only: storage_disconnected, ai_disabled","unknown_key_command_denied":true,"route_reload":true,"console_errors":[],"graceful_exit":true}
```

`tools/verify-native-shell.mjs` launches only the locally built executable with a new ignored WebView profile and temporary loopback CDP debugging. It verifies the opening/empty state, actual JS-to-Rust health response, absent key-read command, fictional sample session navigation, route reload, computed grid styling, a response nonce and normal window close. Unknown command rejection does not certify a production credential backend, which does not exist yet.

Screenshot: `.tools/native/verification/native-opening.png` (ignored, inspected visually). The approved design and supplied artwork render correctly. Final process checks found no remaining Mind Palace process or probe-profile WebView processes. Debugging is supplied only to the test child; normal launch enables no debugging endpoint. Native network tracing, all-route desktop coverage, accessibility/zoom and clean-machine testing remain pending.

## Failures discovered and corrected

1. Test attached before the local target URL was ready: added bounded target readiness, no arbitrary foreign-page attachment.
2. Immediate URL equality after a click raced Angular routing: replaced it with Playwright's awaited URL assertion.
3. Visual check exposed missing component styles. Tauri's injected style nonce causes browsers to ignore `unsafe-inline`; Angular's dynamically inserted styles lacked that nonce. Added an inert bundled style marker and passed its per-response `.nonce` through Angular's `CSP_NONCE` token. Removed `unsafe-inline`; kept Tauri CSP modification enabled. Verified nonce use, grid layout, screenshot and zero console errors after rebuilding. No static production nonce or disabled CSP introduced.

Compiler emits a linker informational warning about creating the library/import object. Build/test return success; the warning is retained, not hidden.

## Local generated icons

Pinned Tauri CLI converted the supplied raster mechanically into ignored `src-tauri/icons/`: `icon.png`, `icon.ico`, `icon.icns`, `32x32.png`, `64x64.png`, `128x128.png`, `128x128@2x.png`, `StoreLogo.png`, and `Square30x30Logo.png`, `Square44x44Logo.png`, `Square71x71Logo.png`, `Square89x89Logo.png`, `Square107x107Logo.png`, `Square142x142Logo.png`, `Square150x150Logo.png`, `Square284x284Logo.png`, `Square310x310Logo.png`.

Generator also produced `ios/AppIcon-20x20@1x.png`, `AppIcon-20x20@2x.png`, `AppIcon-20x20@2x-1.png`, `AppIcon-20x20@3x.png`, corresponding `29x29` and `40x40` four-file sets, `AppIcon-60x60@2x.png`, `AppIcon-60x60@3x.png`, `AppIcon-76x76@1x.png`, `AppIcon-76x76@2x.png`, `AppIcon-83.5x83.5@2x.png`, `AppIcon-512@2x.png`; Android `mipmap-hdpi`, `mdpi`, `xhdpi`, `xxhdpi`, `xxxhdpi` directories each contain `ic_launcher.png`, `ic_launcher_foreground.png`, `ic_launcher_round.png`, plus `android/mipmap-anydpi-v26/ic_launcher.xml` and `android/values/ic_launcher_background.xml`. All remain local/ignored. Generation does not establish Mac/mobile support or artwork distribution rights.

## Remaining gates

No Python worker supervision, native vault dialog or durable UI connection; no production key backend, provider HTTPS/cancellation, live AI call, local model selection, single-instance handling or installer. `dev.mindpalace.local` is a development identity only. Full Step 03/04/05 exit gates remain incomplete. Next: trusted bundled-worker resource resolution/supervision and real vault UI, then secure opt-in cloud transport under `cloud-ai-plan.md`. No provider request, real credential access or public push performed here.
