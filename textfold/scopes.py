"""Physical PDF coverage and explicit reading scopes, independent of navigation anchors."""
import copy
import re

from bs4 import BeautifulSoup

from .tokens import plain

LIMIT = 30


def total(pid):
    import pypdfium2 as pdfium
    from . import store
    from .engine import PDFIUM
    with PDFIUM:
        with pdfium.PdfDocument(str(store.pdir(pid) / "source.pdf")) as pdf:
            return len(pdf)


def page_texts(pid):
    import json
    import pypdfium2 as pdfium
    from . import store
    from .engine import PDFIUM
    d = store.pdir(pid)
    pages = []
    with PDFIUM:
        with pdfium.PdfDocument(str(d / "source.pdf")) as pdf:
            for p in pdf:
                tp = p.get_textpage()
                try:
                    pages.append(tp.get_text_range())
                finally:
                    tp.close()
                    p.close()
    sf = d / "structured_content.json"
    if sf.exists():
        sc = json.loads(sf.read_text(encoding="utf-8"))
        for n, page in enumerate(sc.get("pages", [])):
            i = page.get("page_idx", n)
            if 0 <= i < len(pages) and not pages[i].strip():
                pages[i] = " ".join(str(b.get("content", "")) for b in page.get("blocks", []))
    return pages


def select(request, count, chapters=None):
    kind = request.get("kind")
    if kind == "document":
        return {"kind": kind, "pages": list(range(1, count + 1))}
    if kind == "chapter":
        chapter = (chapters or {}).get(request.get("chapter"))
        if not chapter:
            raise ValueError("This section has no reliable PDF page boundaries; choose physical pages")
        first, last = min(chapter), max(chapter)
        position = int(request.get("position") or first)
        if not first <= position <= last:
            raise ValueError("Reading position is outside the selected section")
        return {"kind": kind, "chapter": request["chapter"], "chapter_pages": chapter,
                "pages": list(range(position, min(last + 1, position + LIMIT)))}
    if kind != "range":
        raise ValueError("Choose a document, section or physical page range")
    pages = set()
    for pair in request.get("ranges", []):
        if len(pair) != 2:
            raise ValueError("A page range needs a first and last page")
        a, b = map(int, pair)
        if not 1 <= a <= b <= count:
            raise ValueError(f"Physical pages must be between 1 and {count}")
        pages.update(range(a, b + 1))
    if not pages:
        raise ValueError("Choose at least one physical page")
    return {"kind": kind, "pages": sorted(pages)}


def _words(text):
    return re.findall(r"[^\W\d_]+", text.casefold())


def content_pages(doc, page_texts, displays=None):
    """Bound whole passages with unique beginning/end anchors in physical reading order.

    Both ends must map. A continuation includes every intervening physical page. Short,
    ambiguous, scan-only or damaged passages remain unassigned, never certified by navigation.
    """
    tokens, owners = [], []
    for n, text in enumerate(page_texts, 1):
        words = _words(text)
        tokens.extend(words)
        owners.extend([n] * len(words))
    anchors = {}
    for i in range(len(tokens) - 3):
        key = tuple(tokens[i:i + 4])
        anchors[key] = -1 if key in anchors else i

    def locate(text):
        words = _words(text)
        if len(words) < 8:
            return []
        a, b = [anchors.get(tuple(w), -1) for w in (words[:4], words[-4:])]
        if a < 0 or b < a:
            return []
        return list(range(owners[a], owners[b + 3] + 1))

    result = {u: locate(plain(v["toks"], doc["atoms"])) for u, v in doc["units"].items()}
    for i, block in enumerate(doc["blocks"]):
        if block.get("html"):
            soup = BeautifulSoup(block["html"], "lxml")
            text = soup.get_text(" ", strip=True)
            pages = locate(text)
            if block["k"] == "eq":
                tags = re.findall(r"\\tag\{([^}]+)\}", " ".join(m.get("alttext", "") for m in soup.find_all("math")))
                found = [displays.get(t, []) for t in tags] if displays else []
                if found and all(len(p) == 1 for p in found):
                    pages = sorted(set(p[0] for p in found))
            result["block:" + str(i)] = pages
    return result


def chapter_pages(doc, mapping):
    result = {}
    # These are the author's actual heading sections, never invented book chapters.
    for chunk in doc["chunks"]:
        spans = [mapping.get(u, []) for u in chunk["units"]]
        spans += [mapping.get("block:" + str(i), []) for i, b in enumerate(doc["blocks"])
                  if b.get("chunk") == chunk["id"] and b.get("html")]
        if spans and all(spans):
            result[chunk["id"]] = sorted(set(p for span in spans for p in span))
    return result


def generation(doc):
    """A generation view of fully covered content; the reader keeps the complete source.

    An unmapped passage needs whole-document coverage. All available outside context is
    explicitly unchecked, and cannot cause more PDF work to be scheduled.
    """
    s = doc["meta"].get("correction") or {}
    if not s or s.get("status") == "done":
        return doc
    checked = set(s.get("checked", []))
    mapping = s.get("content_pages", {})
    def covered(key):
        pages = mapping.get(key, [])
        return bool(pages) and set(pages) <= checked
    out = copy.deepcopy(doc)
    out["units"] = {u: v for u, v in out["units"].items() if covered(u)}
    out["blocks"] = [b for i, b in enumerate(out["blocks"])
                     if (not b.get("html") or covered("block:" + str(i))) and
                     (not b.get("u") or b["u"] in out["units"]) and
                     (not b.get("cap") or b["cap"] in out["units"])]
    for c in out["chunks"]:
        selected = [u for u in c["units"] if u in out["units"]]
        partial = selected != c["units"] or c["id"] not in s.get("chapters", {}) or not set(s["chapters"].get(c["id"], [])) <= checked
        c["units"] = selected
        c["scope_partial"] = partial
        if partial:
            c["title"] += " [selected-range summary / 已核查范围摘要]"
    out["meta"]["scope_context"] = (
        "Generate only the supplied checked passages. Any section aggregate is a selected-range summary, not a "
        "whole-chapter/document conclusion. Outside dependencies below are UNCHECKED extraction; explicitly state "
        "any dependency that materially limits interpretation. Never assume missing text or request additional PDF work.\n" +
        "\n".join(plain(v["toks"], doc["atoms"])[:500] for u, v in doc["units"].items() if u not in out["units"])[:14000])
    outside = []
    for i, block in enumerate(doc["blocks"]):
        if block.get("html") and not covered("block:" + str(i)):
            soup = BeautifulSoup(block["html"], "lxml")
            outside.append(" ".join(m.get("alttext", "") for m in soup.find_all("math")) or soup.get_text(" ",strip=True))
    if outside:
        out["meta"]["scope_context"] += "\nUNCHECKED extracted display/table dependencies:\n" + "\n".join(outside)[:12000]
    out["meta"]["scope_context"] += "\n\n"
    out["edges"] = [e for e in out["edges"] if e["f"] in out["units"] and (e["tk"] != "unit" or e["t"] in out["units"])]
    return out
