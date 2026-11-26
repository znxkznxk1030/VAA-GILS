# R1-7, R2-4: Table 1의 열 폭과 약어 정의

- 작성일: 2026-11-22
- 기준 원고: `paper/jkiie_submit_body.tex` 119–140행, `paper/jkiie_submit_body.docx`의 Table 1 (커밋 `11b2764`)
- 두 지적 모두 1장 Table 1(관련 연구와의 비교표)에 관한 것이라 함께 처리한다.
- 내용(연구 목록, 셀의 값)은 바꾸지 않는다. 표 번호도 그대로다.
- **상태 (2026-11-25)**: 반영 완료. 7절의 권고 세 가지를 모두 따랐다. 다만 Word 열 폭은 4.1절 표 대신 1,600/1,850/1,150/1,500/1,700/1,560으로 정했다. "Inbound/outbound;"(1,602 dxa)가 Truck roles 열 한 줄에 들어가도록 이 열을 넓혔다. 빗금 뒤에는 폭 없는 공백(U+200B, tex는 `\slash`)을 넣어 Word에서도 빗금 뒤에서만 줄이 바뀌게 했다(6절 확인 1). 같은 점검에서 Table 2와 Table A1의 끊김도 발견해 함께 고쳤다(답변서 R1-7).

## 1. 심사 의견

> **R1-7** (투고본 6쪽 11행): unloadi ng 등 표에서 단어가 두 줄로 넘어가는 현상 방지를 위해 열 폭 조정 권장

> **R2-4**: Page 6, Table 1에서 일부 약어가 별도의 정의 없이 사용되고 있습니다. 표의 각주 등을 활용하여 사용된 약어를 정의하면 독자가 관련 연구의 특징을 보다 쉽게 이해할 수 있을 것으로 생각합니다.

## 2. 요약

- **R1-7**: "Partial unloading" 열이 좁아 "unloading"이 한 줄에 들어가지 않는다. 이 열을 넓히고 남는 폭을 다른 열에서 조정한다. Word에서는 표 전체 폭을 본문 폭에 맞춘다.
- **R2-4**: 표 아래에 약어 주석(Note) 한 줄을 넣어 표에 나오는 약어 13개를 모두 정의한다.

## 3. 현재 상태 진단

### 3.1 단어가 끊기는 원인 (R1-7)

**Word** (표 글꼴은 맑은 고딕 9pt, 셀 좌우 여백 각 108 dxa)

| 열 | 현재 폭 (dxa) | 글자가 들어갈 폭 | 가장 긴 단어 | 필요한 폭 | 판정 |
|---|---|---|---|---|---|
| Study | 1,750 | 1,534 | Shahmardan | 1,021 | 충분 |
| Truck roles | 1,600 | 1,384 | Compound; (빗금에서 줄바꿈될 때) | 952 | 충분 (6절 확인 1) |
| **Partial unloading** | **900** | **684** | **unloading)** | **873** | **부족: 지적된 현상의 원인** |
| Temporal constraints | 1,550 | 1,334 | constraints | 882 | 충분 |
| Objective | 1,750 | 1,534 | λ×tardiness | 946 | 충분 |
| Solution method | 1,300 | 1,084 | Evolutionary | 1,001 | 여유 적음 |

- 필요한 폭은 맑은 고딕 글꼴 파일로 글자 폭을 직접 측정한 값이다.
- 표 전체 폭은 8,850 dxa이고 본문 폭은 9,360 dxa(용지 12,240 − 좌우 여백 2,880)다. 510 dxa가 남아 있다.
- LibreOffice 렌더링에서도 "unloadin g", "No (full unloadin g)"처럼 끊긴다. 심사위원이 본 현상과 같다.

**PDF (tex)**

- 같은 열이 `p{0.08\textwidth}`라서 "unload-ing"처럼 하이픈으로 나뉜다.
- 표 전체 폭이 본문 폭보다 좁다(열 폭 합 0.81\textwidth).

### 3.2 정의 없이 쓰인 약어 (R2-4)

표에 나오는 약어와 본문에서의 정의 여부:

| 약어 | 쓰인 행 | 정의 (영문) | 본문 정의 |
|---|---|---|---|
| AGV | Li et al. (2026) | automated guided vehicle | 없음 |
| ALNS | Bodnar, Rijal, Li | adaptive large neighborhood search | 1장에 있음 (표 밖) |
| CP-SAT | This study | constraint programming–satisfiability (Google OR-Tools solver) | 1장에 있음 |
| DE | Assadi and Bagheri | differential evolution | 없음 |
| GA | Nowak and Puladi | genetic algorithm | 없음 |
| MILP | Assadi and Bagheri, This study | mixed-integer linear programming | 1장에 있음 |
| MIP | Ozden and Saricicek, Abtahi | mixed-integer programming | 없음 |
| PBSA | Assadi and Bagheri | population-based simulated annealing | 없음 |
| RL | Shahmardan and Sajadieh | reinforcement learning | 없음 (본문은 "RL" 그대로 사용) |
| SA | Ozden, Abtahi, Shahmardan | simulated annealing | 3장에 영문으로만 |
| TS | Ozden and Saricicek | tabu search | 없음 |
| VNS | Nowak and Puladi | variable neighborhood search | 없음 |
| VAA-GILS | This study | Vogel approximation algorithm–based guided iterated local search (proposed) | 3장에 있음 |

- 정의는 참고문헌 제목과 맞는지 확인했다. Assadi and Bagheri(2016)의 제목이 "Differential Evolution and Population-Based Simulated Annealing …"이고, Van Belle 등(2013)의 제목이 "A Tabu Search Approach …"이다.
- 표 밖에서 정의된 약어도 표만 보고 읽을 수 있도록 주석에 모두 넣는다.

## 4. 수정안

### 4.1 열 폭 (R1-7)

**Word**: 표 폭을 본문 폭 9,360 dxa로 넓히고 다음과 같이 나눈다. `tblW`, `tblGrid`, 모든 행의 `tcW`를 함께 바꾼다.

| 열 | 현재 | 수정 | 글자가 들어갈 폭 | 가장 긴 단어 대비 |
|---|---|---|---|---|
| Study | 1,750 | 1,650 | 1,434 | +413 |
| Truck roles | 1,600 | 1,700 | 1,484 | +532 |
| **Partial unloading** | **900** | **1,150** | **934** | **+61** |
| Temporal constraints | 1,550 | 1,550 | 1,334 | +452 |
| Objective | 1,750 | 1,700 | 1,484 | +538 |
| Solution method | 1,300 | 1,610 | 1,394 | +393 |
| 합 | 8,850 | 9,360 | | |

본문 폭을 넘기지 않으려면 표 폭을 8,850으로 두고 Study를 1,600, Objective를 1,650으로 줄여 Partial unloading을 1,150으로 만들어도 된다. 여유는 위 안보다 적다.

**tex**: 열 폭을 다시 나눈다. 예: `p{0.15}`, `p{0.17}`, `p{0.10}`, `p{0.14}`, `p{0.15}`, `p{0.13}` (\textwidth 기준). 컴파일 후 "unloading"이 끊기지 않는지 확인한다.

### 4.2 약어 주석 (R2-4)

표 바로 아래에 영문 주석 한 단락을 둔다. 표가 영문이므로 주석도 영문으로 쓴다. 캡션이 이미 길어서 캡션에는 넣지 않는다.

> *Note.* AGV, automated guided vehicle; ALNS, adaptive large neighborhood search; CP-SAT, constraint programming–satisfiability solver of Google OR-Tools; DE, differential evolution; GA, genetic algorithm; MILP, mixed-integer linear programming; MIP, mixed-integer programming; PBSA, population-based simulated annealing; RL, reinforcement learning; SA, simulated annealing; TS, tabu search; VAA-GILS, Vogel approximation algorithm–based guided iterated local search (proposed); VNS, variable neighborhood search.

- 순서는 알파벳순이다.
- 글자 크기는 표 본문보다 작게(8pt) 하고 왼쪽 정렬한다.
- tex에서는 `tabular` 뒤, `table` 환경 안에 `\par\smallskip{\scriptsize\raggedright ...}` 형태로 넣는다.

**함께 정리할 표기 (선택)**: Van Belle 등(2013) 행은 "Tabu search"로 풀어 쓰고 Ozden and Saricicek 행은 "TS"로 줄여 써서 표기가 섞여 있다. 주석에 TS를 정의하므로 Van Belle 행도 "TS"로 맞추는 것을 권한다. 내용은 같다.

## 5. Word 작업

- 표의 열 폭은 `w:tblGrid`의 `gridCol` 6개와 12개 행의 `w:tcW`를 같은 값으로 바꾼다. 레이아웃이 고정(`tblLayout fixed`)이라 값대로 적용된다.
- 주석 단락은 표 바로 뒤에 새 단락으로 넣고 노란색으로 표시한다.
- 열 폭만 바뀐 부분은 글자 하이라이트로 표시할 수 없다. 답변서에 "열 폭 조정"으로 밝힌다.
- Van Belle 행의 "TS" 변경을 하면 그 글자만 노란색으로 표시한다.
- 확인 방법: LibreOffice로 렌더링해 "unloading"이 끊기지 않는지 본다. 한글 글꼴이 없어 Latin 글꼴로 대체되므로, 가능하면 Word에서도 직접 연다.

## 6. 반영 전에 확인할 것

| 번호 | 항목 | 내용 |
|---|---|---|
| 1 | 빗금(/)에서의 줄바꿈 | "Inbound/outbound/compound;"는 빗금에서 줄이 바뀌어야 Truck roles 열에 들어간다. LibreOffice와 LaTeX는 빗금에서 줄을 바꾼다. Word에서 빗금 뒤 줄바꿈이 되지 않아 글자가 끊기면 "Inbound, outbound, compound;"처럼 쉼표로 바꾼다. |
| 2 | Solution method 열 | 현재 "Evolutionary"의 여유가 83 dxa뿐이다. 수정안(1,610)에서는 여유가 충분하다. |
| 3 | 표의 쪽 위치 | 표 폭이 넓어지면 행 높이가 줄어 표가 짧아진다. 쪽 나눔이 바뀌는지 렌더링으로 확인한다. |

## 7. 정할 것

| 번호 | 항목 | 권고 |
|---|---|---|
| 1 | Word 표 폭 | 본문 폭 9,360으로 확대 (4.1절 표) |
| 2 | 약어 주석 위치 | 표 아래 Note 단락 (캡션에 넣지 않음) |
| 3 | Van Belle 행 "Tabu search" → "TS" | 맞춤 (선택) |

## 8. 답변서 문안 초안

> **R1-7**
> 지적에 감사드립니다. Table 1에서 "Partial unloading" 열의 폭이 좁아 단어가 두 줄로 나뉘던 문제를 열 폭을 조정하여 해결하였습니다. 표 전체 폭을 본문 폭에 맞추고 다른 열의 폭도 다시 배분하여, 모든 열에서 단어가 중간에 끊기지 않도록 하였습니다. (수정본 Table 1)

> **R2-4**
> 지적에 감사드립니다. Table 1 아래에 주석을 추가하여 표에 사용된 약어(AGV, ALNS, CP-SAT, DE, GA, MILP, MIP, PBSA, RL, SA, TS, VAA-GILS, VNS)를 모두 정의하였습니다. 본문에서 이미 정의한 약어도 표만 보고 이해할 수 있도록 주석에 함께 포함하였습니다. (수정본 Table 1)
