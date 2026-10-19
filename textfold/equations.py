"""Display equation identity and progressive selection, separate from paragraph token ids."""
from bs4 import BeautifulSoup
import re

SELECTION = {"type": "array", "items": {"type": "object", "properties": {
    "id": {"type": "string"}, "key": {"type": "boolean"}, "takeaway": {"type": "boolean"},
    "meaning": {"type": "string"}, "conditions": {"type": "string"}},
    "required": ["id", "key", "takeaway", "meaning", "conditions"]}}


def inventory(doc, chunk):
    out = []
    for b in doc["blocks"]:
        if b["k"] != "eq" or b.get("chunk") != chunk["id"]:
            continue
        soup = BeautifulSoup(b["html"], "lxml")
        latex = [m.get("alttext", "") for m in soup.find_all("math")]
        tag = soup.select_one(".ltx_tag_equation")
        printed = re.search(r"\\tag\*?\s*\{([^{}]+)\}", " ".join(latex))
        out.append({"id": b["id"], "number": tag.get_text(" ", strip=True) if tag else
                    ("(" + printed[1] + ")" if printed else ""),
                    "latex": latex or [soup.get_text(" ", strip=True)]})
    return out


def prompt(doc, chunk):
    import json
    eqs = inventory(doc, chunk)
    if not eqs:
        return ""
    return ("\n\nOriginal display equations in reading order (stable source ids):\n" +
            json.dumps(eqs, ensure_ascii=False) + "\nSelect these WITHIN the same progressive compression of the "
            "author's argument. Return section.equations with one decision per source id: key and takeaway booleans, "
            "a short meaning statement and all necessary validity conditions from the paper. Key retains necessary "
            "definitions, governing mechanisms and central results; Takeaway separately selects the subset essential "
            "to the paper's main message. Familiar definitions and intermediate derivation steps do not qualify just "
            "because they are equations. No numeric quota. A selected long equation is displayed directly at both "
            "levels: do not omit it because of length. Never rewrite its mathematics; use the id. Keep necessary "
            "conditions even when they need more words than a headline. Copy essential mathematical conditions "
            "exactly as $...$, rather than spelling out powers or weakening inequalities. Meaning/conditions are English; empty "
            "conditions only if none are needed. Refer to the author's equation numbers in explanations, never "
            "internal source ids. Integrate the concepts and findings of essential equations into the section's "
            "takeaway and topic, rather than treating equation selection as a separate summary. Topic remains a "
            "short concept map, without displaying the formulas themselves.\n")


def selected(doc, chunk, rows):
    available = {e["id"]: e for e in inventory(doc, chunk)}
    def explanation(text):
        for eid, eq in available.items():
            if eq["number"]:
                text = re.sub(r"(?<!\w)" + re.escape(eid) + r"(?!\w)", "equation " + eq["number"], text)
        return text.strip()
    out = []
    for row in rows or []:
        if row.get("id") not in available or any(r["id"] == row["id"] for r in out):
            continue
        if row.get("key") or row.get("takeaway"):
            if not row.get("meaning", "").strip():
                raise ValueError("A selected equation needs its meaning statement")
            out.append({"id": row["id"], "key": True, "takeaway": bool(row.get("takeaway")),
                        "meaning": explanation(row["meaning"]), "conditions": explanation(row.get("conditions", ""))})
    return out


def reader_captions(doc):
    """Build view-only equation captions with the ordinary aligned text ladder."""
    from copy import deepcopy
    from . import ladder
    doc = deepcopy(doc)
    chunks = {c['id']: c for c in doc['chunks']}
    for i, block in enumerate(doc['blocks']):
        if block['k'] != 'eq' or block.get('chunk') not in chunks:
            continue
        chunk = chunks[block['chunk']]
        row = next((r for r in (chunk.get('lad') or {}).get('equations', []) if r['id'] == block['id']), None)
        if not row:
            continue
        context = []
        for direction in (-1, 1):
            for j in range(i + direction, -1 if direction < 0 else len(doc['blocks']), direction):
                near = doc['blocks'][j]
                if near.get('chunk') != block.get('chunk') or near['k'] in ('h', 'fig'):
                    break
                if near['k'] == 'u':
                    context.append(doc['units'][near['u']])
                    break
                if near['k'] != 'eq':
                    break
        if not context:
            continue
        uid = block['id'] + '.cap'
        unit = {'id': uid, 'role': 'caption', 'of': block['id'], 'toks': [], 'sents': []}
        for source in context:
            offset = len(unit['toks'])
            if offset:
                unit['toks'][-1]['s'] = 1
            unit['toks'] += deepcopy(source['toks'])
            unit['sents'] += [[a + offset, b + offset] for a, b in source['sents']]
        summary = ' '.join(filter(None, (row['meaning'], row.get('conditions', '')))).rstrip('.。')
        unit['lad'] = ladder.assemble(unit, {'takeaway': summary, 'evidence': list(range(len(unit['sents']))),
                                          'role': 'analysis'}, doc['atoms'], 'equation')
        for lang, translated in chunk.get('tr', {}).items():
            translated_row = next((r for r in (translated.get('lad') or {}).get('equations', [])
                                   if r['id'] == block['id']), None)
            sources = [source.get('tr', {}).get(lang) for source in context]
            if not translated_row or not all(sources):
                continue
            z = {'toks': [], 'sents': []}
            for source in sources:
                offset = len(z['toks'])
                if offset:
                    z['toks'][-1]['s'] = 1
                z['toks'] += deepcopy(source['toks'])
                z['sents'] += [[a + offset, b + offset] for a, b in source['sents']]
            text = ' '.join(filter(None, (translated_row['meaning'], translated_row.get('conditions', '')))).rstrip('.。')
            z['lad'] = ladder.assemble(z, {'takeaway': text, 'evidence': list(range(len(z['sents']))),
                                         'role': 'analysis'}, doc['atoms'], 'equation')
            unit.setdefault('tr', {})[lang] = z
        doc['units'][uid] = unit
        chunk['units'].append(uid)
        block['cap'] = uid
    return doc
