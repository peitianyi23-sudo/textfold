// Personal documentation chapter navigation and reading-position restoration.
(() => {
  'use strict';
  if (!document.getElementById('documentation-chapter')) return;
  const data = document.getElementById('paper-data');
  const D = data ? JSON.parse(data.textContent) : null;
  const api = async (path, body) => {
    const r = await fetch(path, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const value = await r.json();
    if (!r.ok) throw new Error(value.error || r.statusText);
    return value;
  };
  const piece = t => t.t ?? (D.atoms[t.a]?.kind === 'math' ? `$${D.atoms[t.a].alt || ''}$` : D.atoms[t.a]?.text || '');
  const text = tokens => (tokens || []).map((t, i) => piece(t) + (t.s && i + 1 < tokens.length ? ' ' : '')).join('').trim();
  const source = uid => D.meta.chapter_sources?.[D.units[uid]?.chunk] || D.meta.abs_url;
  const current = () => {
    if (!D) return null;
    const selection = getSelection();
    const selected = selection?.anchorNode?.parentElement?.closest('[data-u]');
    const equation = selection?.anchorNode?.parentElement?.closest('[data-eq]');
    if (equation) {
      const index = D.blocks.findIndex(b => b.k === 'eq' && b.id === equation.dataset.eq);
      const before = D.blocks.slice(0, index).reverse().find(b => b.k === 'u' && b.chunk === equation.dataset.chunk);
      return before?.u || D.chunks.find(c => c.id === equation.dataset.chunk)?.units[0] || null;
    }
    const el = selected || [...document.querySelectorAll('#doc [data-u]')].find(e => e.getBoundingClientRect().bottom > 80);
    return el?.dataset.u || null;
  };
  if (!D?.meta.documentation_chapters) return;
  function keep() {
    if (!D) return;
    const uid = current(), el = document.querySelector(`[data-u="${CSS.escape(uid || '')}"]`);
    sessionStorage.setItem('pf-keep', JSON.stringify({ pid: D.meta.id, uid, level: window.__reader?.level, top: el?.getBoundingClientRect().top || 80 }));
    sessionStorage.setItem(`tf-reading-${D.meta.id}`, JSON.stringify({ uid, text: uid ? text(D.units[uid].toks) : '', source: uid ? source(uid) : '', level: window.__reader?.level, chapter: D.meta.active_chapter }));
  }
  function refresh() { keep(); setTimeout(() => location.reload(), 100); }
  function open(paper, chapter = '', target = '', note = '', level) {
    keep();
    const saved = JSON.parse(sessionStorage.getItem(`tf-reading-${paper}`) || 'null');
    const page = chapter || saved?.chapter;
    const query = page ? `?chapter=${encodeURIComponent(page)}` : '';
    level = level ?? (D?.meta.id === paper ? window.__reader?.level : saved?.level) ?? 4;
    const hash = page || target ? `#level=${encodeURIComponent(window.DR_I18N.t('en').levels[level])}${target ? `&target=${encodeURIComponent(target)}` : ''}${note ? `&n=${encodeURIComponent(note)}` : ''}` : '';
    const url = `/p/${encodeURIComponent(paper)}${query}${hash}`;
    setTimeout(() => location.assign(url), 100);
    return { paper, opening: true, url };
  }
  function followDocumentation(job, navigate = true) {
    const tick = setInterval(async () => {
      try {
        const current = (await api('/api/jobs')).find(j => j.id === job.id);
        if (!current || ['done', 'error', 'stopped'].includes(current.status)) {
          clearInterval(tick);
          if (current?.readable && navigate) open(current.pid);
        }
      } catch { clearInterval(tick); }
    }, 1000);
    return job;
  }
  if (D) {
    document.addEventListener('textfold-note-navigate', e => {
      const n = e.detail, a = n.anchor;
      if (a.unresolved || (a.unit && D.units[a.unit]) || (!a.unit && document.getElementById(a.section))) return;
      const page = D.meta.document_unit_chapters?.[a.unit] || D.meta.documentation_chapters?.find(c => c.url === a.source_url || c.url === D.meta.chapter_sources?.[a.section])?.id;
      if (page) { e.preventDefault(); open(D.meta.id, page, a.unit || a.section, n.id); }
    });
    const chooser = document.getElementById('documentation-chapter');
    if (chooser) chooser.onchange = () => open(D.meta.id, chooser.value);
    document.addEventListener('click', e => {
      const link = e.target.closest('a[href]');
      if (!link || !D.meta.documentation_chapters) return;
      const href = link.getAttribute('href');
      if (href.startsWith('?chapter=')) {
        e.preventDefault(); e.stopImmediatePropagation();
        open(D.meta.id, new URLSearchParams(href.slice(1)).get('chapter'));
        return;
      }
      const destination = href.startsWith('#') ? href.slice(1) : '';
      if (destination && !document.getElementById(destination)) {
        const page = D.meta.document_unit_chapters?.[destination] || D.meta.documentation_chapters.find(c => c.url === D.meta.chapter_sources?.[destination])?.id;
        if (page) { e.preventDefault(); e.stopImmediatePropagation(); open(D.meta.id, page, destination); }
      }
    }, true);
    const retry = document.getElementById('documentation-retry');
    if (retry) retry.onclick = async () => {
      retry.disabled = true;
      try { const result = await api('/api/documentation', { paper: D.meta.id, mode: 'retry' }); followDocumentation(result); retry.textContent = `Retry queued · ${result.id}`; }
      catch (e) { retry.textContent = e.message; retry.disabled = false; }
    };
    addEventListener('pagehide', keep);
    const saved = JSON.parse(sessionStorage.getItem(`tf-reading-${D.meta.id}`) || 'null');
    const target = new URLSearchParams(location.hash.slice(1)).get('target');
    if (target) document.getElementById(target)?.scrollIntoView({ block: 'center' });
    else if (saved && (!saved.chapter || saved.chapter === D.meta.active_chapter)) {
      const ids = Object.keys(D.units).filter(u => text(D.units[u].toks) === saved.text && source(u) === saved.source);
      if (ids.length === 1) {
        window.TFDocumentationPosition = { matched: true, unit: ids[0] };
        window.__reader.setLevel(saved.level);
        document.querySelector(`[data-u="${CSS.escape(ids[0])}"]`)?.scrollIntoView({ block: 'center' });
      } else if (D.meta.chapter_sources) {
        const uid = Object.keys(D.units).find(u => source(u) === saved.source);
        window.TFDocumentationPosition = { matched: false, source_url: saved.source, original_text: saved.text, fallback_unit: uid || null };
        document.querySelector(`[data-u="${CSS.escape(uid || '')}"]`)?.scrollIntoView({ block: 'center' });
      }
    }
  }
})();
