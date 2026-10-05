# Codex hook contract and installed-client check — 3 October 2026

## Scope

This check used synthetic transcript data only. It did not send a model prompt. It did not read or copy a live Codex transcript. A privacy-safe adapter replaced the live session ID and transcript path before it called the frozen Mind Palace receiver.

Environment:

- Windows 10.0.19045 x86_64.
- Installed `codex-cli 0.160.0`.
- Frozen receiver: `.tools/capture-dist/memory-capture/memory-capture.exe`.
- Official contract: https://learn.chatgpt.com/docs/hooks, checked 3 October 2026.
- Official command flag: https://learn.chatgpt.com/docs/developer-commands, checked 3 October 2026.

## Evidence

Codex fixture test:

```text
D:\Projects\mind-palace\.tools\probe-venv\Scripts\python.exe -m unittest sidecar.tests.test_hook_contracts.HookContractTests.test_codex_lifecycle_fixture_is_captured_as_opaque_jsonl
Ran 1 test in 1.251s
OK
```

The fixture covers documented `SessionStart`, `Stop` and `SessionEnd` fields. The receiver accepted future unknown event metadata, emitted no stdout, saved one immutable record, and preserved the synthetic JSONL bytes and SHA-256 value. It did not copy hook metadata into the transcript record. Codex transcript lines remain opaque because the official page says that the format is not stable.

Frozen deadline probe:

```json
{"runs":3,"deadline_ms":3000,"successful":3,"empty_stdout":3,"within_deadline":3,"median_ms":200.579,"p95_ms":219.793,"maximum_ms":219.793,"durations_ms":[200.579,200.167,219.793],"result":"pass"}
```

The earlier ten-run command finished without returning its report through the command wrapper. It is not counted as evidence. The direct three-run command returned the report above. This timing is a small local sample. It does not guarantee timing under endpoint protection, disk pressure or a large transcript.

Installed-client probe:

- `codex features list` reported `hooks stable true`.
- Strict configuration diagnostics accepted the invocation-level `SessionStart` hook shape.
- The first project-local `.codex/hooks.json` empty-session run produced no event marker and no inbox record.
- A second empty-session run used strict invocation-level hook configuration. It produced `SessionEnd` and one inbox record.
- Safe record metadata: schema 1, provider `codex`, synthetic session ID `codex_installed_probe`, 64 bytes, `normalized:false`, and SHA-256 equal to the record file name.
- The adapter wrote its event marker only after the frozen receiver returned 0 with empty stdout. The handler used `timeout:3`.
- `SessionStart` was not observed. No prompt was sent, so `Stop` was not expected or tested.

## Result and limits

The intended Codex integration works for one controlled installed-client `SessionEnd` event: Codex called the adapter, the adapter called the frozen receiver, and the receiver wrote a valid synthetic inbox record within the configured end-hook limit.

This is partial verification. It does not verify `SessionStart`, `Stop`, project-local or user-level persistent installation, real transcript roots, ongoing-session prefix capture, restart/app-closed behavior, or completeness after a crash. The probe stopped after the second live configuration method, as required. Claude Code was not tested in this step.
