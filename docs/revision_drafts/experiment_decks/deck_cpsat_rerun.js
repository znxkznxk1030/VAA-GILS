// Deck 2: CP-SAT rerun on the M and L conditions (R1-1, R1-18, R2-11, R2-14).
// Source: outputs/cpsat_rerun.jsonl, docs/revision_drafts/R1-1_R1-18_R2-11_R2-14_cpsat_m_correction.md
const { newDeck, applyTheme, THEME } = require("./common.js");
const OUT = process.argv[2];
const D = newDeck("CP-SAT 재실행 결과");
const { pres, C, HEX, MX, CW, TOP, content, closing, card, text, bullets, HEAD, CELL, table, stats, source, GOOD, WARN } = D;

// ------------------------------------------------------------------ cover
pres.addSection({ title: "CP-SAT 재실행" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "CP-SAT 재실행" });
  s.addText("CP-SAT 재실행 결과", { placeholder: "title" });
  s.addText("중형·대형 조건 12건 · 600초 순차 실행 · 8스레드\n심사 의견 R1-1 / R1-18 / R2-11 / R2-14 · 2026-11-17", { placeholder: "body" });
  s.addText("본문 정정 필요", { x: MX, y: 5.7, w: 2.2, h: 0.4, fontSize: 14, bold: true, color: C.background1, fill: { color: C.accent3 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "status tag" });
}

// ------------------------------------------------------------------ why + headline
{
  const s = content("중형 조건에서는 CP-SAT가 실행 가능해를 찾는다", ["R1-1"], null, "CP-SAT 재실행");
  stats(s, [
    ["12 / 12", "재실행 기록이 모두 유효", "계산 시간과 경과 시간이 일치 (11월 13일, 15일)", C.accent1],
    ["6 / 6", "M: 실행 가능해 반환", "최적성은 한 건도 증명되지 않음", HEX.accent2],
    ["0 / 6", "L: 실행 가능해 없음", "제약 약 697만 개, 전처리에서 시간 소진", HEX.accent3],
  ], TOP, 2.3);
  text(s, "무엇이 잘못되어 있었나", MX, 4.35, CW, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "제출본 5.1절: \"M의 시간 제약 조건과 L의 모든 조건에서 CP-SAT가 제한시간 안에 실행 가능해를 반환하지 못했다\"",
    "7월 기록은 실행 중 장비가 절전으로 들어가 실제 계산 시간이 21~355초였다. 솔버의 제한시간은 경과 시간 기준이라 그대로 종료되었다",
    "600초를 온전히 준 재실행에서 M은 여섯 건 모두 기준해를 반환했고, L은 여섯 건 모두 반환하지 못했다",
    "재실행은 한 건씩 순차로 수행하고 로그로 계산 시간을 확인했다",
  ], MX, 4.8, CW, 2.0);
  source(s, "outputs/cpsat_rerun.jsonl · experiments/cpsat_rerun.py · outputs/logs/cpsat_rerun_*.log");
}

// ------------------------------------------------------------------ rerun table
{
  const s = content("중형 6건은 모두 기준해를 반환했고 균등 선택 GILS가 더 좋았다", ["R1-1", "R2-11"], null, "CP-SAT 재실행");
  const rows = [[HEAD("조건"), HEAD("CP-SAT 기준해", { align: "right" }), HEAD("하한", { align: "right" }), HEAD("계산 시간", { align: "center" }), HEAD("GILS-uniform", { align: "right" }), HEAD("기준해 대비", { align: "center" })]];
  [["M-none 0", "2,133.6", "1,512.9", "603초", "2,136.5", "+0.14%", null],
   ["M-none 1", "2,578.6", "1,892.2", "603초", "2,586.9", "+0.32%", null],
   ["M-medium 0", "19,969.3", "12,706.9", "603초", "19,908.5", "−0.30%", GOOD],
   ["M-medium 1", "15,574.6", "8,957.9", "603초", "15,541.9", "−0.21%", GOOD],
   ["M-tight 0", "27,945.0", "17,051.5", "603초", "27,878.9", "−0.24%", GOOD],
   ["M-tight 1", "25,986.2", "15,834.1", "605초", "25,985.7", "−0.00%", GOOD]].forEach((r) => {
    rows.push([CELL(r[0], { bold: true }), CELL(r[1], { align: "right" }), CELL(r[2], { align: "right" }),
               CELL(r[3], { align: "center" }), CELL(r[4], { align: "right" }), CELL(r[5], Object.assign({ align: "center" }, r[6] || {}))]);
  });
  rows.push([CELL("L 6건", { bold: true }), CELL("해 없음", { align: "right", color: HEX.accent3 }), CELL("—", { align: "right" }),
             CELL("570~602초", { align: "center" }), CELL("—", { align: "right" }), CELL("—", { align: "center" })]);
  table(s, rows, MX, TOP, CW, [1.9, 2.2, 1.9, 1.6, 2.3, 2.23], { rowH: 0.45 });
  card(s, MX, 5.5, CW, 1.2, { name: "note card" });
  bullets(s, [
    "음수는 GILS의 목적값이 CP-SAT 기준해보다 낮다는 뜻이다. 600초 기준해를 0.5초 안에 따라잡거나 넘어섰다",
    "M은 한 건도 최적성이 증명되지 않았다. 기준해와 하한의 차이가 크다 (M-medium 0: 19,969 대 12,707)",
    "L은 여섯 건 모두 전처리에서 제한시간을 다 써 분기를 한 번도 시작하지 못했다",
  ], MX + 0.25, 5.65, CW - 0.5, 1.0, { fontSize: 13 });
  source(s, "GILS-uniform은 인스턴스당 5회 반복의 평균. 조건당 인스턴스는 2개");
}

// ------------------------------------------------------------------ Table 4 values
{
  const s = content("Table 4의 vs CP-SAT 열에 M 세 조건 값이 들어간다", ["R1-18", "R2-11"], null, "CP-SAT 재실행");
  const rows = [[HEAD("방법"), HEAD("M-medium", { align: "center" }), HEAD("M-tight", { align: "center" }), HEAD("M-none (제출본)", { align: "center" }), HEAD("M-none (재실행, 사용)", { align: "center" })]];
  [["VAA", "+3.28", "+1.03", "+4.80", "+4.94"],
   ["Paper-SA-RL5", "—", "—", "+1.55", "+1.68"],
   ["Extended SA-RL5", "+1.65", "+0.84", "—", "—"],
   ["GILS (tabular)", "−0.29", "+0.07", "+0.08", "+0.21"],
   ["GILS-uniform", "−0.26", "−0.12", "+0.10", "+0.23"],
   ["GILS-dqn", "−0.19", "+0.05", "+0.12", "+0.26"]].forEach((r, i) => {
    const em = r[0] === "GILS-uniform" ? { bold: true, fill: { color: HEX.lt2 } } : {};
    rows.push([CELL(r[0], Object.assign({ bold: true }, em)), CELL(r[1], Object.assign({ align: "center" }, em)),
               CELL(r[2], Object.assign({ align: "center" }, em)), CELL(r[3], Object.assign({ align: "center" }, em)),
               CELL(r[4], Object.assign({ align: "center" }, em))]);
  });
  table(s, rows, MX, TOP, 8.2, [2.1, 1.5, 1.5, 1.6, 1.5], { rowH: 0.47 });
  card(s, 9.1, TOP, 3.63, 3.3, { name: "delta card" });
  text(s, "Δbo는 바뀌지 않는다", 9.35, TOP + 0.2, 3.2, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "관측 최선해는 CP-SAT 결과를 포함하지만, M 여섯 인스턴스 모두 휴리스틱의 최선값이 새 기준해보다 낮거나 같다",
    "예: M-medium 0은 19,850.6 대 19,969.3",
    "Table 4의 Δbo 열과 Table 5~8은 재계산이 필요 없다",
  ], 9.35, TOP + 0.65, 3.2, 2.4, { fontSize: 13 });
  text(s, "M-tight에서는 균등 선택만 기준해보다 좋다 (−0.12). tabular와 DQN은 조금 나쁘므로, 본문의 서술은 \"기본 선택 정책인 균등 선택 기준\"으로 한정한다.",
    MX, 5.25, 8.2, 0.9, { fontSize: 13.5, color: C.text1 });
  source(s, "인스턴스 2개에서 방법별 반복 평균과 재실행 기준해의 상대 차이(%)를 평균한 값");
}

// ------------------------------------------------------------------ wording changes
{
  const s = content("정정은 네 곳이고 초록 숫자는 0.11~0.23%로 바뀐다", ["R1-1", "R1-18", "R2-14"], "정정", "CP-SAT 재실행");
  const rows = [[HEAD("위치"), HEAD("제출본"), HEAD("수정안")]];
  [["영문·국문 초록", "… while CP-SAT fails within 600 s", "… on large instances, for which CP-SAT returns no feasible solution within 600 s"],
   ["5.1절", "M의 시간 제약 조건과 L의 모든 조건에서 실행 가능해를 반환하지 못했다", "M은 반환했으나 최적성 미증명, 균등 선택 GILS가 평균 0.12~0.26% 낮음. L은 반환하지 못했다"],
   ["Table 4 · 캡션", "M-medium, M-tight의 vs CP-SAT 열이 \"---\", 평균 606초", "값을 채우고 평균 603초로 수정, 음수의 뜻을 캡션에 명시"],
   ["초록 · 5.1절 · 7장", "기준해 대비 평균 0.10~0.23%", "0.11~0.23% (M-none을 더 좋은 재실행 기준해로 통일)"]].forEach((r) => {
    rows.push([CELL(r[0], { bold: true }), CELL(r[1]), CELL(r[2])]);
  });
  table(s, rows, MX, TOP, CW, [2.1, 4.8, 5.23], { rowH: 0.66 });
  card(s, MX, 5.2, 5.9, 1.5, { name: "changed card" });
  text(s, "바뀌는 값", MX + 0.25, 5.35, 3, 0.3, { fontSize: 14, bold: true, color: HEX.accent3 });
  bullets(s, [
    "균등 선택 0.10~0.23% → 0.11~0.23%",
    "전체 변형 0.08~0.48% → 0.11~0.48%",
    "M-none CP-SAT 계산 시간 606초 → 603초",
  ], MX + 0.25, 5.7, 5.4, 0.9, { fontSize: 13 });
  card(s, 6.75, 5.2, 5.98, 1.5, { name: "kept card" });
  text(s, "바뀌지 않는 값", 7.0, 5.35, 3, 0.3, { fontSize: 14, bold: true, color: HEX.accent2 });
  bullets(s, [
    "최적해 대비 0.23% (S-none 20개)",
    "S 세 조건 값과 Δbo 전체",
    "L에서 실행 가능해를 반환하지 못했다는 결론",
  ], 7.0, 5.7, 5.5, 0.9, { fontSize: 13 });
  source(s, "검산 완료: 균등 선택 0.114~0.230, 전체 변형 0.114~0.483");
}

// ------------------------------------------------------------------ closing
{
  const s = closing("대형 조건에 대한 결론은 그대로이고, 중형 서술만 정정한다", "CP-SAT 재실행");
  card(s, MX, TOP, CW, 2.1, { fill: "16304E", line: "16304E", name: "takeaway" });
  text(s, "보고할 내용", MX + 0.3, TOP + 0.2, 4, 0.35, { fontSize: 16, bold: true, color: HEX.accent6 });
  bullets(s, [
    "심사위원이 지적하지 않은 오류이므로 답변서의 \"저자 자체 수정 사항\"에 밝힌다",
    "M 시간 제약 조건에서 600초 CP-SAT 기준해를 0.5초 안에 따라잡은 결과는 R2-11(성능 차이의 의미)의 근거로 쓴다",
    "L의 실패 원인이 탐색의 어려움이 아니라 모형 크기(약 697만 제약)라는 점을 7장 한계에 추가한다 (R2-14)",
  ], MX + 0.3, TOP + 0.65, CW - 0.6, 1.3, { color: "FFFFFF" });
  text(s, "남은 일", MX, 4.25, CW, 0.35, { fontSize: 16, bold: true, color: HEX.accent6 });
  bullets(s, [
    "원고 반영: 초록(영문·국문), 5.1절, Table 4와 캡션, 4.3절, 7장",
    "국문 초록의 해당 문장을 원고에서 확인해 문안 확정",
    "반영 후 답변서에 쪽·행 번호 기입",
  ], MX, 4.7, CW, 1.4, { color: "FFFFFF" });
  s.addNotes("재실행 기록은 outputs/cpsat_rerun.jsonl, 문안 초안은 docs/revision_drafts/R1-1_R1-18_R2-11_R2-14_cpsat_m_correction.md에 있다.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
