"""Browser regression: python -m tests.browser_paragraph_equations (Playwright and Chrome)."""
import re
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

from textfold import build, ladder
from textfold.parse import parse


def fixture():
    def eq(eid):
        return (f'<table class="ltx_equation" id="{eid}"><tr><td>'
                f'<math display="block" alttext="x=y"><mi>x</mi><mo>=</mo><mi>y</mi></math>'
                '</td></tr></table>')
    doc = parse('<article class="ltx_document"><section class="ltx_section" id="s1">'
                '<h2 class="ltx_title">First section</h2>'
                '<p class="ltx_p" id="intro">The governing relation follows:</p>'
                + eq('eq1') + eq('eq2') +
                '<p class="ltx_p" id="next">A separate original passage with another relation:</p>'
                + eq('eq3') +
                '<figure id="fig1"><div>Original figure</div><figcaption>Original figure caption.</figcaption></figure>'
                + eq('after-figure') +
                '</section><section class="ltx_section" id="s2">'
                '<h2 class="ltx_title">Next section</h2>' + eq('after-heading') +
                '<p class="ltx_p" id="selected">An essential relation:</p>' + eq('essential') +
                '</section></article>', {'id': 'md-equation-expansion', 'title': 'Equation expansion',
                                        'html_url': '', 'authors': []})
    for u in doc['units'].values():
        u['lad'] = ladder.local(u, doc['atoms'])
    for c in doc['chunks']:
        c['lad'] = {'take': [{'t': 'Section'}], 'topic': [0], 'equations': []}
    doc['chunks'][-1]['lad']['equations'] = [
        {'id': 'essential', 'key': True, 'takeaway': True, 'meaning': 'Essential relation.', 'conditions': ''}]
    return doc


def settled(page):
    expect(page.locator('html')).not_to_have_class(re.compile(r'\bmorphing\b'))


def level(page, n):
    page.locator(f'#zoombar button[data-l="{n}"]').click()
    expect(page.locator('#doc')).to_have_attribute('data-level', str(n))
    settled(page)


def run(page):
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    formulas = page.locator('#doc .eq-body').evaluate_all('(els) => els.map(e => e.innerHTML)')
    level(page, 2)
    for eid in ('eq1', 'eq2', 'eq3', 'after-figure', 'after-heading'):
        expect(page.locator(f'#doc .eq[data-eq="{eid}"]')).not_to_be_visible()
    page.locator('#intro .tx').click()
    settled(page)
    for eid in ('eq1', 'eq2'):
        expect(page.locator(f'#doc .eq[data-eq="{eid}"]')).to_be_visible()
        expect(page.locator(f'#doc .eq[data-eq="{eid}"]')).to_have_attribute('data-l', '4')
    expect(page.locator('#next')).to_have_attribute('data-l', '2')
    expect(page.locator('#doc .eq[data-eq="eq3"]')).not_to_be_visible()
    # Source mathematics and prose share the existing local-open card.
    expect(page.locator('#doc .passage.local-open:has(#intro) .eq-body')).to_have_count(2)
    page.locator('#doc .eq[data-eq="eq1"] .eq-body').click()
    settled(page)
    expect(page.locator('#doc .eq[data-eq="eq1"]')).not_to_be_visible()
    page.locator('#next .tx').click()
    settled(page)
    expect(page.locator('#doc .eq[data-eq="eq3"]')).to_be_visible()
    page.keyboard.press('Escape')
    settled(page)
    expect(page.locator('#doc .eq[data-eq="eq3"]')).not_to_be_visible()
    page.locator('#intro .tx').click()
    settled(page)
    level(page, 1)
    expect(page.locator('#doc .passage.local-open')).to_have_count(0)
    expect(page.locator('#doc .eq[data-eq="eq1"]')).not_to_be_visible()
    page.locator('#intro .tx').click()
    settled(page)
    expect(page.locator('#doc .eq[data-eq="eq1"]')).to_be_visible()
    page.locator('#intro .tx').click()
    settled(page)
    expect(page.locator('#doc .eq[data-eq="eq1"]')).not_to_be_visible()
    expect(page.locator('#doc .eq[data-eq="essential"]')).to_be_visible()
    page.locator('#selected .tx').click()
    settled(page)
    expect(page.locator('#doc .eq[data-eq="essential"] .eq-caption')).not_to_be_visible()
    expect(page.locator('#doc .eq[data-eq="essential"] .eq-body')).to_have_count(1)
    level(page, 3)
    for eid in ('eq1', 'eq2', 'eq3', 'after-figure', 'after-heading'):
        expect(page.locator(f'#doc .eq[data-eq="{eid}"]')).to_be_visible()
    level(page, 2)
    page.locator('#fig1 figcaption .tx').click()
    settled(page)
    expect(page.locator('#fig1')).to_have_attribute('data-l', '4')
    expect(page.locator('#doc .eq[data-eq="after-figure"]')).not_to_be_visible()
    level(page, 4)
    assert formulas == page.locator('#doc .eq-body').evaluate_all('(els) => els.map(e => e.innerHTML)'), 'Original formula HTML changed'
    assert not errors, errors
    page.set_viewport_size({'width': 390, 'height': 844})
    level(page, 2)
    page.locator('#intro .tx').click()
    settled(page)
    expect(page.locator('#doc .eq[data-eq="eq1"]')).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Page overflow'


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        path = Path(tmp) / 'reader.html'
        path.write_text(build.page(fixture()), encoding='utf-8')
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1200, 'height': 900})
        page.goto(path.as_uri())
        run(page)
        browser.close()
    print('PASS: original equations, collapse/reset, selection, boundaries, figure caption, narrow viewport')
