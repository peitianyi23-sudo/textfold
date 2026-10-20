import unittest
from bs4 import BeautifulSoup
from textfold import build, correction, ladder
from textfold.parse import parse

class CompletedBannerTests(unittest.TestCase):
 def test_complete_check_has_no_overlay_even_with_retained_observations(self):
  for status in ['done','stopped','error','awaiting-scope','scope-done']:
   doc=parse(correction.render('# Result\n\nA result.',{}),{'id':'pdf-0123456789abcdef','title':'Result','html_url':'https://example.org/paper','correction':{'status':status,'issues':[{'text':'Retained observation'}]}})
   for u in doc['units'].values():u['lad']=ladder.local(u,doc['atoms'])
   html=build.page(doc,app=True)
   menu=BeautifulSoup(html,'lxml').find(id='document-menu')
   self.assertIsNotNone(menu)
   self.assertTrue(menu.has_attr('hidden'))
   self.assertIn('核查全文',menu.get_text())
   self.assertNotIn('aria-label="PDF 校对"',html)

if __name__=='__main__':unittest.main()

