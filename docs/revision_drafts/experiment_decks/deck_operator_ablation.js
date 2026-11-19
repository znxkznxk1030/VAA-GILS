// Deck 3: per-operator ablation of the bottleneck-guided operators (R1-16).
// Source: outputs/b1_individual_summary.txt, outputs/b1_individual.jsonl
const { newDeck, applyTheme, THEME } = require("./common.js");
const OUT = process.argv[2];
const D = newDeck("연산자별 개별 ablation 결과");
const { pres, C, HEX, MX, CW, TOP, content, closing, card, text, bullets, HEAD, CELL, table, stats, source, GOOD, WARN } = D;

const MUTED = { color: HEX.accent5 };

// ------------------------------------------------------------------ cover
pres.addSection({ title: "개별 ablation" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "개별 ablation" });
  s.addText("병목 유도 연산자별\n개별 ablation 결과", { placeholder: "title" });
  s.addText("g1~g4를 하나씩 더하고 빼는 두 방향 비교 · 11개 연산자 집합\n심사 의견 R1-16 · 2026-11-17", { placeholder: "body" });
  s.addText("실행 2,475회 완료", { x: MX, y: 5.7, w: 2.3, h: 0.4, fontSize: 14, bold: true, color: C.background1, fill: { color: C.accent2 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "run count" });
}

// ------------------------------------------------------------------ design
{
  const s = content("두 개씩 묶었던 비교를 연산자 하나 단위로 나눴다", ["R1-16"], null, "개별 ablation");
  const rows = [[HEAD("방향"), HEAD("집합"), HEAD("비교 대상"), HEAD("알 수 있는 것")]];
  [["A. 하나씩 더하기", "generic + gN (8종)", "generic (7종)", "그 연산자가 단독으로 내는 효과"],
   ["B. 하나씩 빼기", "full − gN (10종)", "full (11종)", "다른 유도 연산자가 있을 때의 추가 효과"]].forEach((r) => {
    rows.push([CELL(r[0], { bold: true }), CELL(r[1]), CELL(r[2]), CELL(r[3])]);
  });
  table(s, rows, MX, TOP, CW, [2.4, 2.8, 2.2, 4.73], { rowH: 0.55 });
  text(s, "기존 Table 6은 generic → critical(+g1, g2) → full(+g3, g4)로 두 개씩 묶어 비교했다. 어느 연산자가 효과를 내는지는 그 설계로 알 수 없다.",
    MX, TOP + 1.85, CW, 0.5, { fontSize: 14, color: C.text1 });
  stats(s, [
    ["11", "연산자 집합", "generic · critical · full · add-gN · drop-gN", C.accent1],
    ["2,475", "실행 횟수", "집합마다 9개 조건 × 5개 인스턴스 × 5회 = 225회", C.accent1],
    ["Holm", "다중비교 보정", "한 범위 안의 8개 비교에 Holm 보정을 적용", HEX.accent2],
  ], 4.25, 2.3);
  text(s, "고정: 균등 선택, 최종 엔진(탐욕적 수락·하강 탐색·섭동 재시작), 반복 1,000회 — Table 6과 같은 설정", MX, 6.75, CW, 0.3, { fontSize: 12, color: C.accent5 });
  source(s, "outputs/b1_individual_summary.txt · experiments/b1_individual.py");
}

// ------------------------------------------------------------------ overall result
{
  const s = content("g1, g2, g4는 두 방향 모두에서 유의하고 g3만 다르다", ["R1-16"], null, "개별 ablation");
  const rows = [[HEAD("연산자"), HEAD("단독 추가(%)", { align: "center" }), HEAD("Holm p", { align: "center" }), HEAD("더 좋음/나쁨", { align: "center" }),
                 HEAD("전체 집합 내 추가(%)", { align: "center" }), HEAD("Holm p", { align: "center" }), HEAD("더 좋음/나쁨", { align: "center" })]];
  [["g1 병목 도어 출고트럭 재배치", "+0.043", "0.0001", "35 / 6", "+0.039", "0.0001", "38 / 7", null],
   ["g2 병목 트럭 목적지 교환", "+0.099", "0.0000", "39 / 5", "+0.050", "0.0003", "34 / 11", null],
   ["g3 납기지연 트럭 재배치", "+0.017", "0.0095", "30 / 9", "+0.018", "0.1792", "28 / 17", WARN],
   ["g4 납기지연 트럭 목적지 교환", "+0.089", "0.0001", "33 / 8", "+0.042", "0.0208", "28 / 17", null]].forEach((r) => {
    const em = r[7] || {};
    rows.push([CELL(r[0], { bold: true }), CELL(r[1], { align: "center" }), CELL(r[2], { align: "center" }), CELL(r[3], Object.assign({ align: "center" }, MUTED)),
               CELL(r[4], { align: "center" }), CELL(r[5], Object.assign({ align: "center" }, em)), CELL(r[6], Object.assign({ align: "center" }, MUTED))]);
  });
  table(s, rows, MX, TOP, CW, [3.5, 1.5, 1.1, 1.3, 1.9, 1.1, 1.73], { rowH: 0.56 });
  text(s, "45쌍(9개 조건 × 5개 인스턴스) 기준, 양측 Wilcoxon에 Holm 보정", MX, TOP + 3.05, CW, 0.3, { fontSize: 12, color: C.accent5 });
  card(s, MX, 5.1, CW, 1.6, { name: "reading card" });
  text(s, "읽는 법", MX + 0.25, 5.25, 3, 0.3, { fontSize: 15, bold: true, color: C.text2 });
  bullets(s, [
    "양수는 그 연산자를 넣은 집합의 목적값이 더 낮다(좋다)는 뜻이다",
    "두 방향 모두 유의하면 다른 연산자가 대신할 수 없는 기여다 — g1, g2가 여기에 해당한다",
    "g3은 단독으로는 유의하지만(+0.017, Holm p=0.0095) 전체 집합 안에서는 유의하지 않다(Holm p=0.1792)",
  ], MX + 0.25, 5.6, CW - 0.5, 1.0, { fontSize: 13 });
  source(s, "mean% = 100 × (gN 없는 집합의 목적값 − gN 있는 집합의 목적값) / gN 있는 집합의 목적값");
}

// ------------------------------------------------------------------ scope split
{
  const s = content("시간 제약이 있는 조건에서는 g1, g2만 두 방향 모두 유의하다", ["R1-16", "R1-15"], null, "개별 ablation");
  const rows = [[HEAD("연산자"), HEAD("단독 추가(%)", { align: "center" }), HEAD("Holm p", { align: "center" }),
                 HEAD("전체 집합 내 추가(%)", { align: "center" }), HEAD("Holm p", { align: "center" })]];
  [["g1", "+0.038", "0.0062", "+0.035", "0.0015", null],
   ["g2", "+0.064", "0.0013", "+0.051", "0.0060", null],
   ["g3", "−0.002", "0.2694", "+0.015", "0.2694", WARN],
   ["g4", "+0.049", "0.0412", "+0.048", "0.2694", WARN]].forEach((r) => {
    const em = r[5] || {};
    rows.push([CELL(r[0], { bold: true }), CELL(r[1], { align: "center" }), CELL(r[2], Object.assign({ align: "center" }, r[0] === "g3" ? em : {})),
               CELL(r[3], { align: "center" }), CELL(r[4], Object.assign({ align: "center" }, em))]);
  });
  table(s, rows, MX, TOP, 6.1, [1.0, 1.5, 1.1, 1.6, 1.1], { rowH: 0.5 });
  text(s, "시간 제약 조건 30쌍", MX, TOP - 0.38, 4, 0.3, { fontSize: 13, bold: true, color: C.accent1 });

  const rows2 = [[HEAD("연산자"), HEAD("단독 추가(%)", { align: "center" }), HEAD("Holm p", { align: "center" }),
                  HEAD("전체 집합 내 추가(%)", { align: "center" }), HEAD("Holm p", { align: "center" })]];
  [["g1", "+0.053", "0.0293", "+0.047", "0.0603"],
   ["g2", "+0.168", "0.0024", "+0.050", "0.0905"],
   ["g3", "+0.053", "0.0293", "+0.023", "0.5245"],
   ["g4", "+0.168", "0.0024", "+0.028", "0.1665"]].forEach((r) => {
    rows2.push([CELL(r[0], { bold: true }), CELL(r[1], { align: "center" }), CELL(r[2], { align: "center" }),
                CELL(r[3], { align: "center" }), CELL(r[4], { align: "center" })]);
  });
  table(s, rows2, MX + 6.5, TOP, 5.6, [1.0, 1.4, 1.0, 1.5, 1.0], { rowH: 0.5 });
  text(s, "시간 제약 없는 조건 15쌍", MX + 6.5, TOP - 0.38, 4.5, 0.3, { fontSize: 13, bold: true, color: C.accent1 });

  card(s, MX, 4.6, CW, 2.1, { name: "fallback card" });
  text(s, "시간 제약이 없는 조건의 값을 따로 읽어야 하는 이유", MX + 0.25, 4.75, 7, 0.3, { fontSize: 15, bold: true, color: C.text2 });
  bullets(s, [
    "g3, g4는 납기지연이 가장 큰 트럭을 겨냥하는 연산자다. 납기가 없으면 겨냥할 대상이 없어 g1, g2와 같은 이동으로 대체된다",
    "실제로 시간 제약이 없는 셀에서 add-g3는 add-g1과, add-g4는 add-g2와 결과가 완전히 같았다 (75회 실행, 최대 차이 0)",
    "따라서 g3, g4의 고유한 효과는 시간 제약 조건 30쌍에서만 판단할 수 있다",
  ], MX + 0.25, 5.15, CW - 0.5, 1.4, { fontSize: 13.5 });
  source(s, "같은 범위 안의 8개 비교에 Holm 보정을 적용했다");
}

// ------------------------------------------------------------------ interpretation
{
  const s = content("연산자 수를 줄이자는 결론으로는 가지 않는다", ["R1-16", "R1-15"], "해석 확인", "개별 ablation");
  const rows = [[HEAD("연산자"), HEAD("판단"), HEAD("근거")]];
  [["g1, g2", "대체되지 않는 기여", "두 방향, 두 범위 모두에서 유의하다", HEX.accent2],
   ["g4", "단독 효과는 확인", "단독 추가는 유의하나(+0.049) 전체 집합 안에서는 미확인(Holm p=0.2694)", null],
   ["g3", "개별 효과 미확인", "시간 제약 조건에서 단독 추가 −0.002, 전체 집합 내 +0.015 모두 유의하지 않다", HEX.accent3]].forEach((r) => {
    rows.push([CELL(r[0], { bold: true, color: r[3] || HEX.dk1 }), CELL(r[1], { bold: true }), CELL(r[2])]);
  });
  table(s, rows, MX, TOP, CW, [1.6, 2.9, 7.63], { rowH: 0.55 });
  card(s, MX, 4.15, CW, 1.25, { name: "why keep" });
  text(s, "그래도 최종 엔진은 full을 유지한다", MX + 0.25, 4.3, 6, 0.35, { fontSize: 15, bold: true, color: C.text2 });
  bullets(s, [
    "Table 6의 critical → full은 +0.034%p로 유의하다(p=0.013). 묶음 단위의 이득은 남아 있다",
    "g3의 효과가 작다는 것은 시험 집합에서 확인한 사실이고, 이 결과를 보고 구성을 다시 고르면 시험 집합에 맞춘 선택이 된다",
  ], MX + 0.25, 4.68, CW - 0.5, 0.7, { fontSize: 13.5 });
  text(s, "본문 반영안", MX, 5.6, CW, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "5.2절에 연산자별 표(시간 제약 조건 30쌍)를 추가하고, 시간 제약이 없는 조건에서 g3·g4가 g1·g2로 대체되는 점을 각주로 밝힌다",
    "\"유도 연산자의 이득은 대부분 g1, g2에서 나온다\"는 기존 서술을 개별 결과로 뒷받침한다",
  ], MX, 6.0, CW, 0.85);
  source(s, "docs/revision_drafts/R1-16_individual_operator_ablation.md");
}

// ------------------------------------------------------------------ closing
{
  const s = closing("심사 의견 R1-16이 요구한 연산자별 독립 확인을 마쳤다", "개별 ablation");
  card(s, MX, TOP, CW, 2.3, { fill: "16304E", line: "16304E", name: "takeaway" });
  text(s, "확인된 것", MX + 0.3, TOP + 0.2, 4, 0.35, { fontSize: 16, bold: true, color: HEX.accent6 });
  bullets(s, [
    "g1(병목 도어 출고트럭 재배치)과 g2(병목 트럭 목적지 교환)는 넣고 빼는 두 방향 모두에서 유의하다",
    "g4는 단독 추가에서만, g3은 어느 방향에서도 고유한 효과가 확인되지 않는다",
    "시간 제약이 없는 조건에서 g3, g4는 g1, g2와 같은 이동으로 대체된다는 점을 실행 기록으로 확인했다 (최대 차이 0)",
  ], MX + 0.3, TOP + 0.65, CW - 0.6, 1.5, { color: "FFFFFF" });
  text(s, "결정이 필요한 것", MX, 4.45, CW, 0.35, { fontSize: 16, bold: true, color: HEX.accent6 });
  bullets(s, [
    "본문에 개별 ablation 표를 넣는 범위: 시간 제약 조건 30쌍만 넣을지, 세 범위를 모두 부록에 둘지",
    "g3을 최종 연산자 집합에 남기는 현재 방침을 그대로 쓸지",
  ], MX, 4.9, CW, 1.0, { color: "FFFFFF" });
  s.addNotes("심사 의견 R1-16: 병목 유도 연산자별 독립적인 성능 확인을 위해 개별 ablation 실험을 추가할 것을 권장.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
