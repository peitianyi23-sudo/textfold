# Handoff: prepare the WebMCP contribution for upstream review

Date: 21 October 2026

## Objective and stopping point

Synchronize local `main` with the author's latest upstream `main`, create a clean contribution branch from it, and extract the implemented WebMCP feature from `personal`, including its uncommitted file-import work. Adapt it to current upstream, validate that branch, and create an English GitHub Draft PR with evidence for the user's review.

**The user authorizes pushing the tested contribution branch to their fork and creating an online GitHub Draft PR against the author's `main`.** This supersedes the earlier local-only stopping point. Keep it in draft for the user's review; do not mark it ready, request reviewers, send separate maintainer messages, open an issue, dispatch release workflows, or merge the contribution into `main`/`personal`. A Draft PR is visible to the maintainer and may generate GitHub notifications; it is not a private review document.

## Starting state: verify before acting

- Repository: `C:/Users/admin/agent-native/textfold`.
- Author remote: `upstream`, currently `https://github.com/chenxiachan/textfold.git`.
- User fork: `origin`, currently `https://github.com/peitianyi23-sudo/textfold.git`.
- Primary checkout was on `personal` at `9f852f8` when this handoff was written. It runs the daily TextFold service and contains unrelated dirty work. Keep that checkout and its service intact.
- Historical feature commit: `c48e590` (`Add browser WebMCP reading and documentation workflows`), merged into `personal` by `c0fa57d`. Existing feature worktree: `C:/Users/admin/agent-native/textfold-webmcp`, branch `codex/webmcp-reading`. These are extraction references, not the requested new upstream baseline.
- The later `file-import` implementation is uncommitted in the primary checkout. Inspect explicit diffs in `textfold/web/app.js`, `textfold/web/webmcp.js`, and `docs/webmcp.md`; new files include `tests/webmcp-file-import.test.cjs`, `docs/design/webmcp-file-import-design.md`, and `docs/webmcp-file-import-validation.md`.
- Unrelated dirty files included `tests/test_zotero.py`, `textfold/zotero_cache.py`, and library/UI latency design notes. `docs/design/webmcp-repair-tools-design.md` is a separate, unimplemented proposal, not delivered WebMCP functionality.

Read the actual status and current files; do not assume this snapshot is still complete. Preserve all unrelated files, stashes, worktrees, papers, model settings and producer caches. Record the source commit and explicit uncommitted hunks used for extraction without committing unrelated primary changes.

## 1. Establish the author's current baseline

Fetch `upstream` and inspect its default branch. Record the fetched upstream commit, date and subject. Read that revision's `CONTRIBUTING.md`, applicable agent instructions, `docs/DEVELOPMENT.md`, PR template if present, and relevant CI definitions before deciding the final validation set.

Use an isolated worktree for the clean contribution. Synchronize local `main` by fast-forward to the fetched `upstream/main`; create it from that ref if absent. If `main` has unique commits, is dirty, or is checked out elsewhere, preserve that state and resolve the baseline explicitly rather than resetting or overwriting it. A detached worktree at the fetched upstream commit can support independent extraction while that issue is explained. Do not treat a merge containing personal commits as a clean upstream baseline.

Create a new branch such as `codex/webmcp-upstream` from the synchronized `main`, using an unused name if necessary. Leave the primary checkout on `personal`. Report the actual branch, worktree and baseline SHA in the final handoff.

Completion: the contribution branch starts at the fetched author commit, and its worktree is separate from the daily checkout.

## 2. Extract one coherent WebMCP feature

Inspect `c48e590` and the current personal implementation. The historical commit spans registration, reading/navigation, notes/folders, documentation-directory import, original-language generation, Zotero cache reuse and their necessary shared support. Adapt only the dependencies needed by those workflows. The new file upload tool belongs with this contribution because it exposes the existing upload control through the same browser contract.

Port the feature as targeted patches or reviewed commits. Do not merge `personal`, copy complete personal versions of shared modules over upstream, or blindly cherry-pick a broad commit without examining its diff. Reuse improvements now present upstream, resolve actual API differences, and remove accidental dependencies on unrelated PDF correction, figure grouping, paragraph expansion or latency work.

The current implemented catalog has 19 tools; use `docs/webmcp.md` and `textfold/web/webmcp.js` as the exact current inventory. Preserve the division of responsibility: file upload uses `file-import`, selected cached papers use `zotero-import`, documentation directories use `documentation-import`, and progress uses `processing-status`. Keep shared operations shared; add no duplicate importer, status tool, synthetic browser registry or arbitrary filesystem endpoint.

Treat local design/validation files as implementation evidence. Rewrite public documentation for an upstream reader: remove user-specific paths, private manuscript text, stale tool-count claims and session histories. Do not include the unimplemented inspection/repair proposal in the implemented catalog. Retain compact reproducible tests and documentation needed by the feature.

Completion: every hunk in the diff against the upstream baseline belongs to this feature or an explained necessary dependency. Existing upstream behavior remains available in browsers without WebMCP.

## 3. Validate the extracted branch

Test this branch with its own service port and disposable data. Earlier results from `personal` are leads, not validation of the extracted branch. Before each check, identify the failure it detects and the change that failure would justify.

Current contribution requirements, to recheck against fetched upstream:

- Run the complete Python suite: `python -m unittest discover tests` (use the environment's working Python executable). The previous file-import session ran only 24 related Python tests, not the complete suite.
- Run the new JavaScript tests with `node --test tests/webmcp-file-import.test.cjs`, syntax checks for changed scripts, and diff whitespace checks. Add focused tests for any changed integration behavior that the existing suites do not cover.
- `CONTRIBUTING.md` says no change may make zoom less smooth. Because this feature loads on the reader and affects chapter rendering, measure the clean upstream baseline and contribution using the prescribed GPU/2x-pixel presented-frame procedure in `docs/DEVELOPMENT.md`, including the dense-paper example `2512.23916`. Use identical content, saved layers, viewport, hardware and gestures. Include both measurements, dropped-frame rates and meaningful limitations in the proposed PR. The existing benchmark uses Mac-specific Metal flags and historical fixture names; adapt the runner to the actual platform/current baseline without replacing presented-frame evidence with default headless requestAnimationFrame timings. If the required measurement cannot run, report it as missing and leave the proposal unready rather than claiming compliance.
- Read the fetched CI workflows and run additional checks relevant to the final diff. Desktop payload/build smoke checks are required when touched packaging or server integration warrants them; do not trigger release, publication or unrelated workflows simply because they exist.
- Sign off every contribution commit with `git commit -s`, using the user's configured identity. Stage explicit paths/hunks. Verify the trailers. Do not invent identity or sign with a maintainer's name.

Browser acceptance must use the actual host WebMCP catalog and calls, not REST-only tests or a JavaScript stub registry. The installed `webmcp` skill can guide host operation when available; its absence must not become an application dependency.

Exercise the contributed workflows with isolated fixtures:

1. Discover tools on landing and reader pages. Rediscover names after navigation. Confirm unsupported hosts retain the normal interface.
2. Import Markdown with inline/display mathematics, a PDF and a native office file through `file-import`. Verify saved source, selected language and provenance. Repeated import retains one item and its notes/layers under the existing reuse policy. Distinguish a readable source from completed generation; verify actionable model/engine/payload failures.
3. Import an ordered documentation directory, navigate chapters and source units, repeat without duplicating the work, and exercise failed-page retry/update with successful snapshots preserved. Check original-language behavior with a non-English fixture.
4. Enumerate exact Zotero attachment identity, import an existing matching cache, and verify missing-cache/multiple-attachment results. Keep original PDFs and llm-for-zotero producer caches read-only.
5. Verify reading context, navigation, exact-quote annotation create/update/delete, and library/folder operations. Use fixtures to check both saved outcomes and current reader state. Ordinary discussion must not silently become a note.

Record commands, counts, baseline/candidate commits, browser/host versions, fixture provenance and observed outcomes in a compact local validation report. For failures, compare against the same upstream baseline before attributing them to this feature. Do not suppress failures to obtain a green result. A prior PDF suite encountered Pillow `KeyError: JPEG` while creating a scan fixture and passed after `Image.init()`; investigate any recurrence and disclose the actual invocation/environment rather than silently excluding the case.

Completion: all required branch-specific checks pass, with actual browser calls and smoothness evidence; any unavailable check remains explicitly incomplete.

## 4. Prepare and create the English Draft PR

Produce `PR_TITLE.txt`, `PR_BODY.md` and a compact validation report in a local review-output directory. Do not commit review-only output unless it belongs in upstream documentation. Follow the fetched project's PR template; otherwise follow the applicable `pr` skill. Lead with the problem, resulting behavior and user scenarios, then concise validation and limitations. After all required checks pass, push only the contribution branch to the user's fork and create a Draft PR against `chenxiachan/textfold:main`. Use a structured body or `--body-file` to preserve the prepared Markdown. Inspect any existing matching PR before creating a duplicate. Attach the created PR to this Codex task with `attach_artifact`, and verify its base/head, rendered description and draft state.

Include these scenarios in the proposed body:

- A researcher asks an external browser agent about the exact selected source passage or equation, then explicitly saves a source-anchored note when requested.
- An agent imports a user-supplied reviewer-comments file through the same upload operation as drag/drop and follows conversion/generation through existing status tools. Use a synthetic example, not this user's private review text.
- An agent opens a complete documentation directory as one ordered work, navigates its chapters, or imports a specifically selected Zotero PDF from its existing cache.

Explain the compatibility boundary precisely: tools are registered by the page through `document.modelContext`; discovery/execution requires a supporting browser-agent host. This feature does not create a standalone MCP server and does not make every Codex client WebMCP-capable. Normal UI use remains available without support.

Desktop users may open the **desktop app's actual local server URL** in a supporting agent browser and operate that service/library. The desktop app chooses an available port starting at 31917; do not hard-code the developer server's 3017 address. Direct external-agent access to the Electron window has not been established. Selected passage, local zoom and current chapter belong to the browser view that executes the tool; the desktop app's selection is not automatically synchronized. Do not add desktop transport or address-discovery features as part of this extraction without a new requirement.

Cite the optional workflow guide accurately:

> The optional [WebMCP skill from Builder.io's Agent-Native skills collection](https://github.com/BuilderIO/skills/blob/main/skills/webmcp/SKILL.md) can guide compatible agents through discovery, invocation and result verification. It is not required by TextFold, is not an OpenAI-official skill, and does not supply browser WebMCP support.

That upstream skill path and description were verified when this handoff was written. Recheck the reference when preparing the proposal. Link rather than bundle its complete instructions or enforce its host-specific restrictions in TextFold. Standard interface semantics belong to the [WebMCP specification](https://webmachinelearning.github.io/webmcp/), whose current draft/status should be identified accurately.

Clearly separate measured outcomes, simulated/disabled model workers, and untested platforms. Report full-suite results and before/after smoothness numbers rather than quoting the earlier “31 tests passed” as contribution-wide validation. Screenshots or a short recording may demonstrate the final workflow; omit private source content and credentials.

## Delivery to the user

Return the Draft PR URL, local branch/worktree, exact upstream baseline, diff summary, contribution commits, complete test results, smoothness comparison, remaining limits, and links to the English PR proposal and validation report. Keep the branch and review artifacts available. Stop with the online PR still in draft; the user reviews it before any transition to ready for review or further maintainer outreach. If required checks remain incomplete, retain the local proposal and explain the gap instead of publishing an unvalidated draft.
