# Implementation research

Checked: 2 October 2026. Versions below come from registry/tool output, not memory.

| Source | Finding and use |
| --- | --- |
| https://cli.github.com/manual/gh_repo_create | `--public --source --remote` creates the approved public repo and connects the existing local Git root. Verified remote: https://github.com/ashikvarma11/mind-palace.git. |
| https://angular.dev/reference/versions | Angular 22 supports Node ^24.15.0; installed Node 24.16.0 is compatible. Registry Angular core/CLI/build report 22.2.1; inspect generated package compatibility before locking. |
| https://angular.dev/cli/new | Standalone client-only scaffold with routing and SCSS; use the pinned generator and inspect actual filenames/build/test runner. |
| https://v2.tauri.app/start/prerequisites/ | Windows native builds need Rust MSVC and Microsoft C++ build tools. Rust/cargo not in PATH; vswhere C++ component probe returned no installation. Desktop readiness is not verified. |

No claim of tested model inference, worker freezing, or Graphify extraction yet. Registry and source snapshots/hashes for those dependencies are pending Step 02.

## Verified browser subset

- Pinned @angular core/CLI/build/compiler family 22.2.1; TypeScript 6.0.2, RxJS 7.8.2, tslib 2.8.1, Vitest 5.0.0, jsdom 30.0.0, @playwright/test 1.63.0, @lucide/angular 1.49.0. The installed package lock is authoritative; install and builds verified compatibility.
- https://angular.dev/guide/signals — writable/read-only/computed signals; sample state is explicit and in-memory.
- https://angular.dev/guide/routing/define-routes — typed routes, lazy component loading and route data; actual router declarations/build verified `withComponentInputBinding`.
- https://angular.dev/guide/testing — scaffold uses @angular/build:unit-test with Vitest, not Karma. `ng test --watch=false` was actually run.
- https://lucide.dev/guide/angular/getting-started — @lucide/angular is the current standalone/signal package. Legacy lucide-angular 1.0.0 peers stop at Angular 21, so it was not installed. Verified new package peer range >=17 and actual standalone/dynamic declarations in installed source.
- https://docs.github.com/en/account-and-profile/reference/email-addresses-reference — ID-based no-reply commit identity selected from verified public GitHub account ID; local repository configuration only, no personal email published or global preference changed.
- Prototype bundling uses only local assets/system fonts. No third-party runtime network requests occurred in the tested browser sample flow; this does not certify the future native runtime.

Scaffold generated safely in ignored `.tools/scaffold` because the generator refused to merge the pre-existing README; only enumerated new source/config files were adopted. Existing repository guidance/privacy exclusions were preserved.
