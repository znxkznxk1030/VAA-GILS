"""Helpers for editing the submitted .docx: replace text that spans runs and mark it.

The manuscript body is maintained in LaTeX, but the journal submission is a Word file
that was built by hand, so revisions are ported into the .docx instead of regenerated.
Every ported revision is highlighted so the reviewers can find it.

usage (from another script):
    import docx_edit as de
    doc = de.load("paper/jkiie_submit_body.docx")
    de.replace(doc, "old sentence", "new sentence", mark=True)
    de.save(doc, "paper/jkiie_submit_body.docx")
"""
from __future__ import annotations

import re
import shutil
import zipfile

HL = '<w:highlight w:val="yellow"/>'
PARA = re.compile(r"<w:p(?: [^>]*)?>.*?</w:p>", re.S)
RUN = re.compile(r"<w:r(?: [^>]*)?>.*?</w:r>", re.S)
TEXT = re.compile(r"(<w:t(?: [^>]*)?>)([^<]*)(</w:t>)")


class Doc:
    def __init__(self, path: str, xml: str, parts: dict):
        self.path, self.xml, self.parts = path, xml, parts


def load(path: str) -> Doc:
    with zipfile.ZipFile(path) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    return Doc(path, parts["word/document.xml"].decode("utf-8"), parts)


def save(doc: Doc, path: str, backup: str | None = None) -> None:
    if backup:
        shutil.copy(doc.path, backup)
    doc.parts["word/document.xml"] = doc.xml.encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in doc.parts.items():
            z.writestr(name, data)


def _mark_run(run: str) -> str:
    """Add a yellow highlight to one run, creating w:rPr when the run has none."""
    if HL in run:
        return run
    m = re.search(r"<w:rPr>(.*?)</w:rPr>", run, re.S)
    if m:
        return run[: m.end(1)] + HL + run[m.end(1):]
    m = re.search(r"(<w:r(?: [^>]*)?>)", run)
    return run[: m.end(1)] + "<w:rPr>" + HL + "</w:rPr>" + run[m.end(1):]


def esc(text: str) -> str:
    """Escape text for a w:t body. Angle brackets are common in this manuscript (<Table 4>)."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def replace(doc: Doc, old: str, new: str, mark: bool = True, count: int = 1) -> int:
    """Replace `old` with `new` even when it spans several runs of one paragraph."""
    old, new = esc(old), esc(new)
    done = 0
    out, pos = [], 0
    for pm in PARA.finditer(doc.xml):
        para = pm.group(0)
        runs = list(RUN.finditer(para))
        texts = []  # (run_index, text_match, start_in_concat)
        concat = ""
        for ri, rm in enumerate(runs):
            for tm in TEXT.finditer(rm.group(0)):
                texts.append((ri, rm, tm, len(concat)))
                concat += tm.group(2)
        idx = concat.find(old)
        if idx < 0:
            continue
        span = [(ri, rm, tm, st) for ri, rm, tm, st in texts
                if st < idx + len(old) and st + len(tm.group(2)) > idx]
        first_ri = span[0][0]
        if any("<m:oMath" in runs[ri].group(0) for ri, *_ in span):
            raise ValueError(f"replacement spans a math object: {old[:40]!r}")
        # rebuild each affected run's text
        new_para, prev = "", 0
        for ri, rm, tm, st in span:
            t = tm.group(2)
            lo, hi = max(0, idx - st), min(len(t), idx + len(old) - st)
            piece = t[:lo] + (new if ri == first_ri else "") + t[hi:]
            run_xml = rm.group(0)
            run_new = run_xml[: tm.start()] + tm.group(1) + piece + tm.group(3) + run_xml[tm.end():]
            if mark and ri == first_ri:
                run_new = _mark_run(run_new)
            new_para += para[prev: rm.start()] + run_new
            prev = rm.end()
        new_para += para[prev:]
        out.append(doc.xml[pos: pm.start()] + new_para)
        pos = pm.end()
        done += 1
        if done >= count:
            break
    if done == 0:
        raise ValueError(f"not found: {old[:60]!r}")
    doc.xml = "".join(out) + doc.xml[pos:]
    return done


def find_para(doc: Doc, anchor: str) -> re.Match:
    """Return the paragraph match that contains `anchor` in its concatenated text."""
    anchor = esc(anchor)
    for pm in PARA.finditer(doc.xml):
        if anchor in "".join(t for _, t, _ in TEXT.findall(pm.group(0))):
            return pm
    raise ValueError(f"paragraph not found: {anchor[:60]!r}")


def para_text(para_xml: str) -> str:
    return "".join(t for _, t, _ in TEXT.findall(para_xml))


def clone_para(doc: Doc, anchor: str, text: str, after: bool = True, mark: bool = True) -> None:
    """Insert a new paragraph that copies the formatting of the paragraph holding `anchor`."""
    pm = find_para(doc, anchor)
    para = pm.group(0)
    runs = list(RUN.finditer(para))
    if not runs:
        raise ValueError("anchor paragraph has no run to copy")
    run = runs[0].group(0)
    tm = TEXT.search(run)
    text = esc(text)
    run_new = run[: tm.start()] + tm.group(1).replace("<w:t", '<w:t xml:space="preserve"', 1) \
        .replace(' xml:space="preserve" xml:space="preserve"', ' xml:space="preserve"') \
        + text + tm.group(3) + run[tm.end():]
    if mark:
        run_new = _mark_run(run_new)
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", para, re.S)
    new_para = "<w:p>" + (ppr.group(0) if ppr else "") + run_new + "</w:p>"
    at = pm.end() if after else pm.start()
    doc.xml = doc.xml[:at] + new_para + doc.xml[at:]
