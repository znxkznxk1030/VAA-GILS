"""Helpers for editing paper/jkiie_submit_body.docx without breaking its formatting.

Import from a script (keep the script outside this folder, e.g. in a scratch dir):

    import sys; sys.path.insert(0, ".claude/skills/jkiie-docx-format/scripts")
    from docx_lib import *
    z, files, d = load("paper/jkiie_submit_body.docx")
    base = d
    ...edit d...
    save(z, files, d, "/tmp/out.docx")      # validates the XML
    para_diff(base, d)                      # prints every paragraph whose text changed

Conventions implemented here are documented in ../references/format_spec.md.
"""
from __future__ import annotations

import difflib
import re
import subprocess
import tempfile
import zipfile
import xml.dom.minidom
from xml.sax.saxutils import escape

# --------------------------------------------------------------------------- patterns
# A run that never crosses its own closing tag. Never write r'<w:r ...>(.*?)OLD' with re.S:
# the lazy group can start in an earlier run and swallow whole paragraphs.
RUN = re.compile(r'<w:r(?: [^>]*)?>(?:(?!</w:r>).)*?</w:r>', re.S)
PARA = re.compile(r'<w:p[ >](?:(?!</w:p>).)*</w:p>', re.S)
TABLE = re.compile(r'<w:tbl>.*?</w:tbl>', re.S)
TEXT = re.compile(r'<w:t[^>]*>([^<]*)</w:t>|<m:t[^>]*>([^<]*)</m:t>')

# --------------------------------------------------------------------------- paragraph properties
FONT_THEME = '<w:rFonts w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/>'
FONT_THEME_H = '<w:rFonts w:asciiTheme="minorEastAsia" w:eastAsiaTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/>'
SP480 = '<w:spacing w:line="480" w:lineRule="auto"/>'
PPR_FIRST = f'<w:pPr><w:pStyle w:val="FirstParagraph"/>{SP480}</w:pPr>'           # first paragraph after a heading
PPR_BODY = f'<w:pPr><w:pStyle w:val="a0"/>{SP480}<w:ind w:firstLine="216"/></w:pPr>'  # any other body paragraph
PPR_H1 = f'<w:pPr><w:pStyle w:val="1"/><w:spacing w:line="448" w:lineRule="exact"/><w:rPr>{FONT_THEME_H}</w:rPr></w:pPr>'
PPR_H2 = f'<w:pPr><w:pStyle w:val="2"/><w:spacing w:line="384" w:lineRule="exact"/><w:rPr>{FONT_THEME_H}</w:rPr></w:pPr>'
PPR_TABLE_CAPTION = '<w:pPr><w:pStyle w:val="TableCaption"/><w:jc w:val="center"/></w:pPr>'
PPR_IMAGE_CAPTION = '<w:pPr><w:pStyle w:val="ImageCaption"/><w:jc w:val="center"/></w:pPr>'
PPR_FIGURE = '<w:pPr><w:pStyle w:val="CaptionedFigure"/><w:spacing w:after="120"/><w:jc w:val="center"/></w:pPr>'
PPR_REFERENCE = '<w:pPr><w:pStyle w:val="a0"/><w:ind w:firstLine="216"/></w:pPr>'           # single spaced
PPR_CELL = '<w:pPr><w:pStyle w:val="Compact"/><w:spacing w:after="0"/></w:pPr>'
HL = '<w:highlight w:val="yellow"/>'
MATH_RPR = '<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'
MATH_RPR_HL = '<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>' + HL + '</w:rPr>'


# --------------------------------------------------------------------------- file I/O
def load(path):
    z = zipfile.ZipFile(path)
    files = {k: z.read(k) for k in z.namelist()}
    return z, files, files['word/document.xml'].decode()


def save(z, files, d, out, media=None):
    """Write a copy with document.xml replaced (and optional {'word/media/x.png': bytes})."""
    xml.dom.minidom.parseString(d.encode())  # raises on broken XML
    files = dict(files)
    files['word/document.xml'] = d.encode()
    for k, v in (media or {}).items():
        files[k] = v
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as w:
        for k in z.namelist():
            w.writestr(z.getinfo(k), files[k])


# --------------------------------------------------------------------------- reading
def text(fragment):
    """Visible text of a paragraph/run, including equation text."""
    return ''.join(a or b for a, b in TEXT.findall(fragment))


def table_spans(d):
    return [(m.start(), m.end()) for m in TABLE.finditer(d)]


def in_table(pos, spans):
    return any(a <= pos < b for a, b in spans)


def find_paras(d, needle, start=True):
    """Matches of paragraphs whose text starts with (or contains) `needle`."""
    return [m for m in PARA.finditer(d) if (text(m.group(0)).startswith(needle) if start else needle in text(m.group(0)))]


def one_para(d, needle, start=True):
    hits = find_paras(d, needle, start)
    assert len(hits) == 1, (needle, len(hits))
    return hits[0]


def ppr_of(p):
    m = re.search(r'<w:pPr>.*?</w:pPr>', p, re.S)
    return m.group(0) if m else ''


def rpr_of(run):
    m = re.search(r'<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>', run, re.S)
    return m.group(0) if m else '<w:rPr></w:rPr>'


def with_highlight(rpr):
    if HL in rpr:
        return rpr
    if '<w:vertAlign' in rpr:  # highlight must precede vertAlign in the schema order
        return rpr.replace('<w:vertAlign', HL + '<w:vertAlign', 1)
    return rpr.replace('</w:rPr>', HL + '</w:rPr>', 1)


# --------------------------------------------------------------------------- inline math as formatted runs
GREEK = {r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ', r'\varepsilon': 'ε', r'\epsilon': 'ε',
         r'\lambda': 'λ', r'\mu': 'μ', r'\pi': 'π', r'\rho': 'ρ', r'\sigma': 'σ', r'\tau': 'τ', r'\omega': 'ω',
         r'\Delta': 'Δ', r'\Pi': 'Π', r'\Omega': 'Ω', r'\Sigma': 'Σ', r'\varPi': 'Π', r'\varDelta': 'Δ', r'\varOmega': 'Ω'}
# Capital Greek written as \Pi etc. is upright (operator-like: Δbo, Ω); a capital Greek *variable* such as the
# instance set must be written \varPi so it comes out italic -- upright Π inside Korean text reads like 'ㅍ'.
UPRIGHT_GREEK = {r'\Delta', r'\Pi', r'\Omega', r'\Sigma'}
RELATIONS = {r'\in': '∈', r'\le': '≤', r'\leq': '≤', r'\ge': '≥', r'\geq': '≥', r'\ne': '≠', r'\neq': '≠',
             r'\sim': '∼', r'\leftarrow': '←', r'\gets': '←', r'\to': '→', r'\rightarrow': '→'}
SYMBOLS = {r'\cup': '∪', r'\cap': '∩', r'\setminus': '∖', r'\times': '×', r'\cdot': '·', r'\infty': '∞',
           r'\sum': '∑', r'\ldots': '…', r'\{': '{', r'\}': '}', r'\max': 'max', r'\min': 'min', r'\arg': 'arg',
           r'\prime': '′'}
SPACES = {r'\,': ' ', r'\ ': ' ', r'\quad': ' ', r'\qquad': '  ', r'\textstyle': '', r'\displaystyle': ''}
SCRIPT = {c: chr(0x1D49C + i) for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}
SCRIPT.update({'B': 'ℬ', 'E': 'ℰ', 'F': 'ℱ', 'H': 'ℋ', 'I': 'ℐ', 'L': 'ℒ', 'M': 'ℳ', 'R': 'ℛ'})  # Unicode holes


def _font(name):
    # All four slots: in this Korean document Word draws math operators (∈ ∼ ∑ …) and some Greek with the
    # eastAsia slot. Leaving eastAsia empty falls back to 맑은 고딕 in Word even though LibreOffice looks right.
    return f'<w:rFonts w:ascii="{name}" w:eastAsia="{name}" w:hAnsi="{name}" w:cs="{name}"/>'


def latex_runs(expr, _script=False):
    """LaTeX math -> [(text, kind, vert)], kind in {'var', 'sym', 'script'}.

    Spacing follows TeX rather than the source: source whitespace is dropped, relations get one
    space on each side on the main line, nothing inside sub/superscripts.
    """
    expr = re.sub(r'\\mathcal\{([A-Z])\}', lambda m: SCRIPT[m.group(1)], expr)
    expr = re.sub(r'\\operatorname\*?\{arg\\,?max\}', 'argmax', expr)
    expr = re.sub(r'\\operatorname\*?\{arg\\,?min\}', 'argmin', expr)
    expr = re.sub(r'\\bar\s*\{?([A-Za-z])\}?', lambda m: m.group(1) + '\u0304', expr)
    expr = expr.replace('{}', '')
    out, i = [], 0

    def emit(t, kind, vert=None):
        if t:
            out.append((t, kind, vert))

    while i < len(expr):
        c = expr[i]
        if c.isspace():
            i += 1
            continue
        if c == '\\':
            m = re.match(r'\\(?:text|mathrm|textrm)\{([^}]*)\}', expr[i:])
            if m:
                emit(m.group(1), 'sym'); i += m.end(); continue
            m = re.match(r'\\[A-Za-z]+|\\[{},  ]', expr[i:])
            tok = m.group(0); i += len(tok)
            if tok in GREEK:
                emit(GREEK[tok], 'sym' if tok in UPRIGHT_GREEK else 'var')
            elif tok in RELATIONS:
                emit(' ' + RELATIONS[tok] + ' ', 'sym')
            elif tok in SYMBOLS:
                emit(SYMBOLS[tok], 'sym')
            elif tok in SPACES:
                emit(SPACES[tok], 'sym')
            elif tok in (r'\mathcal',):
                continue
            else:
                raise ValueError(f'unsupported LaTeX token {tok!r} in {expr!r}')
            continue
        if c in '_^':
            vert = 'subscript' if c == '_' else 'superscript'
            if expr[i + 1] == '{':
                depth, j = 0, i + 1
                while True:
                    depth += {'{': 1, '}': -1}.get(expr[j], 0)
                    if depth == 0:
                        break
                    j += 1
                inner, i = expr[i + 2:j], j + 1
            elif expr[i + 1] == '\\':
                tok = re.match(r'\\[A-Za-z]+', expr[i + 1:]).group(0)
                inner, i = tok, i + 1 + len(tok)
            else:
                inner, i = expr[i + 1], i + 2
            for t, k, _ in latex_runs(inner):
                emit(t.strip() if t.strip() else '', k, vert)  # no spaces inside scripts
            continue
        if c in '{}':
            i += 1; continue
        if '\U0001D400' <= c <= '\U0001D7FF' or c in 'ℬℰℱℋℐℒℳℛ':
            emit(c, 'script'); i += 1; continue
        if c.isalpha():
            emit(c, 'var'); i += 1; continue
        emit({'-': '−', '=': ' = ', '<': ' < ', '>': ' > ', ',': ', ', "'": '′'}.get(c, c), 'sym'); i += 1
    # merge neighbours with the same kind/vert, then collapse doubled spaces
    merged = []
    for t, k, v in out:
        if merged and merged[-1][1:] == (k, v):
            merged[-1] = (merged[-1][0] + t, k, v)
        else:
            merged.append((t, k, v))
    flat, prev_space = [], False
    for t, k, v in merged:
        t = re.sub(r' {2,}', ' ', t)
        if prev_space and t.startswith(' '):
            t = t[1:]
        if t:
            flat.append((t, k, v)); prev_space = t.endswith(' ')
    if flat and flat[0][0].startswith(' ') and flat[0][2] is None:
        flat[0] = (flat[0][0].lstrip(), *flat[0][1:])
    return [x for x in flat if x[0]]


def math_run(t, kind, vert=None, sz=None, highlight=True):
    if kind == 'var':
        rpr = _font('Cambria') + '<w:i/>'
    else:  # 'sym' and 'script' (script letters must not be italic)
        rpr = _font('Cambria Math')
    if sz:
        rpr += f'<w:sz w:val="{sz}"/>'
    if highlight:
        rpr += HL
    if vert:
        rpr += f'<w:vertAlign w:val="{vert}"/>'
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(t)}</w:t></w:r>'


def prose_run(t, sz=None, highlight=True, bold=False, italic=False):
    rpr = FONT_THEME + ('<w:b/><w:bCs/>' if bold else '') + ('<w:i/><w:iCs/>' if italic else '')
    rpr += (f'<w:sz w:val="{sz}"/>' if sz else '') + (HL if highlight else '')
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(t)}</w:t></w:r>'


def clean_text(src, labels=None):
    """tex prose -> Word prose: refs, non-breaking space in <Table N>, dashes, \\%."""
    if labels:
        src = re.sub(r'\\ref\{([^}]+)\}', lambda m: labels[m.group(1)], src)
    src = src.replace('<Table~', '<Table\u00a0').replace('<Figure~', '<Figure\u00a0').replace('<Table ', '<Table\u00a0').replace('<Figure ', '<Figure\u00a0')
    src = src.replace('\\%', '%').replace('{,}', ',').replace('---', '—').replace('--', '–').replace('~', '\u00a0')
    src = re.sub(r'\\emph\{([^}]*)\}', r'\1', src)
    return re.sub(r'\s*\n\s*', ' ', src)


def text_runs(src, sz=None, highlight=True, labels=None):
    """tex-like prose with $...$ math -> Word runs following the paper's conventions."""
    out = ''
    for k, part in enumerate(re.split(r'\$([^$]*)\$', clean_text(src, labels))):
        if k % 2 == 0:
            assert '\\' not in part, ('raw LaTeX outside $...$', part[:80])
            if part:
                out += prose_run(part, sz, highlight)
        else:
            out += ''.join(math_run(t, kd, v, sz, highlight) for t, kd, v in latex_runs(part))
    return out


def tex_labels(tex_path='paper/jkiie_submit_body.tex'):
    """\\label{...} -> number as written in the caption ("4", "A1")."""
    tex = open(tex_path, encoding='utf-8').read()
    return {m.group(2): m.group(1).split()[1]
            for m in re.finditer(r'\\caption\{((?:Figure|Table|Algorithm) [A-Z]?\d+)\..*?\\label\{([^}]+)\}', tex, re.S)}


# --------------------------------------------------------------------------- display equations
def omml(latex, highlight=True):
    """Display equation via pandoc -> <m:oMathPara>. Put the number as '\\qquad (n)' at the end."""
    latex = latex.replace('\\qquad', '\\ \\ \\ \\ ')
    doc = '\\documentclass{article}\\usepackage{amsmath}\\begin{document}\n\\[' + latex + '\\]\n\\end{document}\n'
    with tempfile.TemporaryDirectory() as td:
        open(td + '/a.tex', 'w').write(doc)
        subprocess.run(['pandoc', td + '/a.tex', '-o', td + '/a.docx'], check=True, capture_output=True)
        x = zipfile.ZipFile(td + '/a.docx').read('word/document.xml').decode()
    o = re.search(r'<m:oMathPara>.*?</m:oMathPara>', x, re.S).group(0)
    rpr = MATH_RPR_HL if highlight else MATH_RPR

    def fix_r(mm):
        r = mm.group(0)
        if '<w:rPr>' in r:
            return r
        if '</m:rPr>' in r:
            return r.replace('</m:rPr>', '</m:rPr>' + rpr, 1)
        return r.replace('<m:r>', '<m:r>' + rpr, 1)

    o = re.sub(r'<m:r>.*?</m:r>', fix_r, o, flags=re.S)
    o = re.sub(r'<m:ctrlPr\s*/>', '<m:ctrlPr>' + rpr + '</m:ctrlPr>', o)
    o = o.replace('\u2005', '  ').replace('<m:t>', '<m:t xml:space="preserve">')
    if '<m:oMathParaPr>' not in o:
        o = o.replace('<m:oMathPara>', '<m:oMathPara><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr>', 1)
    return o


def equation_paragraph(latex, after_heading=False, highlight=True):
    ppr = PPR_FIRST if after_heading else PPR_BODY
    return '<w:p>' + ppr + omml(latex, highlight) + '</w:p>'


# --------------------------------------------------------------------------- editing
def replace_in_run(d, old, new, skip_tables=False, expect=1, highlight=True):
    """Replace text that sits inside single runs; only the new text is highlighted."""
    spans = table_spans(d) if skip_tables else []
    out, pos, n = [], 0, 0
    for m in RUN.finditer(d):
        run = m.group(0)
        if spans and in_table(m.start(), spans):
            continue
        t = re.search(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', run)
        if not t or old not in t.group(1):
            continue
        rpr = rpr_of(run)
        marks = ''.join(re.findall(r'<w:lastRenderedPageBreak/>|<w:br[^>]*/>|<w:tab/>', run[:t.start()]))
        parts = t.group(1).split(old)
        n += len(parts) - 1
        x = f'<w:r>{rpr}{marks}</w:r>' if marks else ''
        for k, pc in enumerate(parts):
            if pc:
                x += f'<w:r>{rpr}<w:t xml:space="preserve">{pc}</w:t></w:r>'
            if k < len(parts) - 1:
                x += f'<w:r>{with_highlight(rpr) if highlight else rpr}<w:t xml:space="preserve">{new}</w:t></w:r>'
        out += [d[pos:m.start()], x]
        pos = m.end()
    out.append(d[pos:])
    assert n == expect, (n, old[:40])
    return ''.join(out)


def replace_para(d, match, new_xml):
    return d[:match.start()] + new_xml + d[match.end():]


def insert_after(d, match, new_xml):
    return d[:match.end()] + new_xml + d[match.end():]


def body_paragraph(src, after_heading=False, highlight=True, labels=None):
    return '<w:p>' + (PPR_FIRST if after_heading else PPR_BODY) + text_runs(src, None, highlight, labels) + '</w:p>'


# --------------------------------------------------------------------------- verification
def para_diff(old, new, width=160):
    """Print paragraphs whose text changed; returns the number of changed paragraphs."""
    a = [text(p) for p in PARA.findall(old)]
    b = [text(p) for p in PARA.findall(new)]
    print(f'paragraphs {len(a)} -> {len(b)}')
    n = 0
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == 'equal':
            continue
        n += max(a2 - a1, b2 - b1)
        for x in a[a1:a2]:
            print('  -', x[:width])
        for y in b[b1:b2]:
            print('  +', y[:width])
    return n


def text_width_dxa(s, sz=18):
    """Rendered width of `s` in Malgun Gothic at sz half-points (for table column widths)."""
    from PIL import ImageFont
    font = ImageFont.truetype('/Applications/Microsoft Word.app/Contents/Resources/DFonts/malgun.ttf', 1000)
    return font.getlength(s) / 1000 * (sz / 2) * 20


def render(docx, outdir, pages=None, dpi=90):
    """LibreOffice render -> PNG pages (Korean shows blank: no Korean font in LibreOffice here)."""
    import os
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/lo/profile', '--headless', '--convert-to', 'pdf',
                    '--outdir', outdir, docx], check=True, capture_output=True)
    pdf = os.path.join(outdir, os.path.basename(docx).rsplit('.', 1)[0] + '.pdf')
    if pages:
        subprocess.run(['pdftoppm', '-f', str(pages[0]), '-l', str(pages[-1]), '-r', str(dpi), '-png', pdf,
                        os.path.join(outdir, 'page')], check=True)
    return pdf
