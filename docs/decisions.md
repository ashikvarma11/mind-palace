# Decisions

Updated: 2 October 2026. Only direct user choices are marked approved.

| ID | Decision | Status and evidence |
| --- | --- | --- |
| D001 | Name: Mind Palace | Approved: user chose the name in this conversation. |
| D002 | Public GitHub repo, MIT code license | Approved: user's public-repo and MIT answers. Owner is the verified authenticated account; child root is D:/Projects/mind-palace. |
| D003 | Workspace design | Approved: selected Workspace in the design carousel, then “This looks good. Let's proceed with the implementation.” |
| D004 | Supplied brain-and-palace logo, favicon/app-icon source, opening artwork | Approved for temporary app use by user; artwork licensing is separately unresolved. Preserve original bytes. |
| D005 | Angular + Tauri + bundled Python + local AI, Windows tested first | Approved in the explicit baseline-choice answer on 2 October 2026. No paid/cloud service is authorized. |
| D006 | Angular browser shell may be developed before complete native/model probes | Engineering sequencing decision: missing native build prerequisites; Step 03A remains an explicitly partial prototype, not native gate verification. |
| D007 | Locally bundled Lucide Angular subset for prototype icons | Engineering choice matching reviewed design; no runtime CDN requests. Material/CDK interactions are introduced when actually needed. |
| D008 | No browser persistence masquerading as a durable vault | Integrity boundary: prototype sample state is in memory and resets on reload; storage is owned by the planned Python service. |
| D009 | Isolated Windows diagnostic packaging before production worker | Delegated engineering choice: free pinned dependencies in ignored .tools/probe-venv; synthetic tests only; no global/admin installation. Frozen diagnostic is not labelled production storage/native/AI. |
| D010 | Graphify direct AST API only in the diagnostic | Inspected pinned 0.9.73 extractor; sequential TypeScript parsing with explicit fixture/cache roots, no provider path. CLI even performs stale-skill refresh before help/version, so do not invoke it or register skills in the app workflow. |
| D011 | MCP 2.2.0 stdio diagnostic, separate from memory integration | Inspected official SDK docs and installed signatures; local diagnostic tool only, no assistant registration/vault scopes. Source tests cover legacy and modern protocols; frozen test covers legacy. Disable OpenTelemetry exporters and keep transport local stdio. |

Pending: stable release bundle identity/publisher, model selection, minimum supported OS/hardware, Mac testing, signing/distribution, artwork redistribution license, provider export fixtures. Jev remains future-only.

## Delegated safe decisions

The user subsequently said: “from here on, take your own decisions. dont ask me. just make sure the decisions are safe and no money is involved”. Make routine and remaining engineering choices autonomously, within the original scope. Use local/reversible operations, free dependencies, no purchases, no paid cloud services, no private-data publication, and no unrequested system-wide administrator changes. Lack of Mac hardware or an unknown asset license limits claims/distribution; it is not permission to pretend verification or ownership.

Release engineering defaults: Windows x86_64 first; free unsigned development builds with limitations disclosed; no automatic release publication; plain English rather than formal compliance claims. Model selection still requires measured results, not guesses.
