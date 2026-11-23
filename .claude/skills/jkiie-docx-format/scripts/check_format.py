"""Audit paper/jkiie_submit_body.docx against the paper's formatting conventions.

Usage:
    python .claude/skills/jkiie-docx-format/scripts/check_format.py paper/jkiie_submit_body.docx [--all]

Prints findings grouped by rule (first few examples each; --all prints every example).
Rules mirror references/format_spec.md. A finding is a prompt to look, not proof of an error:
check the example in context before changing anything.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_lib import PARA, RUN, TABLE, load, text  # noqa: E402

TEXT_WIDTH = 9360          # dxa
MAX_FIG_EMU = 5852160      # 6.4 in
MATH_CHARS = re.compile(r'[Ͱ-Ͽ\U0001d400-\U0001d7ffℬℰℱℋℐℒℳℛ∈∪∼≤≥≠←∑∞∖]')
SCRIPT_CHARS = re.compile(r'[\U0001d400-\U0001d7ffℬℰℱℋℐℒℳℛ]')
HANGUL = re.compile(r'[가-힣]')


def style(p):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    return m.group(1) if m else '-'


def ppr(p):
    m = re.search(r'<w:pPr>.*?</w:pPr>', p, re.S)
    return re.sub(r'<w:rPr>.*?</w:rPr>', '', m.group(0)) if m else ''


def main(path, show_all=False):
    _, _, d = load(path)
    findings = defaultdict(list)
    add = lambda rule, ex: findings[rule].append(ex)
    spans = [(m.start(), m.end()) for m in TABLE.finditer(d)]
    paras = list(PARA.finditer(d))
    texts = [text(m.group(0)) for m in paras]
    ref_start = next((i for i, t in enumerate(texts) if t.strip() == '참고문헌'), len(paras))
    ai_note = {i for i, t in enumerate(texts) if t.startswith('본 논문의 작성 과정에서 저자는 생성형 AI')}

    eq_numbers, table_caps, fig_caps = [], [], []
    for i, m in enumerate(paras):
        p, t = m.group(0), texts[i]
        intab = any(a <= m.start() < b for a, b in spans)
        st, pp = style(p), ppr(p)
        # ---- headings
        if st == '1' and 'w:line="448"' not in pp:
            add('장 제목 줄간격(line 448 exact) 없음', t[:40])
        if st == '2':
            if 'w:line="384"' not in pp:
                add('절 제목 줄간격(line 384 exact) 없음', t[:40])
            if not re.match(r'^\d+\.\d+ ', t):
                add('절 제목이 "N.M 제목" 형식이 아님', t[:40])
        # ---- body line spacing / indent
        if not intab and st in ('a0', 'FirstParagraph') and t.strip() and i < ref_start and i not in ai_note:
            if 'w:line="480"' not in pp:
                add('본문 문단에 2줄 간격(line 480) 없음', t[:50])
            if st == 'a0' and '<m:oMathPara>' not in p and 'w:firstLine="216"' not in pp:
                add('a0 본문 문단에 첫 줄 들여쓰기(216) 없음', t[:50])
        if i > ref_start and st == 'a0' and t.strip() and re.search(r'\(\d{4}[a-z]?\)', t):
            if 'w:line="480"' in pp:
                add('참고문헌 항목이 2줄 간격임(1줄이어야 함)', t[:50])
            if '<w:i/>' not in p:
                add('참고문헌 항목에 기울임(학술지명) run이 없음', t[:50])
        # ---- display equations
        if '<m:oMathPara>' in p and not intab:
            if 'w:line="480"' not in pp:
                add('별행 수식 단락에 line 480 없음', t[-30:])
            for n in re.findall(r'\((\d+)\)(?=,|\s*$)', re.sub(r'\s+', ' ', t)):  # skip min^{(2)} etc.
                eq_numbers.append(int(n))
        # ---- captions
        if st == 'TableCaption':
            table_caps.append(t)
            if '<w:jc w:val="center"/>' not in pp:
                add('표 캡션 가운데 정렬 아님', t[:40])
            nxt = d[m.end():m.end() + 400]
            if not re.match(r'\s*(<w:bookmark[^>]*/>\s*)*<w:tbl>', nxt):
                add('표 캡션 바로 뒤에 표가 없음(캡션은 표 위)', t[:40])
        if st == 'ImageCaption' and not t.startswith('Algorithm'):  # Algorithm 1 caption shares the style but sits above a table
            fig_caps.append(t)
            if '<w:jc w:val="center"/>' not in pp:
                add('그림 캡션 가운데 정렬 아님', t[:40])
            if i == 0 or '<w:drawing' not in paras[i - 1].group(0):
                add('그림 캡션 바로 앞에 그림 단락이 없음(캡션은 그림 아래)', t[:40])
        if '<w:drawing' in p:
            if st != 'CaptionedFigure':
                add('그림 단락 스타일이 CaptionedFigure가 아님', st)
            ext = re.search(r'<wp:extent cx="(\d+)"', p)
            if ext and int(ext.group(1)) > MAX_FIG_EMU:
                add('그림 폭이 6.4 in 초과', f'{int(ext.group(1)) / 914400:.2f} in')
            if '<wp:anchor' in p:
                add('그림이 inline이 아님(anchor)', t[:30])
        # ---- cross references
        for mm in re.finditer(r'&lt;(Table|Figure) [A-Z]?\d+&gt;', t):
            add('<Table/Figure N> 사이 공백이 일반 공백(U+00A0이어야 함)', t[max(0, mm.start() - 15):mm.end() + 5])
        # ---- runs: math fonts and spacing
        runs = list(RUN.finditer(p))
        maths = [(a.start(), a.end()) for a in re.finditer(r'<m:oMath>.*?</m:oMath>', p, re.S)]
        prev_end, prev_space = 0, False
        for r in runs:
            rr = r.group(0)
            rt = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', rr))
            if not rt:
                continue
            if any(prev_end <= a < r.start() for a, b in maths):
                prev_space = False
            prev_end = r.end()
            tnr = 'Times New Roman' in rr
            theme = 'asciiTheme="minorEastAsia"' in rr or '<w:rFonts' not in rr
            fm = re.search(r'<w:rFonts ([^>]*)/>', rr)
            if fm and 'w:ascii="Cambria' in fm.group(1) and 'w:eastAsia=' not in fm.group(1):
                add('수식 글자 run에 eastAsia 글꼴이 없음(Word에서 맑은 고딕으로 그려짐)', rt[:20])
            if SCRIPT_CHARS.search(rt) and 'Cambria Math' not in rr:
                add('수학 필기체(𝒳 등)가 Cambria Math가 아님', rt[:20])
            if not tnr and theme and not HANGUL.search(rt) and MATH_CHARS.search(rt) and len(rt) <= 20 and not intab:
                add('수식 기호가 본문 글꼴(맑은 고딕)로 들어감', rt[:20])
            if '<w:vertAlign' in rr and re.search(r'\s[∈=≠≤≥∪∼]|[∈=≠≤≥∪∼]\s', rt):
                add('첨자 안에 공백이 있음', rt[:20])
            if not intab and not tnr:
                if '  ' in rt:
                    add('이중 공백', rt[:30])
                elif prev_space and rt.startswith(' '):
                    add('run 경계의 이중 공백', rt[:30])
            prev_space = rt.endswith(' ')
    # ---- tables
    for m in TABLE.finditer(d):
        tb = m.group(0)
        head = text(tb)[:30]
        grid = [int(x) for x in re.findall(r'<w:gridCol w:w="(\d+)"', tb)]
        if '<w:tblLayout w:type="fixed"/>' not in tb:
            add('표 레이아웃이 fixed가 아님', head)
        if sum(grid) > TEXT_WIDTH:
            add('표 열 폭 합이 본문 폭(9360) 초과', f'{head} ({sum(grid)})')
        for row in re.findall(r'<w:tr[ >].*?</w:tr>', tb, re.S):
            tcw = [int(x) for x in re.findall(r'<w:tcW w:w="(\d+)" w:type="dxa"/>', row)]
            if tcw and len(tcw) == len(grid) and tcw != grid:
                add('셀 폭(tcW)이 gridCol과 다름', head)
                break
    # ---- numbering
    expected = list(range(1, max(eq_numbers) + 1)) if eq_numbers else []
    if sorted(set(eq_numbers)) != expected:
        add('식 번호가 1부터 연속이 아님', f'missing {sorted(set(expected) - set(eq_numbers))}')
    if len(eq_numbers) != len(set(eq_numbers)):
        add('식 번호 중복', str(sorted(n for n in set(eq_numbers) if eq_numbers.count(n) > 1)))
    def seq(caps, word):
        nums = [re.match(word + r' ([A-Z]?\d+)\.', c) for c in caps]
        if not all(nums):
            add(f'{word} 캡션이 "{word} N. " 형식이 아님', str([c[:20] for c, n in zip(caps, nums) if not n]))
        main_nums = [int(n.group(1)) for n in nums if n and n.group(1).isdigit()]
        if main_nums != list(range(1, len(main_nums) + 1)):
            add(f'{word} 번호가 순서대로가 아님', str(main_nums))
    seq(table_caps, 'Table')
    seq(fig_caps, 'Figure')
    # ---- report
    hl = d.count('<w:highlight w:val="yellow"/>')
    print(f'{path}: paragraphs {len(paras)}, tables {len(spans)}, figures {len(fig_caps)}, '
          f'equation numbers {min(eq_numbers, default=0)}–{max(eq_numbers, default=0)}, highlighted runs {hl}')
    if not findings:
        print('OK: no findings')
        return 0
    for rule, exs in findings.items():
        print(f'\n[{len(exs)}] {rule}')
        for e in (exs if show_all else exs[:5]):
            print('    ', repr(e))
        if not show_all and len(exs) > 5:
            print(f'     ... {len(exs) - 5} more (--all)')
    return 1


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    sys.exit(main(args[0] if args else 'paper/jkiie_submit_body.docx', '--all' in sys.argv))
