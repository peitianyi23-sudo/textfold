# Zotero Library opening latency discussion

Status: first-stage scope and delivery workflow settled on 2026-10-18; handoff requested. This discussion made no implementation changes. The next implementation session should follow the accepted scope below.

Latest runtime correction from the user: daily service is now http://localhost:3017/ . Earlier 3027 references describe historical measurements only. Inspect 3017 before any service replacement.

## Established facts

This is separate from Settings/New model discovery, now submitted as upstream PR https://github.com/chenxiachan/textfold/pull/24 . Do not add Zotero changes to that PR.

On 2026-10-18 the daily personal page at http://localhost:3027/ was reproduced opening Zotero Library into a dialog containing only an ellipsis. Source: `textfold/web/app.js`, `openLibrary`; `textfold/zotero.py`, `_get`, `_all`, `status`, `collections`, `items`.

Current UI waits for library status, then all collections, before showing the browse controls; item rows appear only after the complete item listing has been fetched. Each local API listing page contains at most 100 records. The API reported 144 collections and 1827 top-level records; TextFold returned 1447 browse items after its existing type filtering.

Measured daily HTTP calls: status 2.241 s, collections 4.096 s, items 44.852 s. Repeating status/collections gave 2.211 s / 4.088 s. Direct single-page requests via localhost took about 2.0–2.3 s each, while the same routes via 127.0.0.1 took 20–86 ms. With a temporary in-process base override to 127.0.0.1, complete calls took status 0.206 s, collections 0.058 s, items 5.769 s. The override did not write configuration. The precise cause of localhost connection overhead has not been proven; the address-dependent timing and serial-pagination amplification have been demonstrated.

Read-only diagnostic scripts are under `launch/zotero-open-latency/`: `diagnose.py`, `loopback_comparison.py`. The loaded browser screenshot is `library-loaded.png`. These local artifacts are ignored by Git. No library, PDF, extraction cache, model credentials or daily configuration was changed.

## Design tree

Settled: discuss before implementation; separate scope from PR #24; retain existing Zotero PDF attachment/cache reading responsibilities.

## Accepted behavior and current frontier

- The user emphasized that even the first-level collection tree is slow. Optimize collection availability separately from item availability. The current status plus full-collection chain takes about 6 s on localhost; temporary direct-loopback measurements reduced those calls to about 0.264 s combined. Do not treat item pagination as the solution to the collection delay.
- Q2 accepted: reopening shows the last successful collections/items immediately while refreshing in the background. Failed refresh preserves previous content with an explicit error and retry; no continuous idle scan.
- Q3 accepted: reopen at the last selected collection, restoring its expanded ancestor path and previously available items. If a successful fresh collection result confirms that collection was deleted, fall back to All items. A request failure is not evidence of deletion.
- Q1 remains undecided: whether initial item results should appear in automatic batches. The user explicitly asked to think further; no manual Load more or automatic incremental-loading behavior is accepted yet.

First-stage scope: remove avoidable connection, duplicate-request and dependency costs; accelerate the collection tree independently; implement the accepted cached reopening and collection restoration; measure directory, item and search latency separately. Defer Q1 until those measured improvements can be assessed. No incremental item-display behavior is included in this stage.

## Accepted branch and delivery workflow

The user corrected the proposed upstream-first workflow and accepted starting from **personal** for this task:

1. Create `codex/zotero-library-latency` from the current verified personal HEAD, preferably in an isolated worktree. Inspect attached worktrees first. Keep existing personal features and discussion artifacts intact.
2. Reproduce and validate with separate test data/settings and port. Diagnose actual API/search costs before choosing implementation details. Record before/after measurements for first-level collections, selected-collection items, library search and reopening.
3. After validation passes, use ordinary signed-off merge back into personal. Confirm the daily service's identity/data/queues before replacement; keep running generation jobs intact.
4. Verify the merged source and actual daily page, then deliver the personal version for user experience testing.
5. An upstream contribution is optional and later. After the user accepts the personal result, assess general applicability. If subsequently authorized, create a clean branch from latest author main and transfer only the common optimization, excluding personal integration changes. This task does not create a PR or push.

This workflow supersedes the earlier suggestion to start the Zotero fix from upstream/main. Existing Settings/New PR #24 remains separate.

## User steering after the first round

The user did not accept Q1-Q3 as the core design. They regard normal loading/search behavior as expected and want the software's actual search and API calls sped up, rather than merely presenting the waiting differently. Prioritize measuring and removing underlying delay; do not treat pagination, cached reopening or a Load more control as accepted product choices.

Correction: this is not port conversion. Both localhost and 127.0.0.1 use port 23119. DNS/address selection, IPv6 fallback or connection handling may explain the difference, but the specific mechanism is not established.

Recommended engineering investigation, not implementation authorization:

- Measure connection and address selection; use an appropriate direct loopback for the default local service if confirmed, preserving explicit configured remote/custom bases.
- Break down the remaining 5.769 s into Zotero page-response time, decoding, TextFold item mapping and stored-paper checks; optimize the demonstrated cost rather than assume a second cause.
- Preserve server-side Zotero `qmode=titleCreatorYear` search; current UI/backend already search the whole selected library even with a collection selected. Each query currently drains all matching pages before returning. Avoid fetching unrelated rows; share duplicate in-flight reads and prevent obsolete searches delaying the newest query.
- Remove unnecessary serial dependency between the collection tree and the current item query once the library is known. Do not blindly flood Zotero with concurrent page requests.
- Only if avoidable cost removal leaves material first-content latency, discuss incremental transfer/rendering; this need not imply a new manual Load more interaction.

Code fact check found that item sorting is currently upstream order without explicit sort parameters; totals are consumed for pagination but discarded before UI. Failures are swallowed into empty collection/item lists. `_all` also serves attachment enumeration, so a future browsing optimization must preserve reading/import semantics instead of globally changing that helper's contract.

Original first frontier (superseded as the starting discussion; no answers accepted):

1. Opening and browsing: recommended immediate closable dialog, then first page of items as soon as available, with explicit Load more rather than waiting for the complete library.
2. Reopening and freshness: recommended show the last successful view immediately with a refresh indicator; refresh on opening and explicit retry, no idle background scan. Clearly mark stale results if refresh fails.
3. Search: recommended server-side search across the selected library, independent of which browse pages have loaded; retain a clear indication of search scope. No search restricted silently to loaded rows.

Implementation details such as page size, request deduplication and loopback selection belong to the implementer after product behavior is agreed. Explicit non-default Zotero base addresses must be respected. Do not add an ADR for reversible local pagination choices.

Routine implementation should preserve ongoing navigation/search and avoid stale responses replacing the current context. Reopen discussion only for a new product trade-off; Q1 is explicitly deferred rather than a blocker for the accepted first stage.
