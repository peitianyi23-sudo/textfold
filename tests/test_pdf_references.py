"""Reference separation at the PDF conversion boundary, before any model sees the article."""
from tests.test_pdftext import typeset
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from textfold import engine, ladder, markdown, parse, pdfdoc, semantic, store, zotero_cache
from textfold.tokens import plain


META = {"id": "pdf-0123456789abcdef", "title": "Reference separation"}


def document(blocks):
    return {"pages": [{"blocks": blocks}]}


def parsed(blocks):
    _, _, md = pdfdoc.to_markdown(document(blocks))
    html, _ = markdown.to_html(md)
    return parse.parse(semantic.normalize(html, resolve_img=lambda s: s), META.copy())


class ReferenceTest(unittest.TestCase):
    def test_headingless_explicit_references_never_enter_model_input(self):
        doc = parsed([
            {"type": "paragraph_title", "content": "Conclusions"},
            {"type": "text", "content": "The turbulent front propagates more slowly in polymer solutions [1]."},
            {"type": "ref_text", "content": "First author, A cited publication (2009)."},
            {"type": "ref_text", "content": "Second author, Another publication (2011)."},
            {"type": "text", "content": "This untagged narrative remains part of the conclusion."},
            {"type": "image", "image_source": "img/figure.png", "captions": [{"content": "Figure 1. Front velocity."}]},
            {"type": "table", "content": "<table><tr><td>42</td></tr></table>", "captions": [{"content": "Table 1. Values."}]},
            {"type": "table", "image_source": "img/panels.png", "content": "<table><tr><td>panel labels</td></tr></table>",
             "captions": [{"content": "Figure 2. A plot extracted as a table."}]},
        ])
        text = " ".join(plain(u["toks"], doc["atoms"]) for u in doc["units"].values())
        self.assertIn("[1]", text)
        self.assertIn("untagged narrative", text)
        self.assertNotIn("cited publication", text)
        self.assertEqual(doc["bib"].count('class="ltx_bibitem"'), 2)
        figures = [b for b in doc["blocks"] if b["k"] == "fig"]
        self.assertEqual(len(figures), 3)
        self.assertIn('src="img/panels.png"', figures[-1]["html"])
        self.assertNotIn("panel labels", text)
        for chunk in doc["chunks"]:
            prompt = ladder.prompt_for(doc, chunk)
            self.assertNotIn("cited publication", prompt)
            self.assertNotIn("Another publication", prompt)

    def test_headed_references_related_work_and_narrative_lists(self):
        doc = parsed([
            {"type": "paragraph_title", "content": "Related Work"},
            {"type": "text", "content": "Earlier experiments [2] measured turbulent transport."},
            {"type": "list", "content": "1. Measure velocity\n2. Compare results"},
            {"type": "text", "content": "[1] Measure velocity in 2020.\n[2] Compare results in 2021.\n[3] Repeat in 2022."},
            {"type": "paragraph_title", "content": "References"},
            {"type": "text", "content": "A. Author, A publication (2010)."},
            {"type": "paragraph_title", "content": "Appendix"},
            {"type": "text", "content": "These additional measurements remain narrative."},
        ])
        text = " ".join(plain(u["toks"], doc["atoms"]) for u in doc["units"].values())
        self.assertIn("Earlier experiments", text)
        self.assertIn("Repeat in 2022", text)
        self.assertIn("additional measurements", text)
        self.assertIn("A publication", doc["bib"])
        self.assertNotIn("A publication", text)
        self.assertTrue(any(c["title"] == "Related Work" for c in doc["chunks"]))

    def test_merged_numbered_bibliography_in_a_text_block(self):
        refs = ("[1] A. Author, Turbulent transport, J. Fluid Mech. 123, 45 (2020).\n"
                "[2] B. Author, Turbulent Flows (Cambridge University Press, Cambridge, 2006).\n"
                "[3] C. Author, Free-surface turbulence, Ph.D. thesis, University, 2000.")
        doc = parsed([{"type": "paragraph_title", "content": "Acknowledgments"},
                      {"type": "text", "content": "We thank the experimenters for their assistance."},
                      {"type": "text", "content": refs}])
        self.assertEqual(len(doc["units"]), 1)
        self.assertEqual(doc["bib"].count('class="ltx_bibitem"'), 3)

    def test_zotero_and_native_storage_share_reference_separation(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(store, "DATA", Path(tmp) / "data"), \
                patch.object(engine, "convert", side_effect=AssertionError("must not run MinerU")):
            root = Path(tmp)
            pdf = root / "paper.pdf"
            pdf.write_bytes(typeset([(12, "A physical PDF page for the import fixture.")]))
            cached = [{"type": "text", "text": "Conclusions", "text_level": 1},
                      {"type": "text", "text": "The measured turbulent transport agrees with the predicted scaling law."},
                      {"type": "ref_text", "text": "A. Author, A cited publication (2020)."}]
            zotero_cache.save(META["id"], (root, cached), pdf, META["title"])
            self.assertEqual(len(store.parsed(META["id"])["units"]), 1)
            self.assertIn("A cited publication", store.parsed(META["id"])["bib"])
            sc = zotero_cache.structured(cached, root, root, pdf, META["title"])
            pid = "pdf-fedcba9876543210"
            pdfdoc.store_pdf(pid, root, sc, "paper.pdf", "fast")
            self.assertEqual(len(store.parsed(pid)["units"]), 1)
            self.assertIn("A cited publication", store.parsed(pid)["bib"])
