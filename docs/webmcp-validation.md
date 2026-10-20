# WebMCP reading validation — 2026-10-20

Implementation starts at personal `80d389f`, on `codex/webmcp-reading`, in a separate checkout.
No push or pull request is part of this delivery.

## Automated checks

- `python -m unittest discover tests`: 223 tests passed, 3 skipped. Existing subprocess/socket ResourceWarnings remain.
- Seven documentation tests cover order/hierarchy, fragments, partial/all-page failures, targeted retry, repeat reuse
  without fetching, provenance/internal links, preserved and unresolved notes, changed-paragraph quote offsets,
  original Chinese generation without translation, bounded chapter scenes and complete exports.
- JavaScript syntax checks for app, reader and WebMCP scripts; `git diff --check`: passed.
- Tests used the installed TextFold Python and an isolated temporary dependency directory for reportlab.

## Actual browser host

The Codex in-app browser discovered 18 genuine registered tools through its WebMCP capability. Calls used the
host-issued document-specific names, without a synthetic page registry or REST substitute.

- Actual `documentation-import` of `https://www.agent-native.com/docs/#create-an-agent`: one work, 202 source pages,
  ordered sidebar groups, retained code, tables, images and source URLs; fragments are not separate pages.
- Initial fetch: 198 ready and four network failures; successful content opened. `documentation-retry` fetched four
  pages only and reached 202 ready. A later explicit update processed all 202; 17 requests failed and retained old
  snapshots. The final status distinguishes those failures from current successful chapters. No unresolved notes.
- `documentation-import` repeated the same URL and reused the same document without a new generation.
- The final reader has the whole ordered directory and one source chapter in its live zoom scene. WebMCP navigation
  moved from Getting Started to Create an App with an AI Agent, retaining the document identity and source context.
- Annotation create/list/update/delete completed through the host tools. The original mark remained visible and
  editable after retry and explicit update; a second test mark was created and deleted. Exact quote offsets were
  returned and the original mark visibly highlighted its source words in the existing margin-note design.
- Folder create/rename/move and folder-filtered library query round-tripped through the browser tools.
- Zotero query found parent `users/0/XK5TF43K`, enumerated exact attachment `7Q2CCQEP`, imported its existing cache as
  `pdf-cab09c60d336f652`, and opened the PDF reader. Parent `PMG3PDKN` returned its two attachment choices; explicitly
  selecting `9569D2UT` imported that cache. Cache-missing behavior remains covered by the existing Zotero suite.

## Original-language generation

The large site was imported on isolated port 3028 with its generation deliberately unable to resolve a model.
Its Full content remained readable and the job reported `no-model`; it did not start thousands of model requests.

A one-paragraph Chinese documentation fixture was imported through the same browser tool from local port 3029.
The import automatically queued generation, completed with exactly two bounded `gpt-6.1-sol` requests, and the
browser showed Chinese Key-level output with Original selected. `layers/en.json` holds its Chinese base ladder;
there are no `tr-*` layers. A separate small Chinese Markdown test also completed with two real requests.
This establishes the workflow and source-language behavior, not a full-site generated-summary quality review.

## Zoom measurement and limits

Reader rendering/zoom algorithms are unchanged; added reader hooks route cross-chapter notes and label Original.
GPU traces used real Chrome, 1512×982 at 2× pixels, RTX 4060 Ti, on the existing dense PDF `pdf-df8fbf77e90bb2d2`.
Its parsed payload was equal between baseline and implementation.

| Sample | Before dropped/presented | After dropped/presented |
| --- | --- | --- |
| Controlled same-browser slider drag | 3 / 173 (1.70%) | 3 / 171 (1.72%) |

Initial four-gesture runs had small mixed pinch results and unstable Full-click results; one run stopped presenting
frames during dragging. The controlled comparison above and separate Topic/Full interactions with the WebMCP script
enabled/disabled did not reproduce a drag failure. This is limited GPU evidence, not a universal smoothness claim.
The prescribed arXiv `2512.23916` was unavailable in the local daily data, so this existing dense PDF was used.

All import data, notes, folders, settings and model fixtures used a separate temporary data folder. Daily port 3017,
the local bridge, original PDFs, Zotero producer caches and llm-for-zotero were not changed. Full-site source retrieval
depends on network availability; JavaScript-only/authenticated documentation is not supported by the HTML fetcher.
