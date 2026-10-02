# Mind Palace

A private, local-first memory workspace for notes, conversations, decisions, and unfinished work.

**Early development. Not an installable product yet.** The approved Workspace interface is the first milestone. Local memory storage, bundled AI, repository mapping, and native installers are still pending; the browser prototype uses clearly labelled fictional examples, not real AI or durable memory.

Backend progress: portable storage and a packaged Windows worker are tested separately; offline OpenAI/Anthropic API adapters and sharing previews are implemented. They are not connected to this interface and cannot send requests yet. Secure native key handling and transport remain pending. See [the latest verification](docs/verification/cloud-foundation-01.md).

Desktop progress: a Windows native development shell now builds and renders the approved interface with your local artwork. Native health/navigation/reload/close checks pass; it still uses sample-only state. See [native verification](docs/verification/step-03b.md) and [local toolchain setup](docs/development.md#project-local-windows-desktop-development).

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
