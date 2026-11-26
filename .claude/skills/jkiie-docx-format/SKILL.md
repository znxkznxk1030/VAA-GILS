---
name: jkiie-docx-format
description: 대한산업공학회지 투고 원고 paper/jkiie_submit_body.docx(VAA-GILS 논문)의 Word 서식 규칙(줄간격, 제목, 본문 수식과 식 번호, 표, 그림, 캡션, 참고문헌, 상호참조, 수정 표시)과 이를 지키며 OOXML을 직접 고치는 방법. 이 Word 원고에 문단·문장·식·표·그림·참고문헌을 추가하거나 고칠 때, tex 원고의 수정을 Word에 옮길 때, 심사 의견 반영분을 Word에 넣을 때, 줄간격·자간·글꼴·하이라이트가 이상하다는 지적을 받았을 때, 제출 전 Word 서식을 점검할 때 반드시 이 스킬을 먼저 사용한다. 사용자가 서식을 명시하지 않아도 jkiie_submit_body.docx를 건드리는 작업이면 적용한다.
---

# JKIIE 원고 Word 서식 스킬

이 원고는 pandoc으로 만든 뒤 Word에서 다듬은 문서라 스타일 이름이 pandoc 계열(`FirstParagraph`, `Compact`, `ImageCaption` …)이고, 일부 서식은 스타일이 아니라 문단마다 직접 지정되어 있다. 그래서 새 문단을 넣을 때 스타일만 맞추면 줄간격이나 들여쓰기가 달라진다. 이 스킬은 실제 원고에서 조사한 규칙과, 지난 수정에서 실제로 생긴 문제(줄간격 누락, 수식 자간, 글꼴 대체, run 경계를 넘는 치환으로 문서가 깨진 일)를 피하는 작업 방법을 담는다.

- 원고: `paper/jkiie_submit_body.docx` (Word, 제출용), `paper/jkiie_submit_body.tex` → `.pdf` (같은 내용의 LaTeX판)
- 투고본(비교 기준): `paper/jkiie_submit_body_v4.docx`
- 상세 XML 규격: `references/format_spec.md` — 새 문단·식·표·그림을 만들 때 해당 절을 읽는다.
- 도구: `scripts/docx_lib.py`(편집 함수), `scripts/check_format.py`(서식 점검)

## 핵심 서식 요약

| 요소 | 규칙 |
|---|---|
| 쪽 | Letter(12240×15840), 여백 위 1701·나머지 1440 dxa → 본문 폭 9360 dxa(6.5in). 머리글 없음, 바닥글 쪽 번호 |
| 본문 글꼴 | run에 `rFonts asciiTheme/hAnsiTheme="minorEastAsia"`(맑은 고딕), 크기 지정 없음(Normal 10pt) |
| 장 제목 | 스타일 `1`, `line=448 exact`, 번호를 글자로 씀: "3. 휴리스틱 알고리즘" |
| 절 제목 | 스타일 `2`, `line=384 exact`, "2.1 기호 정의" |
| 제목 바로 뒤 본문 | `FirstParagraph` + `line=480 auto`(2줄), 들여쓰기 없음 |
| 그 밖의 본문 | `a0` + `line=480 auto` + `ind firstLine=216` |
| 별행 수식 | 본문과 같은 pPr 안에 `m:oMathPara`(`m:jc center`), 식 번호는 식 끝에 공백 4칸 뒤 "(n)" |
| 표 | 캡션이 표 **위**(`TableCaption`, 가운데, 9pt 기울임, 영문 "Table N. …"). 위·아래 굵은 선과 머리행 아래 선만 있는 3선 표, 셀은 `Compact` 9pt, `tblLayout fixed`, 폭 합 ≤ 9360 |
| 그림 | `CaptionedFigure` 단락에 inline 그림(폭 ≤ 6.4in), 캡션은 그림 **아래**(`ImageCaption`, 가운데, 9pt, 영문 "Figure N. …") |
| 참고문헌 | 제목 "참고문헌", 각 항목 `a0` + `firstLine=216`, **1줄 간격**(line 지정 없음), 학술지명만 기울임, 알파벳순 |
| 상호참조 | `<Table N>`, `<Figure N>`(사이에 줄바꿈 없는 공백 U+00A0), "식 (17)", 범위 "식 (18)–(19)"(en dash) |
| 인용 | 국문 본문 "(Van Belle 등, 2013)", 서술형 "Boysen과 Fliedner(2010)", 영문 표·캡션은 "et al." |
| 수정 표시 | 새로 쓰거나 바꾼 글자에 노란 하이라이트(`<w:highlight w:val="yellow"/>`). 지운 글자는 표시할 수 없으므로 `docs/response_to_reviewers.md`에 적는다 |

## 본문 속 수식(inline) 규칙

새 문단 안의 짧은 수식은 Word 수식 개체가 아니라 **서식 있는 글자 run**으로 넣는다. 사용자가 새로 넣은 inline 수식 개체가 빈칸으로 보인다고 한 적이 있기 때문이다(투고본부터 있던 inline 수식 개체는 그대로 둔다). 글자 run으로 넣을 때는 모양이 별행 수식과 어긋나지 않게 다음을 지킨다.

- 글꼴은 `rFonts`의 네 칸(`ascii`, `eastAsia`, `hAnsi`, `cs`)에 모두 지정한다. 한국어 문서에서 Word는 수학 기호와 일부 그리스 문자를 `eastAsia` 칸의 글꼴로 그린다. 이 칸을 비우면 Word에서는 맑은 고딕으로 남아 "고쳐지지 않았다"는 지적을 받았다. LibreOffice 렌더링으로는 확인되지 않는 문제다.
- 이탤릭 변수(라틴·소문자 그리스): `Cambria` + `<w:i/>` — 맑은 고딕의 그리스 문자는 산세리프 전각에 가까워 식과 어울리지 않는다.
- 연산자·대문자 그리스·숫자 기호(∈ ∪ ∼ ≤ ← ∑ Π Ω 등): `Cambria Math` — Cambria Italic에는 ∈ ∪ ∼ ∖가 없다.
- 수학 필기체(𝒳, 𝒜): `Cambria Math`, 기울임 없음 — 맑은 고딕·Cambria에 없어 대체 글꼴로 그려진다.
- 대문자 그리스 **변수**(인스턴스 집합 Π 등)는 이탤릭(`Cambria` + `<w:i/>`, tex `\varPi`). 곧은 Π는 한글 문장 사이에서 "ㅍ"처럼 보여 수식으로 읽히지 않는다. Δbo의 Δ나 연산자 집합 Ω처럼 이름에 가까운 기호는 곧은 글자로 둔다.
- 아래·위첨자는 `<w:vertAlign w:val="subscript|superscript"/>`. 첨자 안에는 공백을 넣지 않는다(`i∈I`).
- 공백은 관계 기호(=, ∈, ∼, ≤, ≥, ←) 양옆에만 한 칸. LaTeX 원문의 공백(`\rho H`의 공백 등)은 옮기지 않는다 — 옮기면 "ρ H", "∼  U"처럼 자간이 벌어진다.
- `scripts/docx_lib.py`의 `text_runs()`가 이 규칙대로 run을 만든다.

## 작업 순서

1. **읽기**: 고칠 문단을 텍스트로 찾고(`docx_lib.find_paras`), 주변 문단의 pPr을 확인한다. 같은 종류의 기존 문단이 있으면 그 pPr을 복사하는 것이 가장 안전하다.
2. **고치기**: Python으로 `word/document.xml`을 직접 고친다(아래 함정 참고). tex에도 같은 수정을 하고 `% Rx-y: 이유` 주석을 남긴다.
3. **검증**
   - XML 파싱(`docx_lib.save`가 자동으로 함)
   - 수정 전 파일과 **문단 단위 텍스트 비교**(`docx_lib.para_diff`): 의도한 문단만 바뀌었는지, 문단 수가 예상대로인지
   - `python .claude/skills/jkiie-docx-format/scripts/check_format.py paper/jkiie_submit_body.docx`로 서식 점검
   - LibreOffice 렌더링: `soffice -env:UserInstallation=file:///tmp/lo/profile --headless --convert-to pdf --outdir <dir> paper/jkiie_submit_body.docx` 후 `pdftoppm`으로 해당 쪽을 이미지로 본다. 이 컴퓨터의 LibreOffice에는 한글 글꼴이 없어 한글이 빈칸으로 보이고, Cambria는 Caladea로 대체된다. 파일 문제가 아니다.
4. **기록**: 답변서(`docs/response_to_reviewers.md`)와 스프레드시트의 상태·위치를 갱신한다.

## 함정 (실제로 겪은 것)

- **run 경계를 넘는 정규식**: `<w:r ...>(.*?)OLD`처럼 쓰면 `.*?`가 앞 run에서 시작해 여러 문단을 삼킨다. 1장 일부가 중복되고 하이라이트가 번진 적이 있다. run은 항상 `docx_lib.RUN`(`</w:r>`을 넘지 않는 패턴)으로 잡는다.
- **문장 속 낱말 고치기**: 고칠 문구가 여러 run에 걸쳐 있으면 `replace_in_run`으로는 찾지 못한다. `docx_lib.replace_text(d, old, new, expect=n)`을 쓴다. 문단 글자를 이어 붙여 찾고, old와 new의 공통 앞뒤는 원래 run에 남긴 채 **달라진 가운데 글자만** 새 run(노란색)으로 바꾼다. 수식 개체·탭·필드는 경계로 취급하고, 기본값으로 한글이 있는 문단만 고친다(영문 캡션·표 보호). 용어 통일·문체 교정처럼 많은 곳을 고칠 때는 (old, new, 횟수) 목록을 만들어 tex와 Word에 같은 순서로 적용하고, 적용 전에 두 파일에서 횟수를 먼저 확인한다(R1-2·R1-3에서 240여 곳을 이렇게 고쳤다).
- **새 국문 문장**: 용어와 문체는 `docs/revision_drafts/R1-2_R1-3_terms_style.md`의 용어 대조표(5절)와 문체 원칙(4.2절)을 따른다. 예: ablation → 제거 실험, greedy → 탐욕적, "고르다/쓰다/바꾸다" → "선택하다/사용하다/변경하다".
- **줄간격 누락**: `FirstParagraph`/`a0` 스타일 자체에는 2줄 간격이 없다. 새 본문 문단에 `<w:spacing w:line="480" w:lineRule="auto"/>`를 빠뜨리면 그 문단만 1줄 간격이 된다.
- **수식 개체 양옆 공백**: inline 수식 개체(`m:oMath`) 앞뒤의 공백은 이중 공백이 아니다. 공백을 정리할 때 수식 개체를 사이에 둔 run은 건너뛴다.
- **pandoc OMML**: `\qquad`는 `\ \ \ \ `로 바꿔 넣고, 결과의 U+2005는 일반 공백 두 칸으로 바꾼다(식 번호 앞 간격이 사라짐). `{}^{(2)}`는 빈 상자가 생기므로 `\min^{(2)}_{...}`처럼 쓴다. `m:r`마다 `Cambria Math` rPr을 넣는다(`docx_lib.omml`이 처리).
- **의사코드(Algorithm 1)**: 3열 무테 표, Times New Roman 9pt. 본문 수식 글꼴 규칙을 이 표에 적용하지 않는다.
- **표 열 폭**: 맑은 고딕 9pt에서 "unloading"이 900 dxa 열에 들어가지 않아 끊겼다(R1-7). 열을 줄일 때는 가장 긴 단어 폭 + 216 dxa(셀 좌우 여백)를 확보한다. `docx_lib.text_width_dxa`로 모든 셀의 낱말을 재서 확인한다. 열 폭을 바꾸면 `tblW`, `tblGrid`, 모든 행의 `tcW`를 함께 바꾼다.
- **빗금으로 이어진 낱말**: "Inbound/outbound/compound", "(compound/outbound/destination/door)"는 한 낱말로 취급되어 좁은 열에서 글자 중간에 끊겼다. 빗금 뒤에 폭 없는 공백(U+200B)을 넣어 빗금 뒤에서만 줄이 바뀌게 한다(tex는 `\slash`).
- **그림 교체**: `word/media/imageN.png`를 같은 픽셀 크기로 바꾸면 `wp:extent`를 고칠 필요가 없다. 비율이 달라지면 `cx/cy`를 함께 고친다.

## 이 스킬이 다루지 않는 것

- 내용 수정의 판단(어떤 문장을 쓸지)은 각 심사 의견의 계획 문서(`docs/revision_drafts/`)를 따른다.
- tex/PDF의 서식은 LaTeX가 처리한다. Word와 tex의 내용이 같게 유지되는지만 확인한다.
