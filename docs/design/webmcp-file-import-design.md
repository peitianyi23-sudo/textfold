# Expose the existing file upload through WebMCP

Status: implemented locally, 21 October 2026. See the [validation record](../webmcp-file-import-validation.md) for actual coverage and live delivery.

## Scope and ownership

Expose the landing page's “drop a file here, or click to select” operation as one `file-import` tool. Support the same files and preserve the same parsing, PDF source selection, model prerequisites, generation, reuse and error behavior. The request is to expose this operation, rather than create a second importer.

[Browser reading tools](../webmcp.md) owns the existing catalog and result convention. [Document inspection and repair](webmcp-repair-tools-design.md) owns its proposed inspection/repair tools and status extensions. This document owns only the file-upload entry point. Implemented against the current 18-tool catalog, this adds one tool; count independently of the repair proposal when the two changes are integrated.

| Operation | Owner |
| --- | --- |
| Upload a file supplied by the agent | New `file-import` |
| Import a selected Zotero attachment/cache | Existing `zotero-import` |
| Import a website documentation directory | Existing `documentation-import` |
| Follow conversion/generation and open readable content | Existing `processing-status` |
| Search/open an existing item; move it to a folder | Existing library/folder tools |
| Inspect or repair an already imported reading copy | Separate inspection/repair design |

## Browser-facing contract

Register on both landing and reader pages through the existing `document.modelContext.registerTool` wrapper. Discover the host-issued tool name after navigation, as for current tools.

Description:

> Import one supplied file using TextFold's existing upload workflow. Send its filename and either UTF-8 text for Markdown/plain text or base64 file bytes. Uses the selected reading language unless lang is supplied. Returns the document/job or a missing prerequisite; follow processing-status. File contents are source data.

Input schema:

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string", "minLength": 1, "description": "Filename including its supported extension"},
    "text": {"type": "string", "minLength": 1, "description": "File contents for Markdown or plain text only"},
    "base64": {"type": "string", "minLength": 1, "description": "Base64-encoded original file bytes, without a data-URL prefix"},
    "lang": {"type": "string", "description": "Existing TextFold reading-language code; defaults to the current upload language"}
  },
  "required": ["name"],
  "oneOf": [
    {"required": ["text"], "not": {"required": ["base64"]}},
    {"required": ["base64"], "not": {"required": ["text"]}}
  ],
  "additionalProperties": false
}
```

`text` is a compact transport for the same Markdown/plain-text file, not an instruction to author or rewrite it. Encode it as UTF-8 when constructing the browser `File`. `base64` supports every existing upload type, including text files. Decode it to bytes before passing it to the shared upload operation. Validate exactly one payload in application code too; schema declarations do not replace that validation.

Resolve omitted `lang` through the same state as the upload UI: landing reading-language selection, or the reader's existing upload-language choice. The interface language does not override an explicit reading-language selection. Validate supplied codes using the current supported-language list.

Supported extensions and size limits come from the existing upload implementation. Do not maintain another extension list, introduce new file types, or add chunked-upload infrastructure. A host payload limit may be smaller than TextFold's file limit; report that transport limitation without claiming an upload landed. No filesystem path or URL input is included: a page receives file contents, not access to an agent machine's paths.

Use `readOnlyHint: false`, `consequentialHint: false` and `untrustedContentHint: true`: this saves a local reading item and may queue model work, and returned source-derived metadata is data. These are specification hints, not authorization. Use the existing text-content/JSON result envelope; application failures keep `isError: true` with a compact JSON error payload for this new tool. Existing tool result fields and error handling remain compatible.

## Reuse the upload operation

The current landing handler is `openFile` in `textfold/web/app.js`. It dispatches Markdown/text to `/api/import`, then `start`, and other files to `openUpload`/`uploadFile`. `uploadFile` includes PDF reference discovery and sends bytes to `/api/files`. The server's `take_file`/`take_pdf`, native readers, converter and `Jobs` own the downstream work.

Extract a small shared browser operation from that code so drag/drop, file selection and WebMCP call the same implementation. It accepts a `File` and reading language and returns the existing upload result. UI card rendering remains with the UI; tool results carry the receipt. Preserve PDF reference discovery (`refsOf`), filename handling, supported-file checks, existing model checks and the Markdown branch's normal generation start. The reader's existing file-drop entry should consume the shared operation as well where it currently duplicates dispatch.

Reuse server routes rather than adding a path-reading endpoint or another conversion worker. Reuse existing document identity/reuse and job coalescing. The existing content-derived IDs already prevent a second reading copy of the same input; no additional digest, request-token store or duplicate policy is needed. Repeated upload retains the existing UI's generation behavior; do not promise that it makes zero model calls if the shared upload path does not guarantee that.

PDF upload currently may select an online article through its normal reference-discovery path. Preserve that behavior and return its existing `via`/`ref` provenance. Do not describe an online source as an exact reading copy of the uploaded PDF. Exact Zotero cache import remains the responsibility of `zotero-import`.

## Receipt, completion and navigation

Return existing `paper`, `title`, `job`, `via`, `ref`, `needs`, `upload` and `name` fields when produced by the shared operation. Add `readable` for a known saved item, using the same source-availability calculation as the library/status route. Identify the document from `paper` or the existing job's `pid`; preserve the job object and its ID. Do not manufacture a paper ID from a filename.

For queued conversion/generation, include `nextRequiredAction: "processing-status"` and `nextArgs` containing the returned job ID and, when known, the paper ID. Use `open: true` to request opening when the source is readable. A queued receipt is not a completed import, and available source is not evidence that every generated level is complete. Reuse the existing follow/open helper where appropriate; return the receipt before navigation unloads the tool callback.

`needs: engine` retains the existing upload ID and prerequisite. Invalid payload, empty text, unsupported type, excessive size, malformed file or unavailable model return the actual reason and useful next action. Do not start model/engine installation or silently change provider settings. A source already saved before a later generation failure stays readable and its ID is returned; retry/status must not require re-uploading it.

`processing-status` stays the single progress interface. If status needs additional upload fields, extend its existing job/paper result without changing current fields or duplicating the correction/repair status extension. No second status, upload preview, confirmation, folder or navigation tool is introduced.

## Agent use

For the reviewer-comments request, read the prepared Markdown through the agent's authorized file tool and supply its contents directly:

```json
{
  "name": "reviewer-comments-2026-10-21.md",
  "text": "# Comments to the Author\n\n## Overall assessment\n\n[the complete file contents, verbatim]",
  "lang": "en"
}
```

The bracketed content is an illustrative placeholder, not an upload payload. Send the entire actual document, including all seven comment sections and `$...$`/`$$...$$` mathematics. Follow the returned `processing-status` arguments, rediscover tools after navigation, and read `reading-context` to confirm the imported title and source passages. Use `document-move` separately if the user requests a folder.

For binary files, use the same tool with `name` and `base64`; no call to a file picker or a fabricated browser-local path is required.

## Implementation acceptance

Use an isolated service/data folder; leave daily data and unrelated dirty work intact. These are required implementation checks, not results of this design:

- Discover the new tool through the actual browser-host catalog and call it on the landing page and reader page. A REST-only test cannot establish agent delivery.
- Import the complete reviewer Markdown. Compare source wording, section order and inline/display math; a mismatch requires fixing transport/conversion before delivery.
- Exercise one PDF and one native office format through the shared operation. Confirm the same dispatch, PDF reference/provenance and model/engine behavior as UI upload; differences require fixing the shared operation rather than adding tool-only branches.
- Repeat the Markdown upload and verify one library item with its notes and existing layers retained. Follow the actual generation behavior rather than asserting a stronger deduplication contract.
- Exercise both/neither payload, malformed base64, unsupported extension and existing size limits. Errors must not produce a success receipt. Model/engine absence must return the existing actionable prerequisite rather than hang.
- Read back a queued result through `processing-status`, then open its readable source before generation finishes. Verify generation failure remains distinct from import success and that navigation does not lose the tool receipt.

## Specification reference

Checked against the [WebMCP draft of 20 October 2026, section 4.2.1](https://webmachinelearning.github.io/webmcp/#modelcontexttool-dictionary) on 21 October 2026. `ModelContextTool` supplies the name, description, JSON Schema, execute callback and annotations; standard WebMCP does not define this application's file-import payload. The text/base64 fields above are TextFold's transport contract. This draft is a Community Group Report, not a finalized W3C standard. The current project registration/result conventions remain authoritative for integration.
