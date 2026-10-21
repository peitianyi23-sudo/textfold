# New and Settings opening latency: design discussion

Status: design discussion complete on 2026-10-18. The user accepted Q1-Q3 recommendations. This turn records the settled design and prepares a handoff; it does not start implementation.

## Established facts and scope

The sidebar + New action navigates to the landing page. Settings awaits GET /api/models before creating its dialog. The model catalog synchronously probes local Ollama through providers.ollama_models, even when the saved generation provider is the running ChatGPT bridge. Landing-page default-model, ask-model and label lookup repeat that catalog work three times in the current configuration.

Observed on this Windows machine: Ollama localhost discovery approximately 3 seconds, Settings backend approximately 3 seconds over 127.0.0.1, landing-page backend approximately 9 seconds. The isolated homepage model lookup alone took 9.054 seconds, with three Ollama probes of 3.024, 3.015 and 3.011 seconds. ChatGPT bridge discovery took approximately 0.003 seconds; the warm engine-status route took approximately 0.001 seconds. These are local observations, not claims about every upstream user's timings.

The issue also exists in the author's current main source at 2cd77e0987b590f9f67154bcdda76c59e6870b73:

- textfold/web/app.js: openSettings
- textfold/server.py: landing_page and models_payload
- textfold/models.py: provider_list, catalog, default_model, ask_choice and label
- textfold/providers.py: ollama_models

The current main design is already established: main mirrors the author; personal carries local customizations. After fetching the missing upstream/main reference, local main, upstream/main and the fork's origin/main all equal 2cd77e0. personal was clean at f120a84 and synchronized with origin/personal before this discussion. The discussion now leaves GLOSSARY.md modified and this design document untracked; preserve both. No branch reset or recreation was necessary.

## Agreed delivery direction

The user's latest correction supersedes the earlier proposed delivery order:

1. Implement on a focused branch based on the author's main and verify locally in isolation.
2. After local verification passes, merge the fix into personal and deliver a working local version for the user to experience. This is the current implementation handoff's completion boundary.
3. Wait for the user to try it and explicitly confirm the experience is satisfactory. Passing automated checks does not replace this acceptance.
4. Only after that confirmation, prepare the draft upstream PR for the user's review.
5. Wait for the user to review and approve the PR before sending it to the author. Creating a draft on GitHub is already an external submission, so do not publish even a draft PR without explicit authorization for that step. A local PR title/body/diff preview can be prepared first when the user requests the draft.

The current handoff does not authorize creating, publishing or sending any upstream PR. Keep the implementation focused so a later upstream PR can exclude local Zotero, figure-grouping, language and reader-presentation customizations.

The intended behavior is prompt opening of New and Settings, without removing model discovery or losing saved settings. Numeric cache lifetimes, concurrency details and routine algorithm choices belong to the implementer after the user-facing behavior is settled.

## Design tree

Settled: both New navigation and Settings opening are in scope; the issue predates personal changes; the focused fix starts from clean main; local verification and merge into personal precede user experience acceptance. Upstream PR preparation and submission are later, separately authorized stages. This discussion does not start implementation.

The frontier is empty after the user accepted all three recommendations. No additional product choice is currently blocking implementation. Ask again only if a newly discovered trade-off changes these agreed behaviors.

## Accepted behavior

1. Open Settings immediately. Language, appearance and other independent settings remain usable while model discovery runs. Show saved configuration and the last discovered model choices when available; on first use without discovery results, show a loading state in the model area. The New/landing interface must also become available without waiting for model discovery.
2. Refresh model discovery automatically in the background when Settings opens. Do not continuously scan while the page is idle. Preserve the distinct purposes of Agent Rescan, provider Fetch models and Connection test. Routine cache lifetimes and duplicate-request handling are implementation choices.
3. On discovery failure, keep the dialog usable, preserve saved settings and previous results, show a clear refresh error with retry, and end the scanning indicator correctly. Discovery failure is not proof that no models exist. With no prior result, show the failure rather than inventing a current empty catalog.
4. Background refresh must not discard in-progress user edits or silently replace saved model selections. Existing generation-time resolution and actual connection-test behavior remain behaviors to preserve, not a request to build new provider-health logic.

## Verification direction

Demonstrate the original slow/failing behavior before implementing the fix. Measure actual New navigation/server response and Settings click-to-visible time, with slow/unavailable Ollama, an existing saved provider, first discovery without a prior result, and later successful discovery. Verify refresh failure/retry and Rescan recovery without overwriting settings. Run repository tests and inspect the resulting upstream-only diff. Follow CONTRIBUTING.md and docs/DEVELOPMENT.md, including the reader smoothness measurement rule if applicable to the eventual patch; do not claim new frame evidence without measurement.

Use isolated data and a separate port. Do not alter the daily paper corpus, Zotero cache, stored levels, annotations or model credentials for this UI/model-discovery fix. Recheck the daily service PID and queue before any later service replacement. Do not restart an occupied generation queue.

## Existing refresh and failure behavior, verified from source

Rescan belongs to the local Agents section. It scans agent binaries/versions/model lists, then returns models_payload, which incidentally discovers Ollama and the bridge. Saved API provider lists are not remotely refreshed by this action; Fetch models is a separate provider action. The bridge already has a five-second status cache.

Selecting a model saves its ID without making a connection-test call. The current default-model resolver can temporarily fall back when the saved choice is absent from discovery, but does not overwrite that saved choice. Generation resolves its model once at job execution; a real model request can still fail after discovery. Preserve these boundaries unless a further product decision explicitly changes them.

Settings' initial model-list request currently has no catch and precedes dialog creation, so failure leaves no dialog or visible error. Agent Rescan failure also lacks a catch/reset and can leave its scanning indicator stuck. These are reachable failures in the same opening/refresh flow, not reasons to add a general provider-health framework.

Model discovery and connection test are now distinguished in GLOSSARY.md. No ADR is proposed: the implementation choices are local and reversible.
