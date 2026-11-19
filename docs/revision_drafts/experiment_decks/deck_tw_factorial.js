// Deck 1: arrival-spread (rho) x due-date slack (delta) factorial experiment (R1-13, R2-11).
// Source: outputs/tw_factorial_summary.txt, outputs/tw_factorial.jsonl
const { newDeck, applyTheme, THEME } = require("./common.js");
const OUT = process.argv[2];
const D = newDeck("도착 분산·납기 여유 요인실험 결과");
const { pres, C, HEX, MX, CW, TOP, content, closing, card, text, bullets, HEAD, CELL, table, stats, source, GOOD } = D;

// ------------------------------------------------------------------ cover
pres.addSection({ title: "요인실험" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "요인실험" });
  s.addText("도착 분산·납기 여유\n요인실험 결과", { placeholder: "title" });
  s.addText("ρ 4수준 × δ 4수준 · 규모 S/M/L · 조건당 20개 인스턴스\n심사 의견 R1-13 / R2-11 · 2026-11-17", { placeholder: "body" });
  s.addText("실행 10,560회 완료", { x: MX, y: 5.7, w: 2.4, h: 0.4, fontSize: 14, bold: true, color: C.background1, fill: { color: C.accent2 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "run count" });
}

// ------------------------------------------------------------------ design
{
  const s = content("두 요인만 바꾸고 나머지는 같은 인스턴스로 고정했다", ["R1-13", "R2-11"], null, "요인실험");
  stats(s, [
    ["4 × 4", "요인 설계", "ρ ∈ {0, 0.10, 0.25, 0.50}, δ ∈ {∞, 1.00, 0.60, 0.35}", C.accent1],
    ["48", "실험 셀", "규모 S/M/L × 16조합, 셀마다 20개 인스턴스", C.accent1],
    ["10,560", "실행 횟수", "GILS 4,800 · SA-RL5 4,800 · VAA 960", C.accent2],
  ], TOP, 2.3);
  text(s, "설계 요약", MX, 4.35, CW, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "ρ는 도착이 퍼지는 폭이다. 트럭 도착 시각을 U[0, ρH]에서 뽑으며, ρ=0은 모든 트럭이 시각 0에 있는 기존 모델과 같다",
    "δ는 도착 후 납기까지의 여유다. 납기를 rq + δH로 두며, δ=∞는 납기를 끄는 수준이다",
    "심사 의견이 요청한 3×3에 각 요인의 \"꺼짐\" 수준(ρ=0, δ=∞)을 더해 4×4로 확장했다",
    "같은 인스턴스에서 두 요인만 바꾸므로 화물·도어·처리시간은 모든 셀에서 동일하다",
  ], MX, 4.8, CW, 2.0);
  source(s, "outputs/tw_factorial_summary.txt · experiments/tw_factorial.py");
  s.addNotes("H는 시간 제약이 없을 때의 총 작업완료시간 추정치이며 H = 2ΣHi/|M| 이다.");
}

// ------------------------------------------------------------------ main effects
{
  const s = content("두 요인은 문제를 서로 다른 방향으로 어렵게 만든다", ["R1-13"], null, "요인실험");
  const rowsR = [[HEAD("ρ"), HEAD("Cmax/H", { align: "center" }), HEAD("납기지연/H", { align: "center" }), HEAD("VAA 대비", { align: "center" }), HEAD("SA-RL5 대비", { align: "center" })]];
  [["0.00", "1.113", "4.443", "+6.12%", "+1.73%"],
   ["0.10", "1.179", "4.614", "+5.71%", "+1.72%"],
   ["0.25", "1.304", "5.191", "+4.83%", "+1.52%"],
   ["0.50", "1.524", "6.413", "+3.67%", "+1.44%"]].forEach((r) => {
    rowsR.push([CELL(r[0], { bold: true }), CELL(r[1], { align: "center" }), CELL(r[2], { align: "center" }), CELL(r[3], { align: "center" }), CELL(r[4], { align: "center" })]);
  });
  table(s, rowsR, MX, TOP, 6.2, [0.9, 1.35, 1.45, 1.2, 1.3], { rowH: 0.46 });

  const rowsD = [[HEAD("δ"), HEAD("Cmax/H", { align: "center" }), HEAD("납기지연/H", { align: "center" }), HEAD("VAA 대비", { align: "center" }), HEAD("SA-RL5 대비", { align: "center" })]];
  [["∞", "1.277", "0.000", "+3.54%", "+1.24%"],
   ["1.00", "1.279", "1.326", "+11.62%", "+3.17%"],
   ["0.60", "1.282", "7.293", "+3.20%", "+1.20%"],
   ["0.35", "1.282", "12.043", "+1.97%", "+0.80%"]].forEach((r) => {
    rowsD.push([CELL(r[0], { bold: true }), CELL(r[1], { align: "center" }), CELL(r[2], { align: "center" }), CELL(r[3], { align: "center" }), CELL(r[4], { align: "center" })]);
  });
  table(s, rowsD, MX + 6.6, TOP, 5.5, [0.8, 1.2, 1.3, 1.05, 1.15], { rowH: 0.46 });

  text(s, "ρ: 도착이 퍼지는 폭", MX, TOP - 0.38, 3, 0.3, { fontSize: 13, bold: true, color: C.accent1 });
  text(s, "δ: 도착 후 납기까지의 여유", MX + 6.6, TOP - 0.38, 3.5, 0.3, { fontSize: 13, bold: true, color: C.accent1 });
  card(s, MX, 4.5, CW, 2.2, { name: "reading card" });
  text(s, "읽는 법", MX + 0.25, 4.65, 3, 0.35, { fontSize: 15, bold: true, color: C.text2 });
  bullets(s, [
    "ρ가 커지면 총 작업완료시간(Cmax/H)이 1.113에서 1.524로 늘어난다. 늦게 도착한 트럭이 전체 일정을 밀어낸다",
    "δ가 작아지면 Cmax/H는 1.277에서 1.282로 거의 그대로인데 납기지연은 0에서 12.043으로 커진다. 같은 일정이 벌점만 더 받는다",
    "두 요인이 서로 다른 성분을 키우므로, 4×4 설계에서만 두 효과가 분리된다",
  ], MX + 0.25, 5.05, CW - 0.5, 1.5);
  source(s, "각 값은 다른 요인과 세 규모를 모두 평균한 주효과. H로 나눈 무차원 값");
}

// ------------------------------------------------------------------ paired tests
{
  const s = content("극단 수준 사이의 차이는 모두 유의하다", ["R1-13"], null, "요인실험");
  const rows = [[HEAD("비교"), HEAD("지표"), HEAD("평균 차이", { align: "center" }), HEAD("p", { align: "center" }), HEAD("해석")]];
  [["ρ 0 → 0.50", "Cmax/H", "+0.411", "<0.0001", "도착이 퍼지면 작업완료시간이 늘어난다"],
   ["ρ 0 → 0.50", "납기지연/H", "+1.971", "<0.0001", "늦은 도착이 납기지연으로 이어진다"],
   ["ρ 0 → 0.50", "SA-RL5 대비", "−0.296", "0.0006", "두 방법의 격차는 줄지만 우위는 유지된다"],
   ["δ ∞ → 0.35", "Cmax/H", "+0.005", "<0.0001", "일정 길이는 사실상 그대로다"],
   ["δ ∞ → 0.35", "납기지연/H", "+12.043", "<0.0001", "여유가 줄면 납기지연만 커진다"],
   ["δ ∞ → 0.35", "SA-RL5 대비", "−0.439", "<0.0001", "납기가 빠듯할수록 격차가 줄어든다"]].forEach((r, i) => {
    const em = i === 3 || i === 4 ? { bold: true } : {};
    rows.push([CELL(r[0], Object.assign({ bold: true }, em)), CELL(r[1]), CELL(r[2], Object.assign({ align: "center" }, em)), CELL(r[3], { align: "center" }), CELL(r[4])]);
  });
  table(s, rows, MX, TOP, CW, [1.75, 1.8, 1.4, 1.2, 5.98], { rowH: 0.5 });
  text(s, "짝지은 비교: 인스턴스별로 다른 요인을 평균한 뒤 양측 Wilcoxon, 60쌍", MX, 5.45, CW, 0.3, { fontSize: 12, color: C.accent5 });
  card(s, MX, 5.78, CW, 0.92, { name: "note card" });
  text(s, "δ를 줄이면 작업완료시간은 그대로이고 납기지연만 12배로 커진다. 두 요인을 한 축으로 묶을 수 없다는 근거이다.",
    MX + 0.25, 5.95, CW - 0.5, 0.6, { fontSize: 15, bold: true, color: C.text2 });
  source(s, "outputs/tw_factorial_summary.txt의 Paired tests 절");
}

// ------------------------------------------------------------------ size view
{
  const s = content("가장 쉬운 셀과 가장 어려운 셀에서 모두 우위가 유지된다", ["R1-13", "R2-11"], null, "요인실험");
  const rows = [[HEAD("규모"), HEAD("셀"), HEAD("목적값", { align: "right" }), HEAD("납기지연 비중", { align: "center" }), HEAD("VAA 대비", { align: "center" }), HEAD("SA-RL5 대비", { align: "center" })]];
  [["S", "ρ=0, δ=∞", "1,397", "0.0%", "+6.82%", "+0.77%"],
   ["S", "ρ=0.50, δ=0.35", "9,617", "79.8%", "+2.45%", "+0.48%"],
   ["M", "ρ=0, δ=∞", "2,917", "0.0%", "+3.46%", "+1.54%"],
   ["M", "ρ=0.50, δ=0.35", "37,334", "89.4%", "+1.02%", "+0.75%"],
   ["L", "ρ=0, δ=∞", "5,434", "0.0%", "+1.99%", "+1.69%"],
   ["L", "ρ=0.50, δ=0.35", "116,694", "93.6%", "+0.53%", "+0.53%"]].forEach((r, i) => {
    const o = i % 2 === 1 ? { fill: { color: HEX.lt2 } } : {};
    rows.push([CELL(r[0], Object.assign({ bold: true }, o)), CELL(r[1], o), CELL(r[2], Object.assign({ align: "right" }, o)),
               CELL(r[3], Object.assign({ align: "center" }, o)), CELL(r[4], Object.assign({ align: "center" }, o)), CELL(r[5], Object.assign({ align: "center" }, o))]);
  });
  table(s, rows, MX, TOP, 7.45, [0.65, 1.75, 1.2, 1.4, 1.0, 1.45], { rowH: 0.47 });
  card(s, 8.5, TOP, 4.23, 3.4, { name: "summary card" });
  text(s, "48개 셀 전체", 8.75, TOP + 0.2, 3.7, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  text(s, "956 / 960", 8.75, TOP + 0.65, 3.7, 0.7, { fontSize: 36, bold: true, color: HEX.accent2 });
  text(s, "GILS가 SA-RL5보다 좋았던 인스턴스 (99.6%)", 8.75, TOP + 1.4, 3.7, 0.5, { fontSize: 13, color: C.accent5 });
  bullets(s, [
    "48개 셀 가운데 44개에서 20/20 승리",
    "SA-RL5 대비 평균 +1.60%, 최소 +0.48%",
    "모든 셀에서 p < 0.0001",
  ], 8.75, TOP + 2.0, 3.7, 1.2, { fontSize: 13 });
  text(s, "납기지연 비중이 커질수록 두 방법의 격차는 줄지만 부호는 바뀌지 않는다", MX, 5.4, 7.6, 0.6, { fontSize: 14, color: C.text1 });
  source(s, "목적값은 조건당 20개 인스턴스 × 5회 반복의 평균");
}

// ------------------------------------------------------------------ closing
{
  const s = closing("본문에는 주효과와 극단 비교만 넣고 48개 셀은 부록으로 돌린다", "요인실험");
  card(s, MX, TOP, CW, 2.2, { fill: "16304E", line: "16304E", name: "takeaway" });
  text(s, "확인된 것", MX + 0.3, TOP + 0.2, 4, 0.35, { fontSize: 16, bold: true, color: HEX.accent6 });
  bullets(s, [
    "ρ와 δ는 각각 작업완료시간과 납기지연을 따로 키운다. 한 축으로 묶을 수 없다",
    "두 요인을 가장 세게 준 셀에서도 GILS가 SA-RL5보다 좋다 (S +0.48%, M +0.75%, L +0.53%)",
    "ρ=0, δ=∞ 셀의 결과는 기존 none 조건과 같은 설정이므로 본문 Table 4와 연결된다",
  ], MX + 0.3, TOP + 0.65, CW - 0.6, 1.4, { color: "FFFFFF" });
  text(s, "다음 작업", MX, 4.35, CW, 0.35, { fontSize: 16, bold: true, color: HEX.accent6 });
  bullets(s, [
    "본문 5장에 주효과 표(8행)와 극단 수준 짝 비교 표(6행)를 추가한다",
    "48개 셀 전체 표와 규모별 상세는 부록으로 보낸다",
    "4.2절의 시간 제약 수준 설명에 ρ=0, δ=∞ 수준의 정의를 추가한다",
  ], MX, 4.8, CW, 1.6, { color: "FFFFFF" });
  s.addNotes("심사 의견 R1-13은 도착 분산과 납기 여유를 분리한 실험을 요청했고, R2-11은 결과 보고 범위를 지적했다.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
