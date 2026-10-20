"""Reader pages. The same reader in two modes:
  app     served by the local server, with the sidebar, the language menu that can generate, settings
  static  one self-contained file (python -m textfold export): CSS, JS, data and images all inside

A page asks no other server for anything. Its fonts (Inter, Source Serif 4) and KaTeX are kept in textfold/web/vendor: the app
serves them, a gallery keeps them beside its pages (assets), and a single file carries them inside.
"""
import base64
import io
import json
import re
import urllib.parse
from html import escape
from pathlib import Path

from PIL import Image

from . import store
from .fetch import fetch_images

WEB = Path(__file__).resolve().parent / "web"   # the reader's pages, styles, scripts and vendor files
VENDOR = WEB / "vendor"
APP_ASSETS = "/static/vendor/"


def _data(f, kind):
    return f"url(data:{kind};base64,{base64.b64encode(f.read_bytes()).decode()})"


def fonts_head(base=None):
    """The fonts, from base (the app's /static/vendor/, a gallery's assets/) or, with none, inside the page: there the
    Latin faces only, the rest falling back to the system's."""
    if base:
        return f'<link rel="stylesheet" href="{base}fonts/fonts.css">'
    css = (VENDOR / "fonts" / "fonts.css").read_text(encoding="utf-8")
    faces = [m.group(0) for m in re.finditer(r"/\* latin \*/\n@font-face \{.*?\}", css, re.S)]
    return "<style>" + "\n".join(re.sub(r"url\(([\w.-]+\.woff2)\)", lambda u: _data(VENDOR / "fonts" / u.group(1), "font/woff2"), f)
                                 for f in faces) + "</style>"


def _katex_inside():
    css = re.sub(r"url\((fonts/[\w-]+\.woff2)\)", lambda u: _data(VENDOR / "katex" / u.group(1), "font/woff2"),
                 (VENDOR / "katex" / "katex.min.css").read_text(encoding="utf-8"))
    return f'<style id="katex-css">{css}</style><script>{(VENDOR / "katex" / "katex.min.js").read_text(encoding="utf-8")}</script>'


def _has_tex(doc):
    """Math the model wrote that matches no formula of the paper ({"x": latex}): only that needs KaTeX."""
    return ('"x":' in json.dumps([doc["units"], doc["chunks"]]) or
            any("$" in row.get(k, "") for c in doc["chunks"] for lad in
                [c.get("lad")] + [z.get("lad") for z in c.get("tr", {}).values()] if lad
                for row in lad.get("equations", []) for k in ("meaning", "conditions")))


ANIMATED_INSIDE = 2_000_000   # a moving picture larger than this goes into a single-file page as its first frame


def data_uri(f, max_side=1600):
    if f.suffix.lower() == ".svg":  # vector stays vector: crisp at every zoom, and small for line plots
        svg = f.read_text(encoding="utf-8", errors="replace")
        # "&" escaped too: in the page's src="…" an entity of the SVG's own (&quot;) would be decoded first and break it
        return "data:image/svg+xml;charset=utf-8," + urllib.parse.quote(svg, safe=" /:=;,'()-._~!*+@?$")
    im = Image.open(f)
    if getattr(im, "is_animated", False) and f.stat().st_size <= ANIMATED_INSIDE:   # a small demo that moves, as it is
        return f"data:image/{(im.format or 'gif').lower()};base64," + base64.b64encode(f.read_bytes()).decode()
    im.thumbnail((max_side, max_side))
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=80, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def inline_images(doc, app=False):
    """Figures go inside the page: one file that still works when forwarded, previewed, or opened on a phone. In the app
    a picture other than a drawing is the server's to give (/p/<id>/img/<name>): a page carrying a README's GIFs inside
    weighed ten megabytes, and the zoom copies its figures; that way they move as they should, and the page stays light."""
    meta = doc["meta"]
    cache = store.pdir(meta["id"]) / "img"
    local = fetch_images(doc["images"], meta["html_url"], cache)
    pid = urllib.parse.quote(meta["id"])
    uris = {src: (f"/p/{pid}/{path}" if app and not path.lower().endswith(".svg") else data_uri(cache / path.split("/", 1)[1]))
            for src, path in local.items()}
    for b in doc["blocks"]:
        if "html" in b:
            for src, uri in uris.items():
                b["html"] = b["html"].replace(f'src="{src}"', f'src="{uri}"')


def payload(doc, app, katex=None, saved=None, pdf=None):
    from . import equations
    doc = equations.reader_captions(doc)
    data = {k: doc[k] for k in ("meta", "atoms", "units", "chunks", "blocks", "bib", "edges", "alias")}
    data["app"] = app
    data["katex"] = katex   # where the reader finds KaTeX: a folder, "inside" the page, or nowhere (math stays as written)
    if pdf:   # a gallery's page: its PDF and PDF.js beside it ({"file", "pdfjs"}, relative to the page)
        data["pdfAt"] = pdf
    if saved:   # saved from the reader: its notes (kept apart from any other page's in the viewer's browser), its language
        data.update(saved)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def page(doc, app=False, assets=None, saved=None, pdf=None):
    """assets: for a static page published beside a folder holding web/vendor's fonts/ and katex/ (a gallery). saved:
    a page the reader saved for themself ({"notes", "saved", "lang"}: the notes chosen, an id of the file, its language).
    pdf: the paper's PDF beside a gallery's page, for the original pages next to the text ({"file", "pdfjs"})."""
    inline_images(doc, app)
    t = (WEB / "template.html").read_text(encoding='utf-8')
    correction = doc["meta"].get("correction")
    if correction and app:
        status = correction["status"]
        issues = correction.get("issues") or []
        title = ("PDF 校对完成 · 有待核实位置" if issues else "PDF 校对完成") if status == "done" else (
            "PDF 校对未完成 · 当前为提取稿" if status in ("error", "stopped") else
            "请选择 PDF 核查范围 · 当前为提取稿" if status == "awaiting-scope" else
            "所选范围校对完成 · 全文尚未完成" if status == "scope-done" else "PDF 校对中 · 当前为提取稿")
        detail = "".join("<li>" + escape(x["text"]) + "</li>" for x in issues)
        if correction.get("error"):
            detail += "<li>" + escape(correction["error"]) + "</li>"
        checked = correction.get("checked", list(range(1, correction.get("total", 0) + 1)) if status == "done" else [])
        selected_scope = correction.get("requested_scope") or correction.get("scope") or ({"pages":checked} if status == "done" else {})
        selected = selected_scope.get("pages", [])
        chapter = selected_scope.get("chapter_pages", [])
        coverage = (f'已检查物理页：{escape(", ".join(map(str, checked)) or "无")}。'
                    f'当前选择：{escape(", ".join(map(str, selected)) or "无")}。')
        if chapter and not set(chapter) <= set(checked):
            coverage += ' 所选章节尚未完整核查；本次仅处理最多 30 页。'
        controls = ''
        if app:
            chapters = ''.join(f'<option value="{escape(c["id"], quote=True)}">{escape(c["title"] or c["id"])}</option>'
                               for c in doc["chunks"] if c["id"] in correction.get("chapters", {}))
            controls = ('<form id="pdf-scope"><p>选择物理页码（含封面、参考文献及附录）。滚动不会启动核查。</p>'
                        '<label>范围 <input name="ranges" placeholder="1-5, 9-12" aria-label="物理页范围" style="width:150px"></label> '
                        '<button type="submit">核查所选页</button>'
                        + (f'<p><label>章节 <select name="chapter" aria-label="核查章节">{chapters}</select></label> '
                           '<label>起始物理页 <input name="position" type="number" min="1" style="width:60px"></label> '
                           '<button type="button" data-scope="chapter">从此处核查最多 30 页</button></p>' if chapters else
                           '<p>无法可靠确定章节页界时，请选择页码范围。</p>') +
                        '<p><button type="button" data-scope="resume">' +
                        ('继续局部核实' if correction.get('method') == 'targeted' and status != 'awaiting-scope' else '继续已选范围') + '</button></p>'
                        '<p role="status" id="pdf-scope-message"></p></form>')
        if correction.get("method") == "targeted":
            title = "局部核实完成 · 未逐页核查全文" if status == "done" else "局部核实未完成 · Full 可立即阅读"
            coverage = f'已调查疑点 {correction.get("done", 0)} 个。局部核实不代表全文逐页检查。'
        generation_note = ("本轮局部核实结束后生成阅读层；未决位置保留不确定性。" if correction.get("method") == "targeted" else
                           "局部摘要仅覆盖已核查内容；范围外依赖来自未核查提取稿。未能定位完整页界的段落须等待其全部页核查。")
        banner = (f'<div class="document-actions"><button type="button" id="document-menu-button" class="langbtn" '
                  f'aria-label="文档菜单" aria-expanded="false" aria-controls="document-menu">⋯</button>'
                  f'<div id="document-menu" hidden style="position:fixed;top:64px;right:16px;z-index:50;'
                  f'box-sizing:border-box;width:min(360px,calc(100% - 32px));max-height:40vh;overflow:auto;padding:8px 12px;border:1px solid #bdb4e6;'
                  f'border-radius:8px;background:var(--surface);color:var(--ink);font:13px/1.5 system-ui">'
                  f'<button type="button" data-scope="document">核查全文</button> '
                  f'<button type="button" id="pdf-scope-toggle" aria-expanded="false">选择核查范围…</button>'
                  f'<details><summary>查看校正记录</summary><p>{escape(title)}</p><p>'
                  f'{coverage} 对照原始 PDF 校正；疑点不自动补写。</p>'
                  f'<p>{generation_note}</p>'
                  f'<ul>{detail}</ul></details><div id="pdf-scope-controls" hidden>{controls}</div></div></div>')
        t = t.replace('<div class="langpick">', banner + '<div class="langpick">')
    if app:
        head = '<script src="/static/theme.js"></script>' + fonts_head(APP_ASSETS) + '<link rel="stylesheet" href="/static/reader.css"><link rel="stylesheet" href="/static/app.css">'
        scripts = ('<script src="/static/i18n.js"></script><script src="/static/tutorial.js"></script><script src="/static/reader.js"></script>'
                   '<script src="/static/app.js"></script>')
        side, cls, katex = '<aside id="sidebar" class="collapsed"></aside>', "app", APP_ASSETS + "katex/"
    else:
        head = f"<script>{(WEB / 'theme.js').read_text(encoding='utf-8')}</script>" + fonts_head(assets) + f"<style>{(WEB / 'reader.css').read_text(encoding='utf-8')}</style>"
        scripts = f"<script>{(WEB / 'i18n.js').read_text(encoding='utf-8')}</script><script>{(WEB / 'reader.js').read_text(encoding='utf-8')}</script>"
        side, cls, katex = "", "static", (assets + "katex/") if assets else None
        if not assets and (_has_tex(doc) or (saved and saved.get("notes"))):   # (an answer's formulas need it too)
            head += _katex_inside()
            katex = "inside"
    return (t.replace("{{TITLE}}", escape(doc["meta"]["title"])).replace("{{HEAD}}", head).replace("{{CLASS}}", cls)
             .replace("{{SIDEBAR}}", side).replace("{{SCRIPTS}}", scripts).replace("{{DATA}}", payload(doc, app, katex, saved, pdf)))


def export(pid):
    doc = store.assemble(pid)
    out = store.DATA / "out" / pid
    out.mkdir(parents=True, exist_ok=True)
    f = out / "index.html"
    f.write_text(page(doc, app=False), encoding="utf-8")
    return f
