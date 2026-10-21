# File-import validation — 21 October 2026

The local `personal` checkout exposes `file-import` on both landing and reader pages. This adds one tool to the existing catalog. There is no server-route change, second importer, or new progress tool. Existing unrelated Zotero edits and design notes were preserved; no commit or push was made.

## Automated checks

- `node --test tests/webmcp-file-import.test.cjs`: seven tests. The real registration callback and shared upload section run in a browser-like test context. Cases cover exact text/math transport, selected/explicit language, base64 Word bytes, PDF reference discovery, invalid payloads, unsupported types, model absence, saved-source receipts after generation failure, and the existing file-size limit.
- `node --check textfold/web/app.js` and `node --check textfold/web/webmcp.js`: passed.
- Existing `test_local_read.py`, `test_pdftext.py`, `test_documentation.py`: 24 tests passed. The PDF suite initially failed while Pillow created its scanned-image fixture (`KeyError: JPEG`); initializing Pillow plugins with `Image.init()` before that suite resolved the fixture failure. Application code was not changed for this environment issue.

## Real browser-host calls

An isolated service at `127.0.0.1:3036` used a temporary data folder. Real import routes, native conversion and the browser's actual WebMCP bridge ran; generation workers were deliberately disabled so the fixture jobs remained queued without model calls. The PDF conversion engine was disabled to exercise native reading.

- Browser discovery returned 19 tools, including the complete `file-import` schema and annotations.
- Landing-page Markdown import returned `md-upload-test-c9b36bdd`, readable source and a queued generation job. `processing-status(open:true)` opened Full while generation remained queued. `reading-context` returned the exact prose and inline math.
- A base64 DOCX imported as `doc-9190a939b8e665a9`, through the native office reader. A base64 PDF imported from the reader page as `pdf-53f66a2cca3084c9`, through the native PDF path (`via: pdf`). Both returned readable source and existing job receipts.
- A note saved through `annotation-create` survived repeating the identical Markdown upload. The repeated call returned the same paper and queued job IDs. This fixture had no completed generated layers, so it does not independently certify preservation of already completed layers.

## Daily service and requested document

`processing-status` reported no jobs before restart. The existing `TextFold Personal` scheduled task was stopped and started, retaining its configured checkout and data root. The model bridge was left running. Browser refresh then discovered `file-import` in the daily service at `127.0.0.1:3017`.

The requested reviewer comments were imported through that tool in English as `md-comments-to-the-author-4e123312`. Its saved `source.md` exactly matches `Z:/draft/DING/paper-reviews/reviewer-comments-2026-10-21.md`, including all headings, original prose and inline/display math. The live reader context confirms the title, overall assessment and seven substantive section headings.

The first caller payload accidentally reduced the display-math delimiters while converting the prepared TeX string. That newly created incorrect item was moved to the library's recoverable `.trash` after stopping its service/job; the corrected full Markdown was imported after restart. This was a caller transformation error, not a tool mutation of supplied text. Only the corrected item remains in the active library.

At source verification the daily generation job was running in `ladder`, with Full already readable. Final `processing-status` readback reports job `6c680c7f99` as `done`, no error, English layers available, all nine source sections processed and eight argument links saved. Generated summaries have not been scientifically reviewed. The isolated service was stopped after validation; its files remain in the temporary test directory for reproduction.
