# Normal Codex hook trust — 4 October 2026

## Correction and scope

The user did not confirm step 1 as verified. The earlier user-confirmed label was incorrect and is withdrawn. This report tests actual persisted approval with installed Codex CLI 0.160.0, isolated synthetic source/settings/vault data and a loopback fixed-response provider. It does not change or approve normal user capture settings, use paid inference or read private sessions.

## Actual normal review

Probe `trust-l4b2zrow` installed the three generated Mind Palace capture commands without a relay wrapper. The installed app-server's `hooks/list` initially reported three enabled, non-managed, **untrusted** hooks. Its generated JSON schemas were inspected locally. Official documentation: https://learn.chatgpt.com/docs/hooks and https://learn.chatgpt.com/docs/app-server, opened 4 October 2026.

The actual Codex CLI TUI displayed “Hooks need review” and “3 hooks are new or changed.” The review screen showed the source, actual receiver command, ten-second SessionStart timeout and untrusted state. `t` approved that definition. The normal hook browser then approved the two remaining reviewed definitions. No bypass flag, managed policy, manual trusted hash write, or fabricated approval record was used. The TUI wrote its own `[hooks.state]` trusted hashes. The TUI was closed before launching new clients.

Fresh installed-client processes read all three definitions as **trusted**. Two normal `codex exec` turns, using resume for the second, completed without `--dangerously-bypass-hook-trust`. Each selected captured revision matched its exact source. Session `01a1067b-df15-74c1-8a60-3648e6aaa7b6` contains **41,149 bytes**. A separate local vault stored this source and returned cited SQLite evidence. Increasing the isolated Stop timeout changed the installed app-server trust status to **modified**, requiring review again. The probe restored its original definition and removed only its isolated handlers afterward.

Final probe continuation exited 0 and saved `report.json`. Two fresh client turns occurred before the continuation; the continuation used that existing source to finish Ask and hash-change checks, without repeating inference. Normal persisted trust is verified for this installed client and generated handler. It does not establish the user's current global installation status, every event's delivery count, or special-path deadline behavior.

## Discovered installer defect and repair

The reinstall check exposed a real conflict: the installer treated Codex's `[hooks.state]` trust records as inline handler definitions. It now permits the state-only table without changing `config.toml`, while still refusing empty, mixed or actual inline handler tables. The regression test compares exact config bytes across install, removal and reinstallation, then checks mixed definitions remain blocked.

Source controller checks: **9 passed / 1 expected frozen-only skip**, 11.898 seconds. Refreshed frozen controller checks: **10/10 passed**, 6.022 seconds, including actual frozen install/remove/reinstall with saved trust records. Final full source suite: **116 checks / 111 passed / 5 expected frozen-only skips**, 53.018 seconds. PyInstaller 6.22.3 / Python 3.12.10 rebuilt the receiver; staged inventory and final integrity check: **70 files / 22,745,734 bytes**. The unchanged worker inventory remains 111 files / 23,706,282 bytes. The native build passed in 15.09 seconds with the existing linker stdout warning.

Final actual WebView/Tauri/frozen-process check `67875ee6-e18e-41db-a6ec-83184e9d9d2f` **passed, exit 0**. It used the exact 41,149-byte rollout from the no-bypass trusted client, copied only into an isolated test scope. Mind Palace closed before frozen capture, restarted, automatically imported one Session, returned the exact complete source and answered “SQLite local vault” through the Ask UI with quoted SQLite evidence. Console errors: zero. This native capture invokes the configured handler directly; normal persisted approval is separately established by the earlier real TUI/fresh-client checks. No application source edits followed the clean native run. Node/Python syntax checks and final diff checks passed.

## Retained probe failures

- The first check counted the empty TUI review Session together with the generated conversation. The check now selects the intended provider session ID; no source was deleted.
- Reinstall then exposed the real `[hooks.state]` conflict, repaired with source and frozen regression tests.
- The fixture prompt omitted the word “database,” so its original keyword question correctly abstained. The test now asks “SQLite local vault,” which matches explicit source evidence; application retrieval behavior was not changed.
- A long nested test-vault folder hit Windows path limits. The continuation used a shorter isolated vault folder. General long-vault-path support is not proved or repaired by this fixture change.
- The earlier two-minute test's 18-of-20 hook count discrepancy remains open. Persisted trust success does not close it. No one-hour test ran.
