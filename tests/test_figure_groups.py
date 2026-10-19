"""Complete figures at the shared conversion boundary, before reading levels."""
from tests.test_pdftext import typeset
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from textfold import pdfdoc, markdown, semantic, parse, ladder, zotero_cache, engine, store


def picture(box, captions=(), kind="image"):
    return {"type": kind, "bbox": box, "image_source": "images/panel.jpg",
            "content": "<table><tr><td>plot</td></tr></table>" if kind == "table" else "",
            "captions": [{"content": c, "bbox": box} for c in captions]}


def convert(blocks, crops=None):
    want = []
    _, _, md = pdfdoc.to_markdown({"pages": [{"blocks": blocks}]}, want=want, crops=crops)
    return md, want


class FigureGroupsTest(unittest.TestCase):
    def test_six_mixed_panels_interleaved_with_column_prose(self):
        a = picture([.12,.49,.37,.62], ["Full field", "(a)"])
        prose = {"type":"text", "bbox":[.51,.06,.95,.45], "content":"The other column of narrative remains outside the figure."}
        b = picture([.41,.49,.66,.62], ["(b)"])
        d = picture([.095,.634,.357,.8], ["Fig. 1 | Six panels. The inset shows the"], "chart")
        e = picture([.359,.641,.618,.8], ["(e)"], "chart")
        c = picture([.673,.491,.912,.622], ["(c)"])
        f = picture([.621,.643,.885,.8], ["(f)", "temporal evolution and all remaining statistical diagnostics."], "chart")
        md, want = convert([a,prose,b,d,e,c,f])
        self.assertEqual(md.count("<figure>"),1)
        self.assertEqual(len(want),1)
        self.assertEqual(set(want[0]["blocks"]), {id(x) for x in [a,b,c,d,e,f]})
        self.assertIn("shows the temporal evolution", md)
        self.assertNotIn("(f)</figcaption>", md)
        self.assertIn(prose["content"], md)
        self.assertLess(want[0]["box"][0], .095)
        self.assertGreater(want[0]["box"][2], .912)

    def test_two_figures_on_one_page_keep_their_panels_and_continuations(self):
        a=picture([.22,.05,.50,.27],["Fig. 3 | The black"])
        b=picture([.51,.05,.78,.14])
        c=picture([.51,.15,.78,.275],["solid line). More diagnostics are shown here."])
        d=picture([.23,.358,.505,.506])
        e=picture([.52,.365,.78,.505],["(b)"])
        f=picture([.23,.515,.50,.663],["Fig. 4 | Training of the 3D"])
        g=picture([.52,.524,.78,.662],["(d)","fluctuating component and the reference spectrum."])
        md,want=convert([a,f,b,c,d,e,g])
        self.assertEqual(md.count("<figure>"),2)
        self.assertEqual([len(w["blocks"]) for w in want],[3,4])
        self.assertIn("black solid line)",md)
        self.assertIn("3D fluctuating component",md)
        self.assertLess(want[0]["box"][3],want[1]["box"][1])

    def test_adjacent_independent_figures_are_not_merged(self):
        md,want=convert([picture([.1,.2,.48,.5],["Figure 1. First."]),
                         picture([.52,.2,.9,.5],["Figure 2. Second."])])
        self.assertEqual(md.count("<figure>"),2)
        self.assertEqual(md.count("<figcaption>"),2)

    def test_figure_table_joins_panels_but_real_table_remains(self):
        md,want=convert([picture([.1,.2,.48,.5],["(a)"]),
                         picture([.52,.2,.9,.5],["Figure 2. Two panels."],"table"),
                         {"type":"table","bbox":[.1,.7,.9,.8],"content":"<table><tr><td>42</td></tr></table>",
                          "captions":[{"content":"Table 1. Measurements."}]}])
        self.assertEqual(len(want),1)
        self.assertEqual(len(want[0]["blocks"]),2)
        self.assertIn("<td>42</td>",md)
        self.assertNotIn("<td>plot</td>",md)

    def test_ambiguous_panels_show_original_page_without_caption_model_units(self):
        blocks=[picture([.1,.2,.35,.5],["Figure 1. First."]),
                picture([.38,.2,.62,.5],["(b)","The author's caption continuation stays visible."]),
                picture([.65,.2,.9,.5],["Figure 2. Second."]),
                {"type":"text","content":"The narrative still imports normally."}]
        md,want=convert(blocks)
        self.assertIn("Unconfirmed figure grouping",md)
        self.assertEqual(len(want),1)
        self.assertEqual(want[0]["box"],[0,0,1,1])
        html,_=markdown.to_html(md)
        doc=parse.parse(semantic.normalize(html,resolve_img=lambda x:x),{"id":"test","title":"Test"})
        text=" ".join(ladder.prompt_for(doc,c) for c in doc["chunks"])
        self.assertNotIn("caption continuation",text)
        self.assertIn("caption continuation",md)
        self.assertIn("narrative still imports",text)

    def test_standalone_caption_continuation_and_panel_labels(self):
        md,want=convert([picture([.1,.2,.48,.5]),picture([.52,.2,.9,.5]),
            {"type":"text","content":"Figure 1. The complete", "bbox":[.1,.52,.48,.57]},
            {"type":"text","content":"author caption continues in the second column.","bbox":[.52,.52,.9,.57]},
            {"type":"text","content":"(a)","bbox":[.1,.18,.13,.2]}])
        self.assertEqual(md.count("<figure>"),1)
        self.assertIn("complete author caption continues",md)
        self.assertEqual(md.count("author caption continues"),1)

    def test_uncaptioned_single_illustration_is_preserved(self):
        md,_=convert([picture([.1,.2,.9,.5])])
        self.assertIn("panel.jpg",md)
        self.assertNotIn("Unconfirmed",md)

    def test_padding_includes_labels_but_stops_below_running_header(self):
        md,want=convert([{"type":"header","bbox":[.1,.025,.9,.041],"content":"Article DOI"},
                        picture([.2,.056,.5,.27],["Figure 1. Spectra."]),
                        picture([.51,.056,.8,.27])])
        self.assertGreater(want[0]["box"][1],.041)
        self.assertLess(want[0]["box"][1],.056)

    def test_native_and_cache_store_the_same_unconfirmed_original_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); pdf=root/"paper.pdf";pdf.write_bytes(typeset([(12, "A physical PDF page for the import fixture.")]))
            blocks=[{"type":"text","text":"Results","text_level":1},
                    {"type":"text","text":"The healthy narrative still imports before level generation."},
                    {"type":"image","bbox":[100,200,480,500],"img_path":"a.jpg","image_caption":["(a)"]},
                    {"type":"chart","bbox":[520,200,900,500],"img_path":"b.jpg","chart_caption":["An author description without a unique numbered owner."]}]
            def render(pdf,jobs):
                for page,box,target in jobs:
                    Image.new("RGB",(120,160),"white").save(target)
                return {str(target) for _,_,target in jobs}
            with patch.object(store,"DATA",root/"data"),patch.object(engine,"crop_here",side_effect=render),patch.object(engine,"crop",side_effect=render), \
                 patch.object(engine,"convert",side_effect=AssertionError("must not rerun extraction")):
                pid="pdf-0123456789abcdef"
                zotero_cache.save(pid,(root,blocks),pdf,"Test paper")
                sc=zotero_cache.structured(blocks,root,root,pdf,"Test paper")
                (root/engine.PDF).write_bytes(pdf.read_bytes())
                pdfdoc.store_pdf("pdf-fedcba9876543210",root,sc,"paper.pdf","fast")
                for key in [pid,"pdf-fedcba9876543210"]:
                    d=store.parsed(key)
                    fig=next(b for b in d["blocks"]if b["k"]=="fig")
                    self.assertIsNone(fig["cap"])
                    self.assertIn("Unconfirmed figure grouping",fig["html"])
                    self.assertIn("An author description",fig["html"])
                    self.assertIn("<img",fig["html"])
                    self.assertFalse((store.pdir(key)/"layers").exists())
                    for c in d["chunks"]:
                        self.assertNotIn("An author description",ladder.prompt_for(d,c))

    def test_roman_numbered_real_table_with_pictured_cell_is_still_a_table(self):
        table=picture([.1,.6,.9,.8],["Table I. Measured values."],"table")
        table["content"]='<table><tr><td><img src="formula.png"></td><td>42</td></tr></table>'
        md,_=convert([table])
        self.assertIn("<td>42</td>",md)
        self.assertNotIn("Unconfirmed",md)

    def test_two_captions_inside_one_extracted_block_are_unconfirmed(self):
        md,want=convert([picture([.1,.2,.9,.8],["Figure 1. First.","Figure 2. Second."])])
        self.assertIn("Unconfirmed",md)
        self.assertEqual(want[0]["box"],[0,0,1,1])

    def test_single_native_picture_keeps_external_panel_label_in_crop(self):
        b=picture([.2,.3,.8,.6],["Figure 1. A single illustrated panel."])
        b["captions"].insert(0,{"content":"(a)","bbox":[.18,.27,.22,.29]})
        _,want=convert([b])
        self.assertEqual(len(want),1)
        self.assertLess(want[0]["box"][1],.27)
