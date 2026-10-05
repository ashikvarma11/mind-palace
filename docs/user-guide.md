# Use Mind Palace with Codex

**Checked against the current Windows development workflow. Updated 5 October 2026.**

Mind Palace stores original coding sessions locally. Ask returns quoted passages from stored conversations. No AI model or API key is required for that workflow.

## Before you start

Use the desktop build, not the browser sample. There is no published installer yet. A prepared development build resolves its worker resources from the project; keep it in its build location. See [development setup](development.md).

The installed-client checks used Codex CLI 0.160.0. Other client versions and the Codex desktop application's own hook behavior are not separately certified. Verify a new captured turn before relying on your setup.

## 1. Open your vault

On Welcome or Connections, choose **Create local vault** once. Choose **Open existing vault** afterward. Closing the vault preserves its files.

The current app uses one default vault under the OS local-data folder: `dev.mindpalace.local/vault`. Custom vault-folder selection is pending.

`Local vault connected · AI off` means the vault is open and no model is connected. It does not disable local source search.

## 2. Allow a Codex source folder

Open **Connections**. Select **Codex** under **Coding client**.

Enter the absolute transcript folder used by your client. In the tested default layout this is `%USERPROFILE%/.codex/sessions`; a custom `CODEX_HOME` changes that location. Confirm the actual client folder before granting access.

Check **Allow hooks**, then choose **Save capture scope**. This grants capture for that folder. Optional Markdown memory capture is separate and is not needed for session search.

## 3. Install and approve the hook

Choose **Install Codex hook**. Mind Palace merges its handlers into the user-level `hooks.json`, keeps a backup and preserves other handlers. Ambiguous hook configurations are refused.

In Codex, open `/hooks`. Review the exact Mind Palace commands and trust the handlers. A changed handler needs new approval. The app reports hook-file state; it does not verify your current runtime approval.

![Actual native setup checklist](images/codex-setup.png)

## 4. Use Codex and import captures

Start or resume a Codex session after approval. Have a conversation. The local receiver can capture session data while Mind Palace is closed.

Open the vault afterward, or choose **Sync Codex to vault** in Connections. Ask also checks new captures before searching. These checks import available data; they do not prove every client event was delivered.

The capture inbox is under `%LOCALAPPDATA%/MindPalace/capture`. It is separate from the vault. The receiver records raw data; the vault imports verified source revisions into one canonical session record.

## 5. Read and ask

In **Sessions**, select a conversation. Read the original messages or choose **Show complete source**. The title filter searches loaded items; load more to include older sessions.

In **Ask memory**, use terms present in the conversation. For example, the synthetic fixture contains a SQLite choice. A question about SQLite returns its exact stored passage and a source link.

Search is keyword based. It can miss paraphrases. It abstains when evidence is missing. The result is an exact passage, not a model-generated summary or a confirmed decision.

## Import existing history

In Connections, choose **Review Codex history import**. Check the source folder, counts and size. Choose **Confirm and import Codex history** only if that scope is correct. Unknown older sessions are not silently imported.

## Pause, repair or remove

| Action | Effect |
| --- | --- |
| Pause Codex | Stops approved capture for that scope; saved data stays. |
| Repair known Codex sessions | Checks already known session IDs in the approved folder for missed revisions. |
| Validate inbox and rebuild index | Validates captured data and updates the derived inbox index. |
| Clean old imported prefixes | Removes only covered, acknowledged prefixes older than 30 days. It preserves the complete source. |
| Remove Mind Palace hook | Removes the app's handlers and preserves other hooks. It does not erase the vault or inbox. |

## If something fails

| What you see | What to do |
| --- | --- |
| Desktop vault unavailable in browser | Open the desktop build for real storage. |
| Vault closed | Open the existing vault or create one once. |
| Installed hook, no new session | Check `/hooks` approval, saved source scope and capture health. Try one new turn, then sync. |
| `CAPTURE_TIMEOUT` or an uncertain write | Refresh status and inspect stored data before another change. A write may have completed. |
| Capture warning but an answer appears | The answer uses sessions already stored. New captures were not verified in that request. |
| No answer | Check that the session is imported. Use terms from its original text. |
| Large/divergent capture skipped | Keep the source and inbox. The current complete-source bound is 20 MiB; conflicting revisions require investigation. |

Do not delete the inbox or vault to clear an error. Do not publish transcripts, vault files, hook commands with private paths, or credentials in a bug report. Use synthetic reproductions and safe error codes.

## Current limits

The two-minute installed-client test recovered exact source but verified 18 Stop/SessionEnd deliveries for 20 turns. First-turn termination before any capture is not proved. Special-path hook timing, installer acceptance and Mac support remain open. Claude Code is not yet verified end to end.

[Roadmap](roadmap.md) · [Verification](verification/codex-runtime-13.md) · [Back to README](../README.md)
