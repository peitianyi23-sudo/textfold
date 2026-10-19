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
