# Browser reading tools

TextFold registers 18 tools with `document.modelContext.registerTool` on its landing and reader pages. A browser host
with WebMCP support discovers and invokes them directly. Browsers without WebMCP keep the normal interface; TextFold
does not install a synthetic registry or claim browser support through a REST manifest.

The registration follows the [WebMCP imperative API](https://github.com/webmachinelearning/webmcp). Tool results use
text content containing JSON, including actionable failures. The browser may attach a document-specific suffix to
tool names; discover the current catalog again after navigation.

| Tools | Purpose |
| --- | --- |
| `library-query`, `library-open` | Find and open existing reading documents; list folders |
| `zotero-query`, `zotero-import` | Find items, enumerate exact attachments, import the selected cached PDF |
| `documentation-preview`, `documentation-import` | Inspect a directory without writing, or import it directly as one work |
| `documentation-update`, `documentation-retry` | Explicit source refresh, or fetch only failed pages |
| `folder-create`, `folder-rename`, `document-move` | Organize the existing library |
| `reading-context`, `reading-navigate` | Current selection, original passage/formula and surrounding context; chapter/unit navigation |
| `annotation-list`, `annotation-create`, `annotation-update`, `annotation-delete` | Saved notes/highlights in the existing notes format |
| `processing-status` | Import/generation jobs, readable content, failed chapters, unresolved annotations |

An annotation is written only when the user requests saving or marking. Asking about a passage does not create a
note. New marks require a source unit and a unique exact quote from that unit; generated summaries are not treated
as author text. `reading-context` returns source text and a paged outline (40 sections by default, up to 100).

## Documentation sets

The importer selects the documentation root from the starting path and reads the largest navigation directory
within that root, preserving its order and expandable group hierarchy. Same-page fragments collapse to one source
page; unrelated site paths stay out. A site without a readable directory returns an actionable error instead of
guessing a whole-site crawl. Content must be present in the server's HTML; sign-in and JavaScript-only sites may
require another source.

One library item stores the directory in `documentation.json`, individual page snapshots in `pages/`, and the composed
semantic document in `source.html`. Chapters retain source URLs; headings, code, images, tables and matching internal
chapter links use the existing semantic reader. Images use the existing local image importer.

The live reader opens one source chapter at a time, with the ordered directory and previous/next controls in the
existing top bar. This bounds the zoom scene for large documentation sets. All chapters remain in the same work;
generation and whole-document HTML export use the complete document. Unit ids stay global, so chapter changes and
the notes menu can navigate to a saved mark in another chapter.

Import starts the normal generation queue automatically, while Full remains readable. `reading_mode: original`
asks the model for concise levels in each passage's original language, without invoking translation. The historical
base-layer storage slot remains `layers/en.json`; the interface labels it Original for these documents.

Repeated imports open the existing work without generation. Explicit update refreshes the directory and pages;
retry fetches only failed pages, retaining successful snapshots. A failed update fetch may retain the previous
chapter snapshot, and is still reported as failed. The Sources menu names missing chapters and offers retry.

On updates, source-page identity plus original text/quotes remap paragraph notes. Section anchors retain their
stable chapter/heading identity. Unmatched annotations keep their text and original quote with `unresolved: true`
and no active passage anchor; the result and Sources menu report them. Existing generated layers are reconciled
against the changed source and completed incrementally by the generation queue. The browser restores the reading
level and exact source passage across reloads, falling back to its source page if that passage changed.

## Zotero

Use `zotero-query` with an exact `item` (`users/0/KEY` or `groups/ID/KEY`) to enumerate attachments, then pass the
selected attachment key to `zotero-import`. Multiple PDFs return `needs: attachment` rather than choosing another
version. A missing exact cache returns `needs: zotero-cache` with a retry instruction. TextFold reads the existing
llm-for-zotero cache; it neither produces that cache nor modifies the original PDF. New cached PDF imports queue
original-language generation; repeated imports open the existing copy without regeneration.

## Validation

Run `python -m unittest discover tests`. `tests/test_documentation.py` covers directory order/hierarchy, fragment
deduplication, readable partial imports, failed-page-only retry, repeated import reuse, source provenance, internal
links, update remapping, unresolved notes, all-page failure recovery, and Chinese base-layer generation without a
translation call. Browser acceptance must additionally exercise the host's actual tool catalog and calls; REST
tests alone do not establish WebMCP delivery.
