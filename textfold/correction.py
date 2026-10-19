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
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bs4 import BeautifulSoup

from . import llm, llm_openai, markdown, semantic, store
from .parse import parse
from .tokens import plain

SCHEMA = {"type": "object", "properties": {
    "edits": {"type": "array", "items": {"type": "object", "properties": {
        "before": {"type": "string"}, "after": {"type": "string"}, "reason": {"type": "string"},
        "box": {"type": "array", "items": {"type": "number"}}},
        "required": ["before", "after", "reason"]}},
    "issues": {"type": "array", "items": {"type": "string"}},
    "displays": {"type": "array", "items": {"type": "object", "properties": {
        "number": {"type": "string"}, "present": {"type": "boolean"},
        "box": {"type": "array", "items": {"type": "number"}}},
        "required": ["number", "present", "box"]}}}, "required": ["edits", "issues", "displays"]}
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


def page_ranges(text, page_texts):
    """Align reading-order text anchors once, including finalized Markdown without coordinates.

    Unmapped pages keep the full extraction: coverage takes precedence over payload size.
    Overlapping paragraph context covers page continuations; edits still need unique locators.
    """
    tokens = list(re.finditer(r"[a-zA-Z]{3,}", text.lower()))
    source = [m[0] for m in tokens]
    out = []
    for page in page_texts:
        words = re.findall(r"[a-zA-Z]{3,}", page.lower())
        matches = difflib.SequenceMatcher(None, source, words, autojunk=False).get_matching_blocks()
        hits = [b for b in matches if b.size >= 4]
        if not hits:
            out.append((0, len(text)))
            continue
        first = tokens[min(b.a for b in hits)].start()
        last = tokens[max(b.a + b.size - 1 for b in hits)].end()
        start = text.rfind("\n\n", 0, max(0, first - 700))
        end = text.find("\n\n", min(len(text), last + 700))
        out.append((max(0, start), len(text) if end < 0 else end))
    return out


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
    started = time.perf_counter()
    metrics = {"requests": [], "render_seconds": 0., "validation_seconds": 0., "mapping_seconds": 0.}
    original = (d / "source.md").read_text(encoding="utf-8")
    image_map = _images(original, (d / "source.html").read_text(encoding="utf-8"))
    with PDFIUM:
        pdf = pdfium.PdfDocument(str(d / "source.pdf"))
        total = len(pdf)
    def check():
        if stop is not None and stop.is_set():
            raise llm.Stopped()
    def request(prompt, schema, images, page, stage):
        check()
        now = time.perf_counter()
        rec = {"page": page + 1, "stage": stage, "prompt_chars": len(prompt), "images": len(images)}
        try:
            return llm_openai.vision(prompt, schema, spec, images)
        except Exception as e:
            rec["error"] = str(e)
            raise
        finally:
            rec["seconds"] = time.perf_counter() - now
            metrics["requests"].append(rec)
    def picture(page):
        now = time.perf_counter()
        with PDFIUM:
            p = pdf[page]
            bitmap = p.render(scale=2.4)
            try:
                result = bitmap.to_pil().convert("RGB").copy()
            finally:
                bitmap.close(); p.close()
        metrics["render_seconds"] += time.perf_counter() - now
        return result
    def png(image):
        buf = io.BytesIO(); image.save(buf, format="PNG"); return buf.getvalue()
    try:
        now = time.perf_counter()
        pages = []
        with PDFIUM:
            for index in range(total):
                p = pdf[index]; tp = p.get_textpage()
                try: pages.append(tp.get_text_range())
                finally: tp.close(); p.close()
        # A scan can use the extractor's reading-order blocks without any text layer.
        sf = d / "structured_content.json"
        if sf.exists():
            sc = json.loads(sf.read_text(encoding="utf-8"))
            for n, page in enumerate(sc.get("pages", [])):
                i = page.get("page_idx", n)
                if i < total and not pages[i].strip():
                    pages[i] = " ".join(str(b.get("content", "")) for b in page.get("blocks", []))
        snapshot = draft["text"]
        history_start = len(draft["history"])
        ranges = page_ranges(snapshot, pages)
        metrics["mapping_seconds"] = time.perf_counter() - now
        s.update(status="checking", done=draft["page"], total=total, error="")
        _write(d, "correction.json", s)
        def first(page):
            check()
            image = picture(page)
            a, b = ranges[page]
            local = snapshot[a:b]
            prompt = (f"Check physical PDF page {page + 1} of {total} IN FULL: every paragraph, formula, caption, "
                "table and reading-order transition. The image is this page. The extraction below includes surrounding "
                "paragraph context. Correct only differences visible on THIS page, preserving printed author symbols "
                "even if scientifically inconsistent. Ignore running headers, footers, stamps and page numbers. "
                "Preserve image paths/HTML; avoid whitespace-only LaTeX edits. Return exact UNIQUE before substrings "
                "with enough unchanged context, corrected Markdown after, and PDF evidence reason. For each edit "
                "give box=[left,top,right,bottom] in 0..1 image coordinates covering the entire changed paragraph or "
                "equation INCLUDING its number, not just one symbol. Explicitly restore omitted displays by inserting "
                "them at a unique surrounding text anchor. Preserve EVERY printed equation number using \\tag{n}. "
                "displays: inventory EVERY numbered display visible on this page, with number, box covering the whole "
                "equation, and present=true only if the CURRENT extraction includes every line AND the number. "
                "Do not count prose references to equations as displays. A readable missing number or equation needs "
                "an edit, not just an issue. "
                "A page-spanning change must be reported as an issue unless the visible evidence establishes it. "
                "If source content for this page is missing from the context, report it in issues; never claim agreement. "
                "Report only real extraction omissions or unreadable/ambiguous regions in issues; never infer from "
                "physics. Context outside this page is expected, not an issue. Do not report absence of captions/tables "
                "on a page that has none.\nCURRENT extraction:\n" + local)
            return request(prompt, SCHEMA, [png(image)], page, "full-page"), image, local
        # Only two first comparisons in flight; do not queue a whole library of model requests.
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = {}
            begin = draft["page"]
            for page in range(begin, min(total, begin + 2)):
                pending[page] = pool.submit(first, page)
            for page in range(begin, total):
                progress("PDF 校对中", page, total)
                result, image, local = pending.pop(page).result()
                check()
                for change in draft["history"][history_start:]:
                    for edit in change["edits"]:
                        if edit["before"] in local:
                            local = local.replace(edit["before"], edit["after"], 1)
                missing = [r for r in result.get("displays", []) if not r["present"]]
                if missing:
                    # Explicit inventory prevents a readable omitted display being left as a vague issue.
                    crops = []
                    for r in missing:
                        box = r["box"]
                        if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
                            box = [0, 0, 1, 1]
                        w, h = image.size
                        crops.append(png(image.crop((int(max(0,box[0]-.05)*w), int(max(0,box[1]-.05)*h),
                                                    int(min(1,box[2]+.05)*w), int(min(1,box[3]+.05)*h)))))
                    extra = request("Restore the following numbered display equations, including every line and printed "
                        "number as \\tag{n}, from the supplied original PDF regions. They were inventoried as incomplete "
                        "in CURRENT extraction. Return exact unique insertion/replacement anchors. Do not repeat edits "
                        "already proposed below. Preserve author symbols; if unreadable, report the exact ambiguity. "
                        "Copy each region's original full-page box into its proposed edit.\n"+
                        json.dumps({"displays":missing,"already_proposed":result["edits"]},ensure_ascii=False)+
                        "\nCURRENT extraction:\n"+local,SCHEMA,crops,page,"missing-display-regions")
                    result["edits"].extend(extra["edits"])
                    result["issues"].extend(extra["issues"])
                feedback = []
                for attempt in range(3):
                    candidates, rejected = [], []
                    # Simultaneous comparisons share a snapshot. Resolve overlaps against the current draft,
                    # never apply an offset calculated before a different page changed the same passage.
                    text = draft["text"]
                    for edit in result["edits"]:
                        if edit["before"] == edit["after"]:
                            continue
                        try:
                            candidate = patches(text, [edit])
                            # Enforce page-local ownership even when a passage is unique elsewhere.
                            if edit["before"] not in local:
                                raise ValueError("Proposed change lies outside this page's supplied extraction")
                            text = candidate; candidates.append(edit)
                        except ValueError as e:
                            rejected.append({"before": edit["before"], "error": str(e)})
                    draft["issues"] = [x for x in draft["issues"] if x["page"] != page + 1]
                    draft["issues"].extend({"page": page + 1, "text": x} for x in result["issues"])
                    if not candidates and not rejected:
                        break
                    crops = []
                    for e in candidates:
                        box = e.get("box", [])
                        if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
                            box = [0, 0, 1, 1]
                        # Include surrounding lines, not just the symbol claimed to be wrong.
                        w, h = image.size
                        box = [max(0, box[0]-.04), max(0, box[1]-.04), min(1, box[2]+.04), min(1, box[3]+.04)]
                        crops.append(png(image.crop((int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h)))))
                    if candidates:
                        now = time.perf_counter()
                        rec = {"page":page+1,"stage":"independent-region-review","images":len(crops)}
                        try:
                            accepted, review_issues = review(candidates, crops, spec,
                                f"{page+1}, one context crop per indexed edit; check the corrected result against the printed region")
                        except Exception as e:
                            rec["error"] = str(e)
                            raise
                        finally:
                            rec["seconds"] = time.perf_counter()-now
                            metrics["requests"].append(rec)
                        feedback = review_issues
                        if review_issues:
                            draft.setdefault("reviews", []).append({"page": page+1, "issues": review_issues})
                        if accepted:
                            now = time.perf_counter()
                            candidate = patches(draft["text"], accepted)
                            # Parse once per accepted batch; the final publish also validates all images.
                            render(candidate, image_map)
                            metrics["validation_seconds"] += time.perf_counter()-now
                            draft["text"] = candidate
                            draft["history"].append({"page":page+1,"edits":accepted,"reviewed":True})
                            for e in accepted:
                                local = local.replace(e["before"], e["after"], 1)
                        for issue in review_issues:
                            if issue["verdict"] == "unresolved":
                                draft["issues"].append({"page":page+1,"text":issue["before"][:180]+": "+issue["reason"]})
                    else:
                        accepted = []
                    # The independent call has already inspected every accepted after against PDF.
                    # Revisit only rejected/stale locations, not an unchanged full page a second time.
                    if not rejected:
                        break
                    if attempt == 2:
                        draft["issues"].append({"page":page+1,"text":"Could not locate proposed PDF corrections: "+json.dumps(rejected,ensure_ascii=False)})
                        break
                    result = request("Region verification pass. Re-locate only these stale/overlapping edits against "
                        "the page image and CURRENT extraction. Already reviewed changes must retain printed author "
                        "symbols. Do not change other passages. Return edits/issues.\n"+
                        json.dumps({"rejected":rejected,"independent_review":feedback},ensure_ascii=False)+
                        "\nCURRENT extraction:\n"+local, SCHEMA, [png(image)], page, "overlap-resolution")
                draft["page"] = page + 1
                _write(d, "correction-work.json", draft)
                s.update(done=page+1, issues=draft["issues"])
                _write(d, "correction.json", s)
                image.close()
                if page + 2 < total:
                    pending[page+2] = pool.submit(first, page+2)
        publish(pid, draft["text"], s)
        s.update(status="done", model=spec["id"], edits=sum(len(h["edits"]) for h in draft["history"]), finished=store.stamp())
        progress("PDF 校对中", total, total)
    except Exception as e:
        s.update(status="stopped" if isinstance(e,llm.Stopped) else "error", error=str(e))
        raise
    finally:
        with PDFIUM:
            pdf.close()
        metrics["wall_seconds"] = time.perf_counter()-started
        s["timing"] = metrics
        _write(d,"correction.json",s)
