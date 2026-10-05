# Codex native timing and workflow — 4 October 2026

## Scope

Continue from the retained UI setup timeout and large-source failure. Use isolated synthetic folders only. Measure native stages before changing behavior; do not repeat a failed full workflow twice without changing the method. No private transcripts, paid inference, global hook writes or external messages are used.

## Baseline

A standalone `--diagnose-vault` run failed in `capture_import` after **32,205 ms** with `CAPTURE_TIMEOUT`. Earlier operations passed: vault_open 15,615 ms, concurrent capture_status reads, capture_status 1,962 ms, configure 2,004 ms, index 2,191 ms. This does not establish a timeout cause.

Added opt-in `--trace-commands` native stages restricted to a valid isolated debug probe ID. Output contains only stage and elapsed milliseconds; no paths, arguments or source. Release builds do not emit these diagnostics. Native build passed in **1m 11s**, retaining the existing linker warning. The instrumented diagnostic completed all operations, including reopen. Resource verification cost **1,719–1,854 ms**; spawn **3–6 ms**; response frames **171–417 ms**; exit **15–19 ms**. Import took **4,177 ms** before restart and **4,089 ms** after restart. Concurrent status reads passed. This successful run did not reproduce the intermittent timeout.

Changed large-source verification to a focused `--full-size-only` check. Run `1cda55f4-8709-49ad-8f59-4a6d649e154e` passed actual native capture/index/import/list/read for one complete **20 MiB** source with matching SHA-256 and zero console errors. Resource checks remained about 1.7 seconds; the index response frame measured 3,634 ms, import-plan frame 2,919 ms and acknowledgement frame 1,000 ms. This is boundary evidence, not guided setup or installed-client delivery proof.

## Change under verification

Use Cargo's development-package override to optimize sha2 0.10.9 compression at opt-level 3. Keep exact inventory/hash verification for every command, all validation and existing deadlines. This reduces a measured cost; it is not proof that resource hashing caused the earlier timeouts. No cached integrity result or automatic uncertain-write retry is added. Final tests, timing and guided workflow results are pending.


## Final results

- Rust serial suite: **19/19 passed**, 4.00 seconds; test build 39.86 seconds. This includes actual frozen worker persistence/reopen/stop, framing limits, secret redaction, scope/candidate guards and local fake-key OS credential tests. Existing linker warning remains.
- Final native development build: **passed**, 2.82 seconds. Node probe syntax and final diff checks passed.
- Final instrumented full workflow: **passed**, exit 0, isolated run `a7c02329-b777-4361-895c-223be854e967`. Actual WebView/Tauri/frozen receiver/vault worker checks cover guided vault creation, source consent, safe existing-hook merge, explicit runtime trust uncertainty, 390-pixel layout without horizontal overflow, app-closed capture, restart automatic import, exact source, known-session missing-tail repair, Ask on a fresh captured turn, quoted evidence/source opening, title filtering, sync button, explicit history confirmation, one canonical Session per provider/session, complete exact **20 MiB** import/read and hook removal preserving the other hook. Ask also kept stored evidence available during intentionally invalid synthetic capture consent and showed a warning. This is synthetic fixture verification, not paid model generation or a new installed-client duration run.
- Resource checks after SHA-256 optimization measured **100–127 ms** in this full run, versus **1,719–1,854 ms** in the baseline diagnostic. Every call still inventories and hashes the bundle. The 20 MiB index frame took **3,886 ms**, import-plan frame **3,229 ms**, acknowledgement frame **987 ms**. The run completed without timeout or console errors.
- Refreshed native setup, narrow setup, Library and Ask screenshots contain synthetic data. Visually inspected the final narrow setup and Library screenshot. The layout, source paths, fields and source reader remain within their containers.

The guided UI acceptance and 20 MiB boundary now pass on the final executable. The earlier opaque large-source failure and capture timeout remain recorded; the successful run and reduced hashing cost do **not** prove their exact cause or eliminate every intermittent Windows failure. The two-minute **18-of-20** actual-client delivery discrepancy remains open. Runtime user approval still takes place in Codex `/hooks`; the app does not claim to verify it. No release/installer, Mac acceptance, model synthesis or private-content import was performed.
