# Mind Palace

A private, local-first memory workspace for notes, conversations, decisions, and unfinished work.

**Early development. Not an installable product yet.** The approved Workspace interface is the first milestone. Local memory storage, bundled AI, repository mapping, and native installers are still pending; the browser prototype uses clearly labelled fictional examples, not real AI or durable memory.

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

Browser tests can reuse an existing compatible Chromium binary through the optional `MP_BROWSER_EXECUTABLE` environment variable; otherwise use Playwright's installation above. Developer tools are required for this prototype, not a claim that end users must install them in the planned desktop release. Python 3.12 was used for the runtime probe. Native desktop launch and installer commands do not exist yet.

Verified first milestone: production browser build, seven unit tests, seven end-to-end browser tests (all routes at 1024/768/390/320 px, source/review/handoff flow, theme, keyboard entry, unknown-answer abstention, inert input, and no external HTTP requests in the tested sample flow). See [verification evidence](docs/verification/step-03a.md).

The app will not send memory to its developer or collect analytics. Copying selected content into a cloud assistant will share that content with that provider. No cloud AI connection is active in the prototype.

Code is MIT licensed. The supplied temporary logo is a separate asset whose redistribution license has not been established, so its binary is kept out of public Git history for now; the local development copy uses the approved artwork. The app retains a lettermark fallback when the asset is missing.
