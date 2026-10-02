# Mind Palace

A private, local-first memory workspace for notes, conversations, decisions, and unfinished work.

**Early development. Not an installable product yet.** Windows desktop development builds now save and reopen pasted conversations locally. AI, repository mapping and installers remain pending. The browser sample is fictional, not durable memory. Library is the latest design preference; the existing interface is still Workspace.

AI progress: Ask memory now previews one explicitly selected original passage and the complete credential-free provider request, with discard/expiry and cancellation. Nothing is sent. Key entry and HTTPS sending remain pending; the interface cannot produce real AI answers. Native request control and internal Windows credential foundations are separate verified subsets. No real keys or paid calls were used. See [preview UI verification](docs/verification/ai-preview-ui-01.md), [AI request verification](docs/verification/ai-requests-01.md) and [credential verification](docs/verification/native-credentials-01.md).

Desktop progress: Welcome/Sessions offer create/open/close for one local vault, pasted conversation saving, manual notes and source-checked reading. WebView reload, app restart and owned-worker exit checks pass with isolated synthetic data. No AI or cloud calls. See [desktop vault verification](docs/verification/native-vault-01.md) and [local development setup](docs/development.md#project-local-windows-desktop-development).

The first vault is under your device's local app-data/dev.mindpalace.local/vault directory. Opening is manual; closing preserves files. Original saved text is hash-checked when read; manual notes are not confirmed decisions. Custom folder selection/full recovery UI remain pending.

Uncertain saves are never automatically retried. An unchanged draft retains its operation ID while the app is open: reopen the vault and explicitly retry it. Do not reload before resolving it; durable retry drafts across app restart are still pending. Other real-memory pages remain unconnected; sample mode stays separate.

## Development

Angular 22 on compatible Node.js, Tauri 2, and a bundled Python memory service are the approved architecture. See the [implementation plan](docs/implementation-plan.md), [current status](docs/implementation-status.md), and [research](docs/research.md).

```sh
npm ci
npm run dev:web
```

Open `http://127.0.0.1:4200` and choose **Explore sample workspace**. The sample is fictional and resets on reload. Check the source messages, review a decision, and inspect the resulting handoff.

```sh
npm run check
npx playwright install chromium
npm run test:e2e
npm run probe:runtime
```

Browser tests can reuse an existing compatible Chromium binary through the optional `MP_BROWSER_EXECUTABLE` environment variable; otherwise use Playwright's installation above. Developer tools are required for this prototype, not a claim that end users must install them in the planned desktop release. Python 3.12 was used for the runtime probe. Windows development desktop commands now exist; installer commands remain unavailable.

Verified first milestone: production browser build, seven unit tests, seven end-to-end browser tests (all routes at 1024/768/390/320 px, source/review/handoff flow, theme, keyboard entry, unknown-answer abstention, inert input, and no external HTTP requests in the tested sample flow). See [verification evidence](docs/verification/step-03a.md).

The app will not send memory to its developer or collect analytics. Copying selected content into a cloud assistant will share that content with that provider. Optional OpenAI/Anthropic API-key integration is now planned: selected content would leave the device and provider API charges may apply. It will be off by default. No cloud AI connection is active in the prototype; see [the cloud AI plan](docs/cloud-ai-plan.md).

Code is MIT licensed. The supplied temporary logo is a separate asset whose redistribution license has not been established, so its binary is kept out of public Git history for now; the local development copy uses the approved artwork. The app retains a lettermark fallback when the asset is missing.
