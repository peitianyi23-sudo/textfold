import json
import unittest
from textfold import correction, equations, ladder, semantic, store, translate
from textfold.parse import parse
from unittest.mock import patch


class EssentialEquationTests(unittest.TestCase):
    def doc(self):
        return parse(correction.render('# Result\n\nA result subject to $x>0$.\n\n$$x=y+z \\tag{7}$$\n\nAn intermediate step.\n\n$$y=z \\tag{8}$$', {}),
                     {'id': 'pdf-0123456789abcdef', 'title': 'Test'})

    def test_separate_levels_use_original_identity_without_rewriting_math(self):
        doc = self.doc(); c = doc['chunks'][0]
        inv = equations.inventory(doc, c)
        rows = [{'id': inv[0]['id'], 'key': True, 'takeaway': True, 'meaning': 'Main result.', 'conditions': 'Only for x>0.'},
                {'id': inv[1]['id'], 'key': True, 'takeaway': False, 'meaning': 'Necessary definition.', 'conditions': ''}]
        sec = ladder.section_ladder({'takeaway': 'Main result', 'topic': 'result', 'equations': rows}, doc=doc, chunk=c)
        self.assertEqual(sec['equations'], rows)
        self.assertIn('x>0', sec['equations'][0]['conditions'])
        self.assertIn('7', inv[0]['number'] or inv[0]['latex'][0])
        self.assertIn('section.equations', ladder.prompt_for(doc, c))
        self.assertNotIn('equations', doc['blocks'][0])

    def test_unknown_ids_are_not_attached_and_takeaway_is_a_subset(self):
        doc = self.doc(); c = doc['chunks'][0]; eid = equations.inventory(doc, c)[0]['id']
        selected = equations.selected(doc, c, [{'id': 'invented', 'key': True},
            {'id': eid, 'key': False, 'takeaway': True, 'meaning': 'Result', 'conditions': ''}])
        self.assertEqual(len(selected), 1)
        self.assertTrue(selected[0]['key'])
        with self.assertRaises(ValueError):
            equations.selected(doc, c, [{'id': eid, 'key': True}])

    def test_selection_survives_layer_storage_and_translation_prompt(self):
        doc = self.doc(); c = doc['chunks'][0]
        for u in doc['units'].values(): u['lad'] = ladder.local(u, doc['atoms'])
        rows = [{'id': equations.inventory(doc, c)[0]['id'], 'key': True, 'takeaway': False,
                 'meaning': 'Main result', 'conditions': 'Only for x>0'}]
        c['lad'] = ladder.section_ladder({'takeaway': 'Main result', 'topic': 'result', 'equations': rows}, doc=doc, chunk=c)
        with patch.object(store, 'write') as write:
            store.save_en(doc, 'test')
        saved = json.loads(json.dumps(write.call_args.args[2]))
        doc['chunks'][0]['lad'] = None
        store.apply_en(doc, saved)
        self.assertEqual(doc['chunks'][0]['lad']['equations'], rows)
        self.assertIn('Only for x>0', translate.prompt_for(doc, c, 'zh'))

    def test_finalized_markdown_page_mapping_and_unreadable_scan_fallback(self):
        a = ('Alpha beta gamma delta epsilon zeta. ' * 10 + '\n\n') * 8
        b = ('Lambda mu omicron sigma tau upsilon. ' * 10 + '\n\n') * 8
        text = a+'\n\n'+b
        ranges = correction.page_ranges(text, [a, b, ''])
        self.assertLess(ranges[0][1], len(text))
        self.assertGreater(ranges[1][0], 0)
        self.assertEqual(ranges[2], (0, len(text)))

    def test_real_long_aligned_equation_keeps_rows_symbols_number_and_original_latex(self):
        latex = r'\begin{aligned}x&=a+b\\&+c+d\end{aligned}\tag{10}'
        m = semantic.tex_math(latex, True)
        self.assertEqual(m['alttext'], latex)
        self.assertEqual(len(m.find_all('mtr')), 2)
        self.assertNotIn('&', m.get_text())
        self.assertIn('(10)', m.get_text())
        self.assertEqual(m.get_text().replace('(10)', ''), 'x=a+b+c+d')


if __name__ == '__main__': unittest.main()
