# WebMCP reading workflows discussion

Status: implementation authorized on 2026-10-20 in a new chat using GPT-6.1 Sol with medium reasoning, on a feature branch. Merge back into personal after successful validation; do not push or create a PR.

## Agreed direction — 2026-10-20

- Prioritize Zotero import and library organization, plus importing a website documentation set as one reading document.
- A documentation set should be one library item with ordered chapters and retained source URLs, rather than a folder of unrelated page imports.
- Import should automatically start reading-level generation. Do not introduce a separate opt-in generation step as part of this design.
- Read in the original language. Do not automatically generate Chinese or other translations.
- Keep original content readable while generated reading levels are being prepared.
- From a starting URL, identify the documentation set and its chapter directory. Default to the documentation set, excluding unrelated site content such as blogs unless requested.
- When the user asks to import, proceed directly without a routine directory-confirmation step. Report the imported scope and failed pages afterward. Ask only when the intended scope is genuinely ambiguous; a request to preview the directory remains read-only.
- Reimporting the same documentation set opens the existing reading document by default, without creating a duplicate or automatically regenerating its layers.
- An explicit request to update to the latest source updates the existing reading document, preserving notes, highlights and reading position.
- Expose folder management as independent WebMCP tools, including creating and renaming folders and moving documents. The user has no immediate need to create folders; automatic library organization is not a current priority.
- Include current reading context in the first tool set: the current reading document, selected passage or formula, containing chapter, and surrounding source context needed for an external agent to answer.
- Include annotation tools in the first tool set: read, create, update and delete notes and highlights anchored to source passages. Write annotations only when the user requests saving or marking; ordinary conversation does not automatically become an annotation.
- If some pages in a documentation set fail to import, keep successfully imported chapters readable, identify the missing chapters, and support retrying only the failed pages without reimporting the successful ones.

## UI context and constraints

- Any additional import status, missing-chapter indication or retry affordance must fit TextFold's existing visual design and interaction patterns.
- Prefer existing directory, status and error presentation where appropriate. The agreement to expose import results does not prescribe a new badge, panel, dashboard or notification system.
- Determine the concrete presentation against the current UI before implementation. These notes capture the behavior and design constraints, not an approved new layout.
- Report partial import results through the tool response as well, so the agent can explain what was imported and what remains missing.

## Implementation decisions delegated to the implementing agent

- Detailed discovery rules for documentation directories and chapter ordering.
- The concrete presentation of partial failures and targeted retries within the existing UI.
- How source changes are matched to existing chapters and annotation anchors during an explicitly requested update.
- Exact tool boundaries and the ordering of subsequent reader-context and annotation capabilities.

Resolve these details using the agreed behavior and existing project conventions. Do not restart the product interview for routine implementation choices.

## Implementation handoff

- Implement genuine page-exposed WebMCP tools discoverable and callable by a browser host; REST routes alone are not delivery. Reuse the app's existing operations and persistence rather than creating a second application model.
- Cover library search/list/open, exact Zotero item/attachment discovery and import, documentation-set import/update/retry, folder create/rename and document moves, current reading context/navigation, and annotation CRUD. Expose the status needed to distinguish readable content, generation in progress and failures.
- Preserve exact Zotero attachment identity and existing cache-first behavior. Do not modify llm-for-zotero, original PDFs or producer caches, and do not substitute another paper version. Return actionable missing-cache or attachment-selection results.
- Use https://www.agent-native.com/docs/#create-an-agent as the real documentation-set acceptance example. Follow the site's actual directory hierarchy and ordering, retain chapter source links and useful content such as code, images and internal links, and exclude unrelated site areas. A URL fragment is not a separate source page.
- On explicit source updates, preserve existing annotations and reading state. If a changed or removed passage cannot be matched, retain its annotation and original quoted context and report it as unresolved rather than silently dropping it or attaching it to unrelated text.
- Test against an isolated data directory and port, preserving the daily reader on 127.0.0.1:3017 and the local model bridge. Do not auto-import a large test set into the user's daily library or start an unbounded model workload.
- Verify live tool discovery and actual calls in the sidebar browser when available, plus browser-visible reading context, annotation round trips and UI fit. If a host transport prevents verification, identify that specific gap rather than claiming end-to-end success from REST tests alone.
- Validate multi-page chapter order/provenance, repeated import reuse, partial failure and targeted retry, explicit update with annotation preservation, automatic original-language reading-level generation without translation, and exact Zotero import. Use meaningful focused tests plus the project's required checks.
- The primary checkout has unrelated dirty discussion documents and GLOSSARY.md edits. Preserve them; stage only task-owned changes. This discussion document and the source-page/reading-document/library-folder glossary additions belong to this handoff, but other glossary edits may belong to concurrent work.
- Another chat is implementing PDF correction optimization: local thread 01a157cc-c891-7ba2-b92c-e08424caba71. If relying on its state, read it first; do not message it without user authorization. Coordinate integration by inspecting current personal and Git state; do not overwrite its changes.
- Start from current personal on a codex/ feature branch, isolate work as necessary, and commit the scoped implementation. After relevant checks pass, integrate current personal, resolve conflicts preserving concurrent work, rerun checks affected by integration, then merge back into personal. No push or PR. Report the branch, commits, checks, actual browser evidence and any limitations.

## Current implementation evidence

- Generic URL import fetches one page; it does not discover or assemble a documentation tree.
- A composed Markdown import can preserve headings, but it lacks chapter-level source provenance.
- Existing library, Zotero, reader, annotation, job and export operations are candidates for WebMCP exposure.
- Normal UI imports already initiate generation; a tool must preserve the complete workflow. The Markdown storage endpoint alone does not initiate generation.
- The current base reading layers assume English; a general original-language mode does not yet exist. Selecting English avoids translation for English sources, but does not satisfy original-language generation for every source language.

These notes record the intended behavior; they do not establish that the new tools or multi-page ingestion exist.
