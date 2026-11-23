# jkiie_submit_body.docx 서식 규격 (XML 기준)

`paper/jkiie_submit_body.docx`에서 조사한 값이다(2026-11-23). 새 요소를 만들 때는 아래 템플릿을 쓰거나, 같은 종류의 기존 요소를 복사한 뒤 내용만 바꾼다. XML 예시에서 `w14:paraId`, `w:rsid*` 속성은 생략했다. 새 요소에는 넣지 않아도 된다.

## 목차
1. 문서 전체
2. 스타일과 기본 글꼴
3. 문단 템플릿 (제목, 본문, 초록)
4. run 템플릿 (본문, 수식 글자, 하이라이트)
5. 별행 수식
6. 표
7. 그림
8. 참고문헌
9. 상호참조와 표기
10. 수정 표시

---

## 1. 문서 전체

- 구역 하나. `<w:pgSz w:w="12240" w:h="15840"/>`(Letter), `<w:pgMar w:top="1701" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>`
- 본문 폭: 12240 − 1440 − 1440 = **9360 dxa = 6.5 in = 5,943,600 EMU**
- 머리글(`header1.xml`)은 비어 있고, 바닥글(`footer1.xml`)에 `PAGE` 필드가 있다.
- 순서: 제목 단락 → `Abstract` 제목 → 영문 초록 → Keywords → 1–7장 → 생성형 AI 사용 고지 → 참고문헌 → 부록 A(표 A1)

## 2. 스타일과 기본 글꼴

| styleId | 이름 | 스타일 정의 | 쓰임 |
|---|---|---|---|
| `a` | Normal | 10pt(`sz 20`), 검정 | 기반 |
| `a0` | Body Text | 앞뒤 간격 180 | 본문 문단 |
| `FirstParagraph` | First Paragraph | `a0` 기반 | 제목 바로 뒤 첫 문단 |
| `1` | heading 1 | 14pt 굵게, 앞 360 뒤 80, major 글꼴 | 장 제목, "참고문헌" |
| `2` | heading 2 | 12pt 굵게, 앞 160 뒤 80 | 절 제목 |
| `Compact` | Compact | `a0` 기반, 앞뒤 36 | 표 셀 |
| `TableCaption` | Table Caption | caption(기울임, 뒤 120) 기반, keepNext | 표 캡션 |
| `ImageCaption` | Image Caption | caption 기반 | 그림 캡션 |
| `CaptionedFigure` | Captioned Figure | keepNext | 그림이 든 단락 |
| `Abstract`, `AbstractTitle` | | | 초록 |

- 테마 글꼴: minor Latin = Aptos, minor 한글(Hang) = **맑은 고딕**. 본문 run은 `w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"`를 지정하므로 라틴 문자도 맑은 고딕으로 그려진다.
- 줄간격은 스타일이 아니라 **문단마다** `w:spacing`으로 지정되어 있다. 새 문단에 빠뜨리기 쉽다.

## 3. 문단 템플릿

### 장 제목 (번호는 글자로 직접 씀)
```xml
<w:p><w:pPr><w:pStyle w:val="1"/><w:spacing w:line="448" w:lineRule="exact"/><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:eastAsiaTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/></w:rPr></w:pPr>
<w:r><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:eastAsiaTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/></w:rPr><w:t>5. 실험 결과</w:t></w:r></w:p>
```
- 서론과 결론은 "1. 서 론", "7. 결 론"처럼 글자 사이를 띄어 쓴다.
- 기존 제목에는 `w:bookmarkStart/End`가 있다. 새 제목에는 넣지 않아도 된다.

### 절 제목
```xml
<w:p><w:pPr><w:pStyle w:val="2"/><w:spacing w:line="384" w:lineRule="exact"/><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:eastAsiaTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/></w:rPr></w:pPr>
<w:r><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:eastAsiaTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/></w:rPr><w:t>5.1 해 품질</w:t></w:r></w:p>
```

### 본문
| 종류 | pPr |
|---|---|
| 제목 바로 뒤 첫 문단 | `<w:pStyle w:val="FirstParagraph"/><w:spacing w:line="480" w:lineRule="auto"/>` |
| 그 밖의 문단 | `<w:pStyle w:val="a0"/><w:spacing w:line="480" w:lineRule="auto"/><w:ind w:firstLine="216"/>` |
| 1줄 간격 구역(생성형 AI 고지) | `<w:pStyle w:val="FirstParagraph"/>` (line 지정 없음) |

- pPr 안에 `<w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/></w:rPr>`(문단 표시 글꼴)가 함께 있는 문단이 많다. 있어도 되고 없어도 된다.
- 표·그림·식 뒤에서 이어지는 문단은 `a0` 형식을 쓴다.
- 절 안의 항목 이름(예: "반복 탐색(iterated search).")을 구분할 때는 그 부분만 `<w:b/>` run으로 만든다. 계획 문서: `docs/revision_drafts/R1-5_R2-5_headings.md`

### 제목 단락과 초록
- 논문 제목: `FirstParagraph` + `line 480` + `<w:jc w:val="center"/>`, 굵게. 국문 제목과 영문 제목이 같은 단락에 있다.
- `AbstractTitle` + `line 480`, run에 rPr 없음("Abstract").
- 초록 본문과 Keywords: `<w:pStyle w:val="Abstract"/><w:keepNext w:val="0"/><w:keepLines w:val="0"/><w:spacing w:line="480" w:lineRule="auto"/>`. "Keywords:"만 `<w:b/><w:bCs/>`이다. 초록은 150단어 이하(학회 규정)이며, 하이픈으로 이어진 단어는 나눠 센다.

## 4. run 템플릿

| 용도 | rPr |
|---|---|
| 본문 글자 | `<w:rFonts w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/>` |
| 표 셀·캡션 글자 (9pt) | 위 + `<w:sz w:val="18"/>` |
| 수식 이탤릭 변수 | `<w:rFonts w:ascii="Cambria" w:hAnsi="Cambria" w:cs="Cambria"/><w:i/>` (+ 첨자면 `<w:vertAlign w:val="subscript"/>`) |
| 수식 기호·대문자 그리스·첨자 숫자 | `<w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math" w:cs="Cambria Math"/>` |
| 수학 필기체 𝒳 𝒜 | Cambria Math, `<w:i/>` 없음 |
| 대문자 그리스 **변수** (인스턴스 집합 Π 등) | Cambria + `<w:i/>`. tex는 `\varPi`, 별행 수식은 `m:sty p`를 두지 않음 |
| 대문자 그리스 연산자·이름 (Δbo의 Δ, 연산자 집합 Ω) | Cambria Math, 곧은 글자 |
| 기울임 (학술지명) | 본문 글꼴 + `<w:i/><w:iCs/>` |
| 굵게 | `<w:b/><w:bCs/>` |
| 수정 표시 | rPr 끝에 `<w:highlight w:val="yellow"/>` (vertAlign보다 앞에 둔다) |

곧은 대문자 그리스 문자를 한글 문장 사이에 두면 "ㅍ" 같은 한글 자모처럼 보여 수식으로 읽히지 않는다는 지적이 있었다. 변수인 대문자 그리스 문자는 국제 표기 관례(ISO 80000-2)대로 이탤릭으로 쓴다.

**글꼴이 가진 문자** (Word 동봉 글꼴로 확인)
- 맑은 고딕: 그리스 문자는 있으나 산세리프, 𝒳 𝒜 없음
- Cambria: 그리스 문자 있음, 𝒳 𝒜 없음
- Cambria Italic: ∈ ∪ ∼ ∖ 𝒳 𝒜 없음
- Cambria Math: 위 문자 모두 있음

**공백 규칙** (본문 속 수식 글자)
- 관계 기호 = ∈ ∼ ≤ ≥ ≠ ← 양옆에만 한 칸. `+`, `−`, `×`, `/` 양옆과 첨자 안에는 공백을 넣지 않는다.
- 괄호 안 쉼표 뒤에는 한 칸: "(ρ, δ)", "U[0, ρH]"
- 이중 공백이 없어야 한다. 단, inline 수식 개체(`m:oMath`) 앞뒤의 공백은 정상이다.

## 5. 별행 수식

```xml
<w:p><w:pPr><w:pStyle w:val="a0"/><w:spacing w:line="480" w:lineRule="auto"/><w:ind w:firstLine="216"/></w:pPr>
<m:oMathPara><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr><m:oMath> … 식 … (n) </m:oMath></m:oMathPara></w:p>
```
- 제목 바로 뒤라면 pPr을 `FirstParagraph` + `line 480`으로 쓴다(식 (3)·(4) 단락 등).
- **식 번호**는 별도 탭이나 표 없이 식 안 끝에 공백 네 칸(`\ \ \ \ `)과 "(n)"으로 둔다. 번호는 문서 전체에서 하나씩 늘어난다. 현재 (1)–(21)이다(13·14는 한 줄에 함께 있음).
- 한 줄에 두 식을 둘 때: `식1 (1),\qquad 식2 (2)` 형식이다(기존 (1)·(2), (3)·(4), (13)·(14)).
- 모든 `m:r`에 `<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>`를 둔다. 수정 표시는 이 rPr에 `<w:highlight w:val="yellow"/>`를 더한다. LibreOffice는 수식 하이라이트를 그리지 않지만 Word는 그린다.
- 행렬 예시(3장 비용 행렬)는 별행 수식 단락 하나로 넣었다.
- 생성: `docx_lib.omml(latex, highlight=True)` (pandoc → `m:oMathPara`).

## 6. 표

### 캡션 (표 위)
```xml
<w:p><w:pPr><w:pStyle w:val="TableCaption"/><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">Table 6. Operator-pool ablation (…).</w:t></w:r></w:p>
```
- 영문, "Table N. " 다음에 문장. 기울임은 스타일에서 온다. 표 안 수식 기호는 inline 수식 개체를 쓰거나 §4의 수식 글자 run(9pt)을 쓴다.
- 번호는 등장 순서대로 Table 1–10, 부록은 Table A1이다. 캡션 글자에 번호가 직접 쓰여 있으므로, 표를 옮기거나 넣으면 캡션과 본문 참조를 모두 고친다.

### 결과 표 (3선 표) — Table 1, 2, 3–10, A1
```xml
<w:tbl><w:tblPr><w:tblStyle w:val="Table"/><w:tblW w:w="{합 또는 0}" w:type="{dxa|auto}"/>
<w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/><w:left w:val="none" w:sz="0" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/><w:right w:val="none" w:sz="0" w:space="0" w:color="000000"/><w:insideH w:val="none" w:sz="0" w:space="0" w:color="000000"/><w:insideV w:val="none" w:sz="0" w:space="0" w:color="000000"/></w:tblBorders>
<w:tblLayout w:type="fixed"/><w:tblLook w:val="0020" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="0"/></w:tblPr>
<w:tblGrid><w:gridCol w:w="…"/>…</w:tblGrid>
<!-- 머리행 -->
<w:tr><w:trPr><w:tblHeader/></w:trPr>
  <w:tc><w:tcPr><w:tcW w:w="…" w:type="dxa"/><w:tcBorders><w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/></w:tcBorders></w:tcPr>
    <w:p><w:pPr><w:pStyle w:val="Compact"/><w:spacing w:after="0"/></w:pPr><w:r><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/><w:sz w:val="18"/></w:rPr><w:t>Contrast</w:t></w:r></w:p></w:tc> …</w:tr>
<!-- 본문 행: tcBorders 없음 -->
<w:tr><w:tc><w:tcPr><w:tcW w:w="…" w:type="dxa"/></w:tcPr><w:p>…같은 pPr…</w:p></w:tc> …</w:tr></w:tbl>
```
- 위·아래 테두리는 sz 8, 머리행 아래만 sz 6. 세로선과 행 사이 선은 없다.
- 숫자 열은 셀 단락에 `<w:jc w:val="right"/>`를 둔다.
- `gridCol`과 각 행의 `tcW`가 같아야 한다. 폭 합은 9360 이하로 한다. 셀 좌우 여백이 각 108 dxa이므로, 글자가 들어갈 폭은 열 폭 − 216이다.
- 맑은 고딕 9pt에서 가장 긴 단어의 폭을 재서 열 폭을 정한다(`docx_lib.text_width_dxa`).
- 내용은 영문이다. 인용은 "et al.", 약어는 표 아래 주석으로 정의한다(계획: `docs/revision_drafts/R1-7_R2-4_table1.md`).

### 기호 표 (2.1절) — 예외
- 상자형 테두리 sz 6, 2열(1900 / 7100), 행마다 `<w:trPr><w:jc w:val="center"/></w:trPr>`
- 기호 셀은 `m:oMathPara`(Word 수식)이고, 설명 셀은 `Compact` + `<w:spacing w:before="0" w:after="0"/>`, 9pt
- 묶음 제목("집합", "파라미터", "결정변수")은 굵게
- 새 행은 `docx_lib`의 기존 행 복제 방식으로 만든다(기호는 `omml`, 설명은 `text_runs(sz=18)`).

### Algorithm 1 (의사코드) — 예외
- 3열 무테 표(420 / 5200 / 3230), 위·아래 sz 8 선만, `cantSplit`
- 셀 단락: `keepNext`, `keepLines`, `spacing before 0 after 0 line 240 auto`. 행 번호 열은 오른쪽 정렬, 회색(`666666`)
- 글꼴 Times New Roman 9pt(`sz 18`, eastAsia까지 TNR). 키워드(for, if, then …)는 굵게, 주석은 "▷ "로 시작하는 회색(`555555`)
- 본문 수식 글꼴 규칙(Cambria)을 이 표에 적용하지 않는다.

## 7. 그림

```xml
<w:p><w:pPr><w:pStyle w:val="CaptionedFigure"/><w:spacing w:after="120"/><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:noProof/><w:sz w:val="18"/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="…" cy="…"/> … <a:blip r:embed="rIdN"/> … <a:ext cx="…" cy="…"/> …</wp:inline></w:drawing></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="ImageCaption"/><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">Figure 6. …</w:t></w:r></w:p>
```
- 그림은 항상 inline이고 가운데 정렬이다. 폭은 6.4 in(5,852,160 EMU) 이하로 한다. 현재 폭: 6.4, 5.83, 4.6, 6.4, 5.83, 4.2 in
- `wp:extent`와 `a:ext`의 cx·cy를 같이 둔다. 비율은 PNG 픽셀 비율과 같게 맞춘다.
- 그림 파일(`word/media/imageN.png`)과 원본의 대응(현재)

| media | 그림 | 원본 |
|---|---|---|
| image4 | Figure 1 | `paper/figures/fig_problem_structure.drawio` |
| image1 | Figure 2 | `fig0_compound_timeline.drawio.svg` (draw.io 데이터 포함) |
| image5 | Figure 3 | `fig_transfer_example.drawio` |
| image6 | Figure 4 | `fig_algorithm_flow.drawio` |
| image2 | Figure 5 | `experiments/make_figures.py` → `fig2_operator_pool` |
| image3 | Figure 6 | `experiments/make_figures.py` → `fig4_lambda_tradeoff` |

- draw.io 그림은 `drawio -x -f png --scale 3 --border 8 -o out.png src` 형식으로 내보내면 지금 PNG와 크기가 같다. `make_fig_*.py`를 다시 실행하면 예전 그림으로 덮어쓰므로 쓰지 않는다.
- 캡션은 영문 "Figure N. …"이다. 그림 안 글자는 짧게 두고 설명은 캡션에 쓴다(교수님 피드백).

## 8. 참고문헌

```xml
<w:p><w:pPr><w:pStyle w:val="a0"/><w:ind w:firstLine="216"/></w:pPr>
<w:r><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/></w:rPr><w:t xml:space="preserve">Watkins, C. J. C. H. and Dayan, P.(1992), Q-Learning, </w:t></w:r>
<w:r><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/><w:i/><w:iCs/></w:rPr><w:t>Machine Learning</w:t></w:r>
<w:r><w:rPr><w:rFonts w:asciiTheme="minorEastAsia" w:hAnsiTheme="minorEastAsia"/></w:rPr><w:t>, 8, 279-292.</w:t></w:r></w:p>
```
- 형식: `성, 이니셜. and 성, 이니셜.(연도), 제목, ` + *학술지명* + `, 권(호), 쪽-쪽.`
  - 저자가 셋 이상이면 "A, B., C, D., and E, F."
  - 연도 앞에 공백을 두지 않는다: "M.(2016)"
  - 쪽 범위는 하이픈 "149-161"
- 1줄 간격(line 지정 없음), 첫 줄 들여쓰기 216
- 정렬은 제1저자 성의 알파벳순이다. 같은 저자는 연도순이고, 같은 해는 2013a, 2013b로 구분한다.
- 제목 단락은 장 제목 스타일 `1`의 "참고문헌"이다.
- 본문에 새 문헌을 인용하면 이 목록과 tex의 `\item`을 함께 추가한다.

## 9. 상호참조와 표기

- 표·그림 참조: `&lt;Table N&gt;`, `&lt;Figure N&gt;`(꺾쇠, 줄바꿈 없는 공백). 일반 공백이 섞인 곳이 있으면 고친다.
- 식 참조: "식 (17)", 범위 "식 (18)–(19)"(U+2013)
- 절 참조: "4.3절", 장 참조: "3장"
- 인용(국문 본문): 괄호형 "(Boysen and Fliedner, 2010; Van Belle 등, 2013)", 서술형 "Boysen과 Fliedner(2010)", "Li 등(2026)". 두 저자는 괄호형에서 "and", 서술형에서 "과/와"로 잇는다. 셋 이상은 "등"이다.
- 표와 캡션(영문)에서는 "Van Belle et al. (2013)"을 쓴다.
- 용어는 처음 나올 때 "국문(영문)"으로 병기한다. 예: "섭동 재시작(kick restart)"

## 10. 수정 표시

- 새로 쓰거나 바꾼 글자에만 노란 하이라이트를 넣는다. 일부만 바뀐 문단은 run을 나눠 바뀐 부분만 표시한다.
- 수식 개체 안의 글자는 `m:r`의 `w:rPr`에 하이라이트를 넣는다.
- 지운 글자, 줄간격·열 폭 같은 서식만 바뀐 곳은 표시할 수 없으므로 답변서에 적는다.
- 줄간격, 글꼴, 공백 같은 서식만 고친 run에는 새 하이라이트를 넣지 않는다.
- tex에는 바뀐 곳 바로 위에 `% R2-12: 이유` 형식의 주석을 단다.
