# Development

Project root: `D:/Projects/mind-palace`. Browser foundation: Angular 22.2.1 with strict TypeScript and templates, standalone routes, signals, system fonts, and a local Lucide subset.

Use compatible Node (tested 24.16.0) and npm (tested 11.17.0), `npm ci`, and `npm run dev:web`. The server binds only 127.0.0.1:4200. Open Welcome and explicitly choose the fictional sample. Reload resets sample state; do not use it to store personal memory.

`npm run check` runs unit tests and production build. `npm run test:e2e` uses Playwright; first use `npx playwright install chromium` or provide a known compatible existing binary with `MP_BROWSER_EXECUTABLE`. No machine-specific browser path is hard-coded in the committed configuration. Browser tests distinguish in-memory samples from native/backend/inference verification.

`npm run probe:runtime` uses Python for actual preliminary SQLite/atomic-write capability checks. Native desktop and frozen memory-service scripts will be introduced only when their implementations exist; no placeholder successful commands are supplied.

Current public clone uses an MP fallback without the supplied binary artwork. Local artwork remains in ignored public/brand paths pending a separate asset license/provenance decision. Dependency licenses are separate from application MIT; production Angular license extraction remains enabled.
