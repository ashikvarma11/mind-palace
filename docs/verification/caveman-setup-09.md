# Caveman setup — 4 October 2026

The user explicitly requested the caveman skill and automatic use in every Codex session, including subagent responses. This authorizes the user-level skill, hook and instruction changes below. It does not authorize other agent integrations or change Mind Palace capture consent.

## Provenance and configuration

- Installed only `skills/caveman` through the bundled skill installer from `JuliusBrussee/caveman`, pinned commit `6571943370f7c9d4de1946481177ee7b306cd8e8`.
- Installed source: `C:/Users/varma/.codex/skills/caveman/SKILL.md`, SHA-256 `34255a0215a7701eb83d508d03bc9560dc7bffbeb95a145ad2921ad2598a03bf`. The upstream skill preserves facts, commands, code, paths, numbers and negations, and explicitly uses ASD-STE100 as its clarity floor.
- Added `C:/Users/varma/.codex/hooks/caveman-context.ps1`. It emits the installed skill as JSON additional context for SessionStart and SubagentStart. It reads bounded event metadata and the skill file only; it does not open transcripts, use credentials, call a network service or save event content.
- Added these groups to `C:/Users/varma/.codex/hooks.json`, with ten-second handler timeouts and a 2500-token additional-context limit. No user hooks or global AGENTS file existed at inspection; inline config hooks were absent. The mutation rechecked the original bytes before writing and retained a local rollback record at `C:/Users/varma/.codex/hooks/caveman-backup-ee70a6ef-51d6-4eed-bd8f-baa29bf47ee2.json`.
- Added the marked default-style block to `C:/Users/varma/.codex/AGENTS.md`. It tells the main agent to read the skill and include its path in any authorized delegation prompt. The refreshed task instruction chain includes this block. It changes style only and does not grant delegation or action authority. Explicit user instructions and higher-priority requirements still take precedence.

Official sources opened 4 October: [Codex hooks](https://learn.chatgpt.com/docs/hooks) defines SessionStart/SubagentStart additional context and hook trust. [Global AGENTS instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md) defines startup loading and override order. Upstream source: [pinned caveman skill](https://github.com/JuliusBrussee/caveman/blob/6571943370f7c9d4de1946481177ee7b306cd8e8/skills/caveman/SKILL.md).

## Actual checks

Both direct PowerShell hooks passed with exact event-specific JSON and the complete local skill body. SessionStart took 363 ms and SubagentStart took 298 ms. A synthetic sentinel input field was not echoed into the context. Empty input, missing event, malformed JSON, unsupported Stop event and a 65,537-character input were rejected without stdout context.

The skill creator's Python validator could not start because PyYAML was absent in both existing checked Python runtimes. No global package was installed. The alternate installed js-yaml 5.4.2 parser validated the YAML frontmatter, supported fields, skill name, description bounds and absence of unfinished placeholders. Hook JSON validation passed. This alternate check is recorded separately; the Python validator is not claimed as passing.

The skill is available to Codex discovery on the next turn. Normal user hooks require review/trust through Codex `/hooks`; writing the file does not establish runtime trust. The global instruction supplies the requested preference while hook trust is pending. Direct SubagentStart checks establish the handler contract, not an observed spawned subagent or guaranteed model obedience.

Installed Codex CLI 0.160.0 also passed isolated probe `client-immhj243`: its SessionStart hook added the caveman instruction to the single loopback fixture request. The client used the exact installed hook command, strict configuration and a one-off reviewed trust bypass in a separate synthetic Codex home. No global AGENTS copy was supplied in that home, so the observed context came from the hook. The fixture returns fixed text and is not AI. This proves actual startup context delivery, not normal persistent trust or model style quality.

No Mind Palace user capture hook, actual transcript scope, Claude Code configuration, paid provider, global runtime installation or release was changed by this side note.
