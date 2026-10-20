"""Generate a paper in a language: fetch (an arXiv paper), parse, the English ladder and links (once), the translation.

Every step reports through `progress(stage, done, total)`; the server turns that into a progress bar. A set `stop`
(a threading.Event) ends it with llm.Stopped at the next step: what the model has already written stays in the cache,
so the same generation started again goes on from there.
"""
import urllib.error

from . import biorxiv, epmc, github, ladder, links, llm, models, scopes, store, translate, webpage, wiki
from .fetch import fetch


def task(cfg, name):
    """The model spec a task runs with: its reasoning level from the settings (models.for_task)."""
    return models.for_task(llm.spec_of(cfg), name)


def generate(ref, lang, cfg, force=False, jobs=4, progress=lambda *a: None, log=lambda *a: None, stop=None, scope=None, original=False):
    def check():
        if stop is not None and stop.is_set():
            raise llm.Stopped()

    pid = store.resolve(ref)
    progress("fetch", 0, 1)
    if store.is_imported(pid):   # stored when it was opened (local.py), or fetched once from Europe PMC (epmc.py)
        if pid.startswith(("pmc", "ppr")):
            epmc.fetch(pid)
        elif pid.startswith(("biorxiv-", "medrxiv-")):
            biorxiv.fetch(pid, progress)
        elif pid.startswith("wiki-"):
            wiki.fetch(pid)
        elif pid.startswith("gh-"):
            github.fetch(pid)
        elif pid.startswith("web-"):
            webpage.fetch(pid)
        d = store.pdir(pid)
    else:
        try:
            d = fetch(pid, store.DATA)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise RuntimeError("no-html")  # the app shows its own sentence for this
            raise
    check()
    if original:
        import json
        f = d / "meta.json"
        meta = json.loads(f.read_text(encoding="utf-8"))
        meta["reading_mode"] = "original"
        f.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    from . import correction
    correction.prepare_scope(pid)
    check()
    first_scope = scope
    while correction.pending(pid) or first_scope is not None:
        if cfg is None:
            raise RuntimeError("No model is available for PDF checking")
        correction.run(pid, cfg, progress=progress, stop=stop, scope=first_scope)
        first_scope = None
        check()
        if (correction.state(pid) or {}).get("status") != "done":
            generate_scope(pid, lang, cfg, jobs, progress, log, stop, force)
    if (correction.state(pid) or {}).get("status") in ("awaiting-scope", "scope-done"):
        # Opening a long extraction must never start summaries of unchecked content.
        if cfg is not None and (correction.state(pid) or {}).get("checked"):
            generate_scope(pid, lang, cfg, jobs, progress, log, stop, force)
        progress("done", 1, 1)
        return pid
    progress("parse", 0, 1)
    doc = store.parsed(pid)
    if doc["meta"].get("reading_mode") == "original":
        lang = "en"   # the base layer slot holds the source language; no translation task
    cache = d / "llm-cache"
    en = store.read(pid, "en")
    if cfg is None and (en is None or en.get("incomplete") or force or (lang != "en" and store.read(pid, f"tr-{lang}") is None)):
        # fetched and parsed, so it can be read as written; its levels need a model
        raise RuntimeError("No model is available: install Claude Code, Codex or Pi, or add an API provider in the settings")
    model = llm.label(cfg) if cfg else ""
    if en is None or en.get("incomplete") or (force and lang == "en"):
        check()
        only = None
        if en and en.get("incomplete") and not force:
            store.apply_en(doc, en)
            only = {c["id"] for c in doc["chunks"] if c["id"] not in en["chunks"] or
                    any(u not in en["units"] for u in c["units"]) or c["id"] in en.get("scope_partial", [])}
        ladder.build(doc, task(cfg, "ladder"), cache, jobs=jobs, log=log, progress=lambda a, b: progress("ladder", a, b), force=force, stop=stop, only=only)
        if only is not None:
            for uid, z in en["units"].items():
                if uid in doc["units"] and doc["units"][uid]["chunk"] not in only:
                    doc["units"][uid]["lad"] = z
        check()
        progress("links", 0, 1)
        links.build(doc, task(cfg, "links"), cache, log=log, force=force)
        store.save_en(doc, model)
        en = store.read(pid, "en")
    else:
        store.apply_en(doc, en)
    if lang != "en":
        tr = store.read(pid, f"tr-{lang}")
        if force or tr is None or tr.get("incomplete") or tr.get("base") != en["version"]:
            check()
            only = None
            if tr and tr.get("incomplete") and not force:
                store.apply_tr(doc, lang, tr)
                only = {c["id"] for c in doc["chunks"] if c["id"] not in tr["chunks"] or
                        any(u not in tr["units"] for u in c["units"]) or c["id"] in tr.get("scope_partial", [])}
            translate.build(doc, lang, task(cfg, "translate"), cache, jobs=jobs, log=log, progress=lambda a, b: progress("translate", a, b), force=force, stop=stop, only=only)
            if only is not None:
                for uid, z in tr["units"].items():
                    if uid in doc["units"] and doc["units"][uid]["chunk"] not in only:
                        doc["units"][uid].setdefault("tr", {})[lang] = z
            store.save_tr(doc, lang, en["version"], model)
    progress("done", 1, 1)
    return pid


def generate_scope(pid, lang, cfg, jobs, progress, log, stop, force=False):
    """Generate checked units and selected-range aggregates, retaining other healthy layers."""
    doc = scopes.generation(store.parsed(pid))
    cache = store.pdir(pid) / "llm-cache"
    eligible = {c["id"]: c for c in doc["chunks"] if c["units"] or any(
        b.get("chunk") == c["id"] and b.get("k") == "eq" for b in doc["blocks"])}
    doc["chunks"] = list(eligible.values())
    blocks = {c: [b.get("id") or b.get("html") for b in doc["blocks"] if b.get("chunk") == c and b.get("html")]
              for c in eligible}
    if not eligible:
        return
    def build_layer(name, previous, only):
        if name == "en":
            ladder.build(doc, task(cfg, "ladder"), cache, jobs=jobs, log=log,
                         progress=lambda a,b: progress("ladder",a,b), stop=stop, only=only, force=force)
            units = {u: v["lad"] for u,v in doc["units"].items() if v["chunk"] in only and "lad" in v}
            chunks = {c["id"]: c.get("lad") for c in doc["chunks"] if c["id"] in only}
        else:
            translate.build(doc, lang, task(cfg, "translate"), cache, jobs=jobs, log=log,
                            progress=lambda a,b: progress("translate",a,b), stop=stop, only=only, force=force)
            units = {u: v["tr"][lang] for u,v in doc["units"].items() if v["chunk"] in only and lang in v.get("tr",{})}
            chunks = {c["id"]: c["tr"][lang] for c in doc["chunks"] if c["id"] in only and lang in c.get("tr",{})}
        for cid, value in chunks.items():
            lad = value if name == "en" else (value or {}).get("lad")
            if lad:
                lad["scope_partial"] = eligible[cid]["scope_partial"]
        value = {**(previous or {}), "version": store.stamp(), "model": llm.label(cfg), "incomplete": True,
                 "units": {**(previous or {}).get("units",{}), **units},
                 "chunks": {**(previous or {}).get("chunks",{}), **chunks},
                 "scope_units": {**(previous or {}).get("scope_units",{}),
                                 **{c: eligible[c]["units"] for c in only}},
                 "scope_blocks": {**(previous or {}).get("scope_blocks",{}), **{c: blocks[c] for c in only}},
                 "scope_partial": sorted((set((previous or {}).get("scope_partial",[])) - only) |
                                         {c for c in only if eligible[c]["scope_partial"]})}
        if name == "en":
            value["edges"] = (previous or {}).get("edges", [])
        else:
            value["base"] = store.read(pid,"en")["version"]
            value["title"] = doc["meta"].get("titles",{}).get(lang) or (previous or {}).get("title")
        store.write(pid, name, value)
        return value
    en = store.read(pid,"en")
    if en:
        store.apply_en(doc,en)
    only = {c for c,v in eligible.items() if force or not en or
            c not in en.get("chunks",{}) or en.get("scope_units",{}).get(c) != v["units"] or en.get("scope_blocks",{}).get(c) != blocks[c] or
            any(u not in en["units"] for u in v["units"])}
    if only:
        en = build_layer("en", en, only)
    if lang != "en":
        tr = store.read(pid,"tr-"+lang)
        if tr:
            store.apply_tr(doc,lang,tr)
        only = {c for c,v in eligible.items() if force or not tr or
                c not in tr.get("chunks",{}) or tr.get("scope_units",{}).get(c) != v["units"] or tr.get("scope_blocks",{}).get(c) != blocks[c] or
                any(u not in tr["units"] for u in v["units"])}
        if only:
            build_layer("tr-"+lang,tr,only)
