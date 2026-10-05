# Codex workflow UI — 4 October 2026

## Approved scope and changes

The user asks to proceed with the Codex UI update. The interface now guides vault opening, exact source consent, hook installation and external Codex `/hooks` review, sync, session reading and local questions. Connections includes vault controls and direct Sessions/Ask links. The scope form restores saved values after its initial status read, including paused consent, without enabling capture. A failed status read cannot present its stale installed hook as verified. Runtime trust remains explicitly unchecked in the app; the isolated CLI approval test is not promoted into a current-user status.

Sessions now uses a Library list/reader layout with a filter for loaded titles, visible pagination limits, source inspection and a collapsed manual-paste section. Welcome keeps manual paste open and existing controls available. Ask describes its exact quoted evidence, automatic capture check, abstention and source links. The obsolete “Memory service not connected” banner now distinguishes a closed local vault from the unavailable browser vault. The desktop identifies itself as a development build. Empty import results do not claim all Codex events were delivered.

Sources, consent boundaries, capture limits, keyword retrieval and approval semantics remain unchanged. No private source was read or published. No live user hook was installed by UI tests. All native test data uses isolated synthetic folders. This is an incremental Library reading surface within the existing navigation, not a claim that all future Library redesign features or model summaries are complete.

## Verification

- Final Angular 22.2.1 / Node 24.16.0 unit checks: **35/35 passed**, 11.19 seconds. Three added UI checks cover saved scope restoration, paused consent, blocked sync while the vault is closed, explicit runtime-trust uncertainty and stale-state error display. Service doubles in these tests are not real native verification.
- Final production web build passed, **458.26 kB** initial raw size. Existing AJV CommonJS warnings remain.
- Final native build passed, **10.48 seconds**, with the existing linker stdout warning. Build completed before the native app was launched.
- Final `git diff --check` passed with line-ending normalization warnings only.

## Retained first native attempt

Run `a26a6b4c-910d-4e97-8b2f-c27db8652c5b` passed guided vault creation from Connections, saved consent, hook merge, explicit approval uncertainty, the **390-pixel** overflow check, closed-app capture/restart, exact source recovery, Ask and evidence opening, Library filtering and confirmed history. It later failed inside the separate 20 MiB native index/import/read block with an opaque `page.evaluate: Object`; this is not an all-workflow pass. The probe now records only the failed command and safe error code. The final UI refinements also replace the overconfident empty-import notice and add a folder-jump link. The second full native attempt is recorded below.

Screenshots in `.tools/native/verification/` contain synthetic data only: `codex-setup.png`, `codex-setup-narrow.png`, `codex-library.png`, `codex-ask.png`. The wide setup and Library images were visually inspected. These images are from the first native attempt; they do not prove the final build passed the complete setup flow. The Ask image was also visually inspected. The final build changes the development label, empty-import notice, folder-jump link and input styling.

The earlier actual-client two-minute **18-of-20** event-count discrepancy remains open. UI success cannot prove perfect event delivery, real model synthesis, installer acceptance or Mac support.


## Final native evidence and retained limits

The second full attempt, `023f6da7-0eef-4a48-b58d-981c58905be0`, failed before hook installation. After saving the scope, the app reported `CAPTURE_TIMEOUT` and kept the unavailable status visible instead of showing stale installed state. The expected install button was absent. A write may have completed; no automatic mutation retry was made. This attempt did not reach the 20 MiB block. Its timeout cause is not established. The two failures do not support a complete native setup pass.

Changed verification method instead of repeating the full workflow a third time: `--codex-client-probe .tools/codex-hook-probe/trust-l4b2zrow` passed against the final desktop build, isolated run `920dba7a-1ede-4b91-9635-6ca63207dbb7`. This exercised the actual WebView/Tauri/frozen receiver/vault worker boundary with the earlier normally trusted installed-client fixture: app-closed capture, restart automatic import, exact 41,149-byte source, one canonical Session, and Ask returning SQLite with quoted evidence. Console errors: **0**. Configuration in this focused mode uses native commands, so this is not proof of the final guided setup buttons or runtime user trust approval. The original Codex fixture used fixed local replies, not paid model inference.

UI implementation is present in the final development executable. Production readiness remains unproved: investigate the capture timeout and first full-run 20 MiB failure with bounded command timing before claiming complete setup reliability. Preserve the separate two-minute 18-of-20 delivery discrepancy. No release or installer was published.


Subsequent verification: the final guided workflow and exact 20 MiB boundary passed in run `a7c02329-b777-4361-895c-223be854e967` after measured development hashing optimization. See codex-runtime-13.md for actual stage timings, 19 Rust passes and retained limits. Refreshed screenshots now show the final build. Earlier failures above remain historical evidence.
