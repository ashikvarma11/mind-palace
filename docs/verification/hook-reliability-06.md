# Codex reliability 06 — stale-prefix, spool and chunk storage

3 October 2026. Windows 10 build 19045 x86-64; Python 3.12.10; PyInstaller 6.22.3. All transcript content was synthetic. No private session, installed hook, global setting, paid call, commit, push or release operation was used.

## Reproduced defect

A temporary diagnostic created one 36-character prefix and a later 280,236-character revision for the same provider/session key. Before the correction, the import plan returned the 36-character prefix as its candidate, reported one revision, and returned `skipped:0`. The large latest revision had been removed before group selection. No workspace file was changed by this diagnostic.

## Correction

`capture_control.import_plan` now records every provider/session group that contains a snapshot above the current canonical byte guard. The complete group is skipped and counted once. It cannot offer an older prefix as current. Raw inbox revisions remain unchanged.

This is temporary fail-closed behavior. It does not implement D028's complete 20 MiB segmented import. A large Session remains unavailable in the canonical vault until the next storage step.

## Verification

Focused regression after the environment correction:

```text
Ran 1 test in 0.415s
OK
```

Complete capture-ingestion file:

```text
Ran 4 tests in 2.397s
OK
```

Complete source Python suite:

```text
Ran 95 tests in 23.074s
OK (skipped=4)
```

The four skips require selected frozen executables. The focused packaged run then selected the rebuilt staged receiver and covered frozen app control, frozen hook/memory/index, and the stale-prefix regression:

```text
Ran 3 tests in 4.609s
OK
```

PyInstaller rebuilt the Windows onedir receiver because `capture_control.py` changed. The staged inventory check passed:

```json
{"files":70,"bytes":22705870,"checked":true,"executable":"memory-capture.exe"}
```

Staged executable SHA-256:

```text
B85D7E63170AF807279038AEBDD9C62992E45C30A5BB77FD8E41BB8CEB5E35EB
```

`git diff --check` passed. It emitted only existing CRLF-to-LF checkout warnings for three documentation files.

## Next gate

The stale-prefix, unique-spool and chunk-manifest storage items are complete at the tested source and frozen boundaries. Complete large-session vault ingestion is not complete because the canonical import transport still has a 65,536-character guard.

## Unique hook spool and app-side memory scan

The hook now writes one UUID-named spool record through a flushed same-directory temporary file. It does not take `capture.lock`, deduplicate, rebuild the index or scan memory roots. The app-side index operation holds the lock, validates spool records, deduplicates equal transcript revisions, and scans memory roots only when their separate consent remains enabled.

Focused source checks covered two simultaneous hook processes, capture while another process held `capture.lock`, pause and scope validation, damaged spool handling, lifecycle deduplication, app control, and memory scan placement:

```text
Ran 31 tests in 5.426s
OK (skipped=2)
```

The first complete source run found two old lifecycle-fixture assertions that searched only the former direct snapshot path. The receiver had captured the records. The fixtures were corrected to require one spool record per event and one canonical revision after indexing. The next complete run passed:

```text
Ran 97 tests in 23.145s
OK (skipped=4)
```

## Schema 2 chunks and manifests

New canonical inbox revisions contain an ordered schema 2 manifest. Transcript bytes are stored in SHA-256-addressed `.jsonl` chunks. The target is 65,536 bytes, with boundaries only after complete JSONL records. One indivisible record can exceed the target within the existing 1 MiB record guard. Readers reconstruct the ordered bytes, validate each chunk hash and length, validate JSONL records, and verify the complete transcript hash. Schema 1 snapshots remain readable.

Focused source checks covered exact reconstruction, record boundaries, chunk tampering, spool tampering, lifecycle deduplication, canonical ingestion and the stale-prefix guard:

```text
Ran 23 tests in 9.211s
OK (skipped=2)
```

An earlier focused run recorded four errors: one test still tried to edit the removed embedded `transcript` manifest field, and three child-process startup checks timed out. The test was changed to damage the referenced chunk. One isolated child-process run then passed in 0.661 seconds, and the complete focused run above passed. No third retry of the failing combined command was used.

The final complete source suite includes a frozen-only lock-held hook check and passed:

```text
Ran 99 tests in 24.841s
OK (skipped=5)
```

PyInstaller 6.22.3 rebuilt the Windows x86-64 receiver with Python 3.12.10. Staging and inventory verification passed:

```json
{"files":70,"bytes":22709388,"checked":true,"executable":"memory-capture.exe"}
```

Staged executable SHA-256:

```text
BA830929FC934B747DCECDDCF82DE779BBC217E1CD5235EE47B31C31AE848EFF
```

The first selected packaged command named a test method that does not exist; the other three selected tests passed before unittest reported that loader error. The final selection passed frozen capture while `capture.lock` was held, frozen hook/memory/index with schema 2 reconstruction, and generated Codex/Claude Code app control:

```text
Ran 3 tests in 4.074s
OK
```

Three packaged `SessionEnd` deadline probes all passed the 3000 ms limit with empty stdout:

```json
{"runs":3,"successful":3,"empty_stdout":3,"within_deadline":3,"median_ms":182.691,"p95_ms":199.148,"maximum_ms":199.148,"durations_ms":[199.148,180.986,182.691],"result":"pass"}
```

## Remaining gates

- The quota and failure-marker boundary was pending at this point; the later section records its implementation.
- Redundant prefix retention and safe pruning remain pending a verified import acknowledgment.
- Complete large-session canonical import still stops at the existing 65,536-character guard.
- No installed user hook or private transcript was changed or read in this step.
- The controlled one-hour Codex acceptance test remains pending.

## Inbox health, quota and first visible status — 3 October 2026

Hook preflight now checks the last exact app-side byte count plus current spool files against 1 GiB and keeps 1 MiB available for diagnostics. A missing health record uses one bounded migration scan. Content-free failure markers contain only provider, lifecycle event, safe code and UTC time. A focused test verifies that a quota failure writes no transcript record and that its marker contains no session ID, transcript path or sample content.

The Connections screen now displays inbox use and limit, pending spool count, failure count, 30-day retention target and last validation time. It states that pruning waits for a verified import receipt. No retention deletion is active yet.

Focused backend:

```text
Ran 34 tests in 5.667s
OK (skipped=3)
```

Complete backend:

```text
Ran 100 tests in 29.085s
OK (skipped=5)
```

Angular with the project-compatible Node runtime:

```text
Test Files  6 passed (6)
Tests       27 passed (27)
```

The production Angular build passed with the existing two AJV CommonJS optimization warnings. Generated contract check and `git diff --check` passed; the latter emitted only checkout line-ending warnings.

The frozen receiver was rebuilt and staged:

```json
{"files":70,"bytes":22714111,"checked":true,"executable":"memory-capture.exe"}
```

Staged executable SHA-256:

```text
C595FB1ADA1346872E21ADD19C7F64E03BC46F6370A1EB71DD02BD72EC033845
```

Selected packaged checks passed in 4.717 seconds. Three packaged deadline runs measured 182.965–199.749 ms and all passed the 3000 ms limit with empty stdout.

Native tests were attempted by two methods. The npm entry failed because this checkout does not contain `node_modules/npm/bin/npm-cli.js`. Direct `tools/run-native.py cargo test` then stopped because the ignored project-local Rust compiler component is missing from this worktree. Per the two-attempt rule, no third approach was used. No native compile or desktop visual-run claim is made for this UI change.

Next: after each successful vault import, publish a validated inbox acknowledgment. Then test 30-day redundant-prefix pruning and unreferenced-chunk cleanup while preserving the newest and every unimported copy. Add repair and failure-detail controls after that boundary is proven.
