"""PDF-backed correction of the imported reading copy, before generating its levels.

The original extraction and layers remain in correction-original/. A resumable draft is checked
page by page and published only after the whole PDF has been visited. Zotero's cache is never written.
"""
import copy
import difflib
import io
import json
import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

from . import llm, llm_openai, markdown, semantic, store
from .parse import parse
from .tokens import plain

SCHEMA = {"type": "object", "properties": {
    "edits": {"type": "array", "items": {"type": "object", "properties": {
        "before": {"type": "string"}, "after": {"type": "string"}, "reason": {"type": "string"}},
        "required": ["before", "after", "reason"]}},
    "issues": {"type": "array", "items": {"type": "string"}}}, "required": ["edits", "issues"]}
REVIEW = {"type": "object", "properties": {"decisions": {"type": "array", "items": {
    "type": "object", "properties": {"index": {"type": "integer"},
    "verdict": {"type": "string", "enum": ["accept", "reject", "unresolved"]},
    "reason": {"type": "string"}}, "required": ["index", "verdict", "reason"]}}}, "required": ["decisions"]}


def review(edits, images, spec, pages):
    """A separate call sees both versions, so it can reject a plausible but unfaithful correction."""
    if not edits:
        return [], []
    prompt = (f"Independently verify these proposed extraction corrections against original PDF images of pages {pages}. "
              "For EVERY indexed edit, inspect the original printed content. ACCEPT only if the after text matches the PDF "
              "and the before text has a real extraction error. REJECT an unnecessary edit or an edit that changes what "
              "is actually printed, including any author typo/inconsistency, even if after is better science, grammar or "
              "more consistent notation. In particular inspect individual bold/italic letters, accents, subscripts, signs, "
              "integration factors and paragraph boundaries; do not endorse a reason just because it sounds plausible. "
              "Use UNRESOLVED when the image cannot establish the change. Explain the visible evidence, not a physics "
              "argument. Text outside these images is unresolved. Return one decision per index.\n\n" +
              json.dumps([{**e, "index": i} for i, e in enumerate(edits)], ensure_ascii=False))
    result = llm_openai.vision(prompt, REVIEW, spec, images)
    decisions = result["decisions"]
    if sorted(x["index"] for x in decisions) != list(range(len(edits))):
        raise RuntimeError("PDF edit verification did not return a decision for every proposed change")
    accepted, issues = [], []
    for decision in sorted(decisions, key=lambda x: x["index"]):
        edit = edits[decision["index"]]
        if decision["verdict"] == "accept":
            accepted.append({**edit, "verification": decision["reason"]})
        else:
            issues.append({"before": edit["before"], "verdict": decision["verdict"], "reason": decision["reason"]})
    return accepted, issues


def state(pid):
    f = store.pdir(pid) / "correction.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def _write(d, name, value):
    f = d / name
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)


def queue(pid, reset=False):
    """Called only for a newly imported PDF, or an explicit repair request for an existing one."""
    d = store.pdir(pid)
    if reset:
        (d / "correction-work.json").unlink(missing_ok=True)
    if pid.startswith("pdf-") and (d / "source.md").exists() and (reset or not state(pid)):
        _write(d, "correction.json", {"status": "queued", "done": 0, "total": 0, "issues": []})


def pending(pid):
    s = state(pid)
    return bool(s and s["status"] != "done")


def patches(text, edits):
    """Exact replacements only. A stale/ambiguous locator must be checked again, never guessed."""
    for e in edits:
        before, after = e["before"], e["after"]
        if not before or text.count(before) != 1:
            raise ValueError("PDF correction did not uniquely locate its original passage")
        if before == after:
            raise ValueError("PDF correction returned an unchanged replacement")
        text = text.replace(before, after, 1)
    return text


def _images(old_md, old_html):
    """An import renamed its images; reuse those copies rather than reaching into its old cache."""
    raw, _ = markdown.to_html(old_md)
    src = [i.get("src") for i in BeautifulSoup(raw, "lxml").find_all("img")]
    dst = [i.get("src") for i in BeautifulSoup(old_html, "lxml").find_all("img")]
    if len(src) != len(dst):
        raise RuntimeError("The imported image list needs reconciliation before PDF correction")
    return dict(zip(src, dst))


def render(md, image_map):
    html, _ = markdown.to_html(md)
    # A model may fix a caption, never remove or substitute the original paper's images.
    srcs = [i.get("src") for i in BeautifulSoup(html, "lxml").find_all("img")]
    if srcs != list(image_map):
        raise ValueError("PDF correction changed the paper's image references")
    return semantic.normalize(html, resolve_img=image_map.get, sizes=True)


def _signature(unit, atoms):
    # Atom ids are sequential, so compare their content, not their assigned numbers.
    return json.dumps([{**t, **({"a": atoms[t["a"]]} if "a" in t else {})} for t in unit["toks"]], sort_keys=True)


def equations(doc, chunks=None):
    """Displayed formulas restored in a corrected PDF also belong in its reading agents' context."""
    if not doc["meta"].get("correction"):
        return ""
    out = []
    for block in doc["blocks"]:
        if chunks is not None and block.get("chunk") not in chunks:
            continue
        if block.get("html"):
            soup = BeautifulSoup(block["html"], "lxml")
            out.extend(m.get("alttext", "") for m in soup.find_all("math", attrs={"display": "block"}) if m.get("alttext"))
    return ("\n\nOriginal displayed equations, for context (cite the surrounding author's paragraphs):\n" +
            "\n\n".join("$$" + x + "$$" for x in out)) if out else ""


def reconcile(old, new, layers, notes):
    """Retain healthy units and remap their atom references. Changed units get fresh generation.

    User annotations are retained, including their original quotes and conversations. A changed
    passage loses its old token offsets; its quote remains available to the reader's anchor resolver.
    """
    before, after = list(old["units"]), list(new["units"])
    a = [_signature(old["units"][u], old["atoms"]) for u in before]
    b = [_signature(new["units"][u], new["atoms"]) for u in after]
    same = {}
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for block in matcher.get_matching_blocks():
        same.update(zip(before[block.a:block.a + block.size], after[block.b:block.b + block.size]))
    atom_map = {}
    for x, y in same.items():
        for t, v in zip(old["units"][x]["toks"], new["units"][y]["toks"]):
            if "a" in t:
                atom_map[t["a"]] = v["a"]

    def remap(value):
        if isinstance(value, dict):
            return {k: atom_map.get(v, v) if k == "a" and isinstance(v, str) else remap(v) for k, v in value.items()}
        return [remap(v) for v in value] if isinstance(value, list) else value

    # A retained generated sentence may use a formula from elsewhere in its section.
    for aid, atom in old["atoms"].items():
        if aid not in atom_map:
            matches = [k for k, v in new["atoms"].items() if v == atom]
            if len(matches) == 1:
                atom_map[aid] = matches[0]

    def atom_ids(v):
        if isinstance(v, dict):
            return ({v["a"]} if isinstance(v.get("a"), str) else set()) | set().union(*(atom_ids(x) for x in v.values()))
        return set().union(*(atom_ids(x) for x in v)) if isinstance(v, list) else set()

    changed = set(after) - set(same.values())
    affected = {u["chunk"] for k, u in new["units"].items() if k in changed}
    def bodies(doc, cid):
        return [(b["k"], b.get("html")) for b in doc["blocks"] if b.get("chunk") == cid and b.get("html")]
    context_changed = {c["id"] for c in new["chunks"] if bodies(old, c["id"]) != bodies(new, c["id"])}
    affected.update(context_changed)
    old_chunks = {c["id"]: c for c in old["chunks"]}
    for c in new["chunks"]:
        prev = old_chunks.get(c["id"])
        if not prev or prev["title"] != c["title"] or [same.get(u) for u in prev["units"]] != c["units"]:
            affected.add(c["id"])
    out = {}
    for name, layer in layers.items():
        layer = copy.deepcopy(layer)
        layer["units"] = {same[u]: remap(z) for u, z in layer["units"].items()
                          if u in same and new["units"][same[u]]["chunk"] not in context_changed and atom_ids(z) <= atom_map.keys()}
        affected.update(new["units"][u]["chunk"] for u in after if u not in layer["units"])
        layer["chunks"] = {c: remap(z) for c, z in layer.get("chunks", {}).items()
                           if c not in affected and atom_ids(z) <= atom_map.keys()}
        if name == "en":
            layer["edges"] = []  # argument links are rebuilt from the corrected source
        layer["incomplete"] = True
        out[name] = layer

    data = copy.deepcopy(notes)
    if data:
        texts = {u: plain(v["toks"], new["atoms"]) for u, v in new["units"].items()}
        chunk_map = {}
        for c in old["chunks"]:
            destinations = {new["units"][same[u]]["chunk"] for u in c["units"] if u in same}
            if len(destinations) == 1:
                chunk_map[c["id"]] = next(iter(destinations))
        for n in data["notes"]:
            anchor = n["anchor"]
            uid = anchor.get("unit")
            if uid in same:
                anchor["unit"] = same[uid]
                anchor["section"] = new["units"][same[uid]]["chunk"]
            elif uid:
                quote = anchor.get("quote", {}).get("exact", "")
                found = [u for u, t in texts.items() if quote and quote in t]
                anchor["unit"] = found[0] if len(found) == 1 else None
                if anchor["unit"]:
                    anchor["section"] = new["units"][anchor["unit"]]["chunk"]
                anchor.update(tokens=None, sents=[], extraction_changed=True)
            elif anchor.get("section") in chunk_map:
                anchor["section"] = chunk_map[anchor["section"]]
            # Historical answers stay historical; do not point their old citations at unrelated new ids.
            for turn in n.get("thread", []):
                turn["cites"] = [same[u] for u in turn.get("cites", []) if u in same]
                turn["a"] = re.sub(r"\[\[([^\]]+)\]\]", lambda m: "[[" + same.get(m[1], "?") + "]]", turn.get("a", ""))
    return out, data, affected


def publish(pid, text, s):
    d = store.pdir(pid)
    backup = d / "correction-original"
    backup.mkdir(exist_ok=True)
    for name in ("source.md", "source.html", "notes.json", "layout.json", "structured_content.json"):
        f = d / name
        if f.exists() and not (backup / name).exists():
            shutil.copy2(f, backup / name)
    if (d / "layers").exists() and not (backup / "layers").exists():
        shutil.copytree(d / "layers", backup / "layers")
    old_md = (d / "source.md").read_text(encoding="utf-8")
    if text == old_md:
        return
    old_html = (d / "source.html").read_text(encoding="utf-8")
    html = render(text, _images(old_md, old_html))
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    layers = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in (d / "layers").glob("*.json")}
    nf = d / "notes.json"
    notes = json.loads(nf.read_text(encoding="utf-8")) if nf.exists() else None
    updated, notes, affected = reconcile(parse(old_html, meta), parse(html, meta), layers, notes)
    # Each file is replaced atomically; server readers share the source lock while this set is published.
    with store.SOURCE_LOCK:
        for name, value in updated.items():
            store.write(pid, name, value)
        if nf.exists():
            from . import notes as user_notes
            with user_notes._LOCK:
                # Re-read here so a note saved during the background check is not lost.
                current = json.loads(nf.read_text(encoding="utf-8"))
                _, notes, _ = reconcile(parse(old_html, meta), parse(html, meta), layers, current)
                _write(d, "notes.json", notes)
        for name, value in (("source.md", text), ("source.html", html)):
            tmp = d / (name + ".tmp")
            tmp.write_text(value, encoding="utf-8")
            tmp.replace(d / name)
        # Extraction blocks remain the original engine output. Their PDF geometry is still useful
        # for matching corrected paragraphs; do not rerun MinerU or discard a scan's coordinates.
    s["affected"] = sorted(c for c in affected if c)


def run(pid, spec, progress=lambda *a: None, stop=None):
    s = state(pid)
    if not s or s["status"] == "done":
        return
    d = store.pdir(pid)
    work = d / "correction-work.json"
    draft = json.loads(work.read_text(encoding="utf-8")) if work.exists() else {
        "text": (d / "source.md").read_text(encoding="utf-8"), "page": 0, "history": [], "issues": []}
    import pypdfium2 as pdfium
    from .engine import PDFIUM
    with PDFIUM:
        pdf = pdfium.PdfDocument(str(d / "source.pdf"))
        total = len(pdf)
    try:
        s.update(status="checking", done=draft["page"], total=total, error="")
        _write(d, "correction.json", s)
        for page in range(draft["page"], total):
            progress("PDF 校对中", page, total)
            images = []
            detail_images = []
            indexes = range(max(0, page - 1), min(total, page + 2))
            for index in indexes:
                with PDFIUM:
                    p = pdf[index]
                    bitmap = p.render(scale=2.4)
                    try:
                        buf = io.BytesIO()
                        picture = bitmap.to_pil().convert("RGB")
                        picture.save(buf, format="PNG")
                        images.append(buf.getvalue())
                        if index == page:
                            width, height = picture.size
                            for box in ((0, 0, width * .55, height * .55), (width * .45, 0, width, height * .55),
                                        (0, height * .45, width * .55, height), (width * .45, height * .45, width, height)):
                                crop = io.BytesIO()
                                picture.crop(tuple(int(v) for v in box)).save(crop, format="PNG")
                                detail_images.append(crop.getvalue())
                    finally:
                        bitmap.close()
                        p.close()
            feedback = ""
            uncertain = {}
            for attempt in range(3):
                if stop is not None and stop.is_set():
                    raise llm.Stopped()
                prompt = (f"Check physical PDF page {page + 1} of {total} in full: prose, all formulas, tables, "
                          f"captions and paragraph order. Images in order show pages {[i + 1 for i in indexes]}; "
                          "neighbor pages supply context and paragraph continuations. Compare the current extraction below "
                          "directly with those images. Correct OCR, math/text boundaries, broken words and paragraph "
                          "boundaries; retain the author's words and symbols. Do not rewrite, summarize, modernize notation "
                          "or correct the author's science. Ignore running headers, footers, publisher stamps and page numbers, "
                          "which the reading copy intentionally omits. Preserve image paths and figure HTML. Avoid whitespace-only "
                          "LaTeX changes. Before each edit, locate the difference visibly in the PDF. Return edits as exact, "
                          "unique substrings of the CURRENT extraction (before), the corrected Markdown (after), and a "
                          "specific PDF-grounded reason. Include enough unchanged context to make before unique. "
                          "An empty edits array means no further evidenced change. Report unresolved regions in issues, "
                          "including their page and quoted context; never guess. "
                          + ("This is a verification pass: re-read the corrected result against the images, including each "
                             "changed formula and its surrounding paragraph. Look for remaining errors and introduced "
                             "omissions, not agreement with a previous model response. " if attempt else "") +
                          feedback + "\n\nCURRENT extraction:\n" + draft["text"])
                result = llm_openai.vision(prompt, SCHEMA, spec, images)
                edits = result["edits"]
                draft["issues"] = [x for x in draft["issues"] if x["page"] != page + 1]
                draft["issues"].extend({"page": page + 1, "text": x} for x in result["issues"])
                if not edits:
                    break
                text, accepted, rejected = draft["text"], [], []
                for edit in edits:
                    if edit["before"] == edit["after"]:
                        continue
                    try:
                        candidate = patches(text, [edit])
                        render(candidate, _images((d / "source.md").read_text(encoding="utf-8"),
                                                  (d / "source.html").read_text(encoding="utf-8")))
                        text = candidate
                        accepted.append(edit)
                    except ValueError as e:
                        rejected.append({"before": edit["before"], "error": str(e)})
                accepted, review_issues = review(accepted, images + detail_images, spec,
                    f"{[i + 1 for i in indexes]} in order, followed by four enlarged overlapping quadrants "
                    f"(top left, top right, bottom left, bottom right) of page {page + 1}")
                text = patches(draft["text"], accepted)
                for issue in review_issues:
                    if issue["verdict"] == "unresolved":
                        uncertain[issue["before"]] = issue["reason"]
                    else:
                        uncertain.pop(issue["before"], None)
                for edit in accepted:
                    uncertain.pop(edit["before"], None)
                feedback = ("\nThese proposed edits were NOT applied because their before substring was not an exact unique "
                            "match (or changed an image). Locate them afresh in CURRENT extraction, using its literal "
                            "characters and escapes: " + json.dumps(rejected, ensure_ascii=False)) if rejected else ""
                if review_issues:
                    feedback += ("\nIndependent PDF review did NOT apply these changes. Keep the printed author content; "
                                 "do not re-propose these unless the supplied images establish different evidence: " +
                                 json.dumps(review_issues, ensure_ascii=False))
                draft["text"] = text
                if accepted:
                    draft["history"].append({"page": page + 1, "edits": accepted, "reviewed": True})
                if attempt == 2 and rejected:
                    draft["issues"].append({"page": page + 1, "text": "Could not locate proposed PDF corrections: " +
                                           "; ".join(e["before"][:180] for e in rejected)})
            draft["issues"].extend({"page": page + 1, "text": before[:180] + ": " + reason}
                                   for before, reason in uncertain.items())
            draft["page"] = page + 1
            _write(d, "correction-work.json", draft)
            s.update(done=page + 1, issues=draft["issues"])
            _write(d, "correction.json", s)
        publish(pid, draft["text"], s)
        s.update(status="done", model=spec["id"], edits=sum(len(h["edits"]) for h in draft["history"]), finished=store.stamp())
        _write(d, "correction.json", s)
        progress("PDF 校对中", total, total)
    except Exception as e:
        s.update(status="stopped" if isinstance(e, llm.Stopped) else "error", error=str(e))
        _write(d, "correction.json", s)
        raise
    finally:
        with PDFIUM:
            pdf.close()
