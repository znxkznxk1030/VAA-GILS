// Advisor meeting deck: revision status of the VAA-GILS paper (JKIIE, revise and resubmit).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const SKILL = "/Users/yskim/.claude/skills/synced/43f8ff3f-425d-47cd-846e-dcd535a56441_dc04b54d-4e19-4577-9604-39fffa15168a/pptx";
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));

const REPO = "/Users/yskim/Documents/Codex/2026-06-30/files-mentioned-by-the-user-codex";
const FIG = path.join(REPO, "paper/figures");
const OUT = process.argv[2];
const S13 = fs.existsSync(path.join(__dirname, "slide13.json"))
  ? JSON.parse(fs.readFileSync(path.join(__dirname, "slide13.json"), "utf8")) : null;

const THEME = {
  name: "VAA-GILS Revision",
  headFontFace: "Apple SD Gothic Neo",
  bodyFontFace: "Apple SD Gothic Neo",
  colors: {
    dk1: "1B1F24", lt1: "FFFFFF", dk2: "1F3A5F", lt2: "F2F4F7",
    accent1: "2F5D8A", accent2: "3A9E7E", accent3: "B23A48", accent4: "7B5EA7",
    accent5: "6B7785", accent6: "C9D8EA", hlink: "2F5D8A", folHlink: "7B5EA7",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "VAA-GILS 논문 수정 후 재심 대응 현황";
pres.author = "yskim";
const C = pres.SchemeColor;
const HEX = THEME.colors;

const W = 13.33, MX = 0.6, CW = W - 2 * MX, TOP = 1.75, BOTTOM = 6.85;

pres.defineSlideMaster({
  title: "COVER",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 2.35, w: CW, h: 1.5, fontSize: 40, bold: true, color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: MX, y: 4.05, w: CW, h: 1.2, fontSize: 18, color: C.accent6, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  margin: [TOP, MX, 0.7, MX],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.72, w: CW, h: 0.85, fontSize: 30, bold: true, color: C.text2, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: HEX.accent5, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSING",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.72, w: CW, h: 0.85, fontSize: 30, bold: true, color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: HEX.accent6, align: "right" },
});

let slideNo = 0;
// Chips above the title: reviewer item IDs, and a "decision needed" tag.
function chips(slide, ids, decision) {
  let x = MX;
  if (decision) {
    slide.addText(decision, { x, y: 0.3, w: 1.55, h: 0.3, fontSize: 11, bold: true, color: C.background1, fill: { color: C.accent3 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "decision tag" });
    x += 1.67;
  }
  for (const id of ids) {
    const w = 0.34 + 0.085 * id.length;
    slide.addText(id, { x, y: 0.3, w, h: 0.3, fontSize: 11, bold: true, color: C.accent1, fill: { color: C.accent6 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `chip ${id}` });
    x += w + 0.1;
  }
}
function content(title, ids, decision, section, master) {
  const slide = pres.addSlide({ masterName: master || "CONTENT", sectionTitle: section });
  slideNo += 1;
  slide.addText(title, { placeholder: "title" });
  chips(slide, ids || [], decision);
  return slide;
}
function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: opts.fill || C.background2 }, line: { color: opts.line || C.background2, width: 0.75 }, objectName: opts.name || "card" });
}
function text(slide, t, x, y, w, h, o = {}) {
  slide.addText(t, Object.assign({ x, y, w, h, fontSize: 14, color: C.text1, align: "left", valign: "top", margin: 0, isTextBox: true }, o));
}
function bullets(slide, items, x, y, w, h, o = {}) {
  const runs = items.map((it, i) => ({ text: it, options: { bullet: true, breakLine: i < items.length - 1 } }));
  slide.addText(runs, Object.assign({ x, y, w, h, fontSize: 14, color: C.text1, align: "left", valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true }, o));
}
const HEAD = (t, extra = {}) => ({ text: t, options: Object.assign({ bold: true, color: "FFFFFF", fill: { color: HEX.accent1 }, fontSize: 13, valign: "middle" }, extra) });
const CELL = (t, extra = {}) => ({ text: t, options: Object.assign({ fontSize: 13, color: HEX.dk1, valign: "middle" }, extra) });
function table(slide, rows, x, y, w, colW, o = {}) {
  slide.addTable(rows, Object.assign({ x, y, w, colW, border: { type: "solid", pt: 0.5, color: "C8CED6" }, margin: [0.06, 0.1, 0.06, 0.1], fontFace: THEME.bodyFontFace, autoPage: false }, o));
}
const GOOD = { color: HEX.accent2, bold: true };
const WARN = { color: HEX.accent3, bold: true };

// ------------------------------------------------------------------ 1. cover
pres.addSection({ title: "개요" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "개요" });
  slideNo += 1;
  s.addText("VAA-GILS 논문\n수정 후 재심 대응 현황", { placeholder: "title" });
  s.addText("대한산업공학회지 · 심사 의견 32건 · 지도교수 면담 자료\n2026-11-17", { placeholder: "body" });
  s.addText("결정이 필요한 사항 4건", { x: MX, y: 5.7, w: 2.6, h: 0.4, fontSize: 14, bold: true, color: C.background1, fill: { color: C.accent3 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "decision count" });
}

// ------------------------------------------------------------------ 2. overview
{
  const s = content("심사 의견 32건 가운데 15건의 초안이 준비되었다", [], null, "개요");
  const rows = [[HEAD("분류"), HEAD("건수", { align: "center" }), HEAD("초안·결과 있음", { align: "center" }), HEAD("해당 의견")]];
  const data = [
    ["정정", "5", "3", "R1-1, R1-15, R1-18 (R1-14, R1-17은 방향 확인)"],
    ["그림·의사코드", "4", "4", "R1-10, R1-11, R2-1, R2-9"],
    ["가정·정의", "5", "4", "R1-8, R1-12, R2-2, R2-3"],
    ["추가 실험", "2", "2", "R1-13, R1-16"],
    ["구성", "5", "2", "R2-11, R2-14 (일부)"],
    ["수리모형", "6", "0", "미착수"],
    ["표현", "5", "0", "미착수"],
    ["합계", "32", "15", ""],
  ];
  data.forEach((r, i) => {
    const last = i === data.length - 1;
    const o = last ? { bold: true, fill: { color: HEX.lt2 } } : {};
    rows.push([CELL(r[0], o), CELL(r[1], Object.assign({ align: "center" }, o)), CELL(r[2], Object.assign({ align: "center" }, o)), CELL(r[3], o)]);
  });
  table(s, rows, MX, TOP, 7.3, [1.6, 0.8, 1.5, 3.4], { rowH: 0.5 });
  card(s, 8.3, TOP, 4.43, 4.5, { name: "decisions card" });
  text(s, "오늘 결정이 필요한 4가지", 8.55, TOP + 0.2, 3.95, 0.4, { fontSize: 16, bold: true, color: C.accent3 });
  const ds = [
    ["1", "CP-SAT 서술의 자체 정정과 초록 숫자 변경"],
    ["2", "이송시간 계산이 원 모델과 다른 점을 어떻게 밝힐지"],
    ["3", "\"세 가지 통제된 ablation\"의 표현"],
    ["4", "도착 분산·납기 여유 실험의 범위와 분량"],
  ];
  ds.forEach((d, i) => {
    const y = TOP + 0.85 + i * 0.88;
    s.addText(d[0], { x: 8.55, y, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: C.background1, fill: { color: C.accent3 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `decision ${d[0]}` });
    text(s, d[1], 9.12, y - 0.02, 3.4, 0.7, { fontSize: 14, valign: "top" });
  });
  s.addNotes("초안과 결과는 docs/revision_drafts/ 폴더와 심사 의견 관리 스프레드시트에 있다.");
}

// ------------------------------------------------------------------ 3. CP-SAT finding
pres.addSection({ title: "CP-SAT 정정" });
{
  const s = content("M 조건에서는 CP-SAT가 실행 가능해를 찾는다", ["R1-1"], null, "CP-SAT 정정");
  const stats = [
    ["12 / 12", "재실행 기록이 모두 유효", "600초를 온전히 계산 (11월 13일, 15일)", C.accent1],
    ["6 / 6", "M: 실행 가능해 반환", "최적성은 한 건도 증명되지 않음", C.accent2],
    ["0 / 6", "L: 실행 가능해 없음", "제약 약 697만 개, 전처리에서 시간 소진", C.accent3],
  ];
  stats.forEach((st, i) => {
    const x = MX + i * 4.12;
    card(s, x, TOP, 3.9, 2.25, { name: `stat ${i + 1}` });
    text(s, st[0], x + 0.25, TOP + 0.15, 3.4, 0.95, { fontSize: 54, bold: true, color: st[3] });
    text(s, st[1], x + 0.25, TOP + 1.2, 3.4, 0.35, { fontSize: 16, bold: true });
    text(s, st[2], x + 0.25, TOP + 1.6, 3.4, 0.5, { fontSize: 13, color: C.accent5 });
  });
  text(s, "무엇이 잘못되어 있었나", MX, 4.35, CW, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "제출본: \"M의 시간 제약 조건과 L의 모든 조건에서 CP-SAT가 실행 가능해를 반환하지 못했다\"",
    "7월 기록은 실행 중 Mac이 잠들어 실제 계산 시간이 21~355초였다. 솔버의 제한시간은 경과 시간 기준이라 그대로 종료되었다",
    "M 시간 제약 조건에서 균등 선택 GILS는 CP-SAT 기준해보다 0.12~0.26% 낮은(좋은) 목적값을 0.5초 안에 찾는다",
  ], MX, 4.8, CW, 1.9);
}

// ------------------------------------------------------------------ 4. CP-SAT wording (decision 1)
{
  const s = content("CP-SAT 정정으로 네 곳의 서술이 바뀐다", ["R1-1", "R1-18", "R2-11", "R2-14"], "결정 1", "CP-SAT 정정");
  const rows = [[HEAD("위치"), HEAD("제출본"), HEAD("수정안")]];
  [
    ["초록", "… while CP-SAT fails within 600 s.", "… on large instances, for which CP-SAT returns no feasible solution within 600 s."],
    ["5.1절", "M의 시간 제약 조건과 L의 모든 조건에서 실행 가능해를 반환하지 못했다", "M은 실행 가능해를 반환했으나 최적성 미증명. L의 모든 조건에서 반환하지 못했다"],
    ["Table 4", "M-medium, M-tight의 vs CP-SAT 열이 \"---\"", "값을 채움 (GILS-uniform −0.26%, −0.12%)"],
    ["초록, 5.1절, 7장", "기준해 대비 평균 0.10~0.23%", "0.11~0.23% (M-none을 더 좋은 재실행 기준해로 통일)"],
  ].forEach((r) => rows.push([CELL(r[0], { bold: true }), CELL(r[1]), CELL(r[2])]));
  table(s, rows, MX, TOP, CW, [1.9, 4.9, 5.33], { rowH: 0.62 });
  card(s, MX, 5.15, CW, 1.55, { name: "decision card" });
  text(s, "결정해 주실 것", MX + 0.25, 5.28, 3, 0.35, { fontSize: 15, bold: true, color: C.accent3 });
  bullets(s, [
    "심사위원이 지적하지 않은 M 조건 정정을 답변서의 \"저자 자체 수정 사항\"에 밝히는 방식",
    "초록의 숫자가 0.10에서 0.11로 바뀌는 점. L에 대한 결론과 최적해 대비 0.23%는 그대로이다",
  ], MX + 0.25, 5.7, CW - 0.5, 0.95);
}

// ------------------------------------------------------------------ 5. problem structure figure
pres.addSection({ title: "문제 정의와 가정" });
{
  const s = content("문제 구조 그림을 새로 넣는다", ["R2-1", "R2-2"], null, "문제 정의와 가정");
  const iw = 8.3, ih = iw * 1277 / 2378;
  s.addImage({ path: path.join(FIG, "fig_problem_structure.png"), x: MX, y: TOP, w: iw, h: ih, altText: "기존 크로스도킹과 병행 트럭 방식을 비교한 문제 구조 그림", objectName: "figure problem structure" });
  card(s, 9.15, TOP, 3.58, ih, { name: "notes card" });
  text(s, "그림이 답하는 것", 9.38, TOP + 0.2, 3.1, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "(a) 기존 방식: 입고트럭은 전부 하역하고 다른 트럭이 싣고 나간다",
    "(b) 본 연구: 병행 트럭이 한 목적지의 화물을 유지한 채 운송 트럭이 된다",
    "도착 시각과 납기 때문에 늦은 트럭이 다른 트럭을 늦춘다",
    "출고트럭의 도어는 결정 사항임을 표시했다",
  ], 9.38, TOP + 0.7, 3.15, ih - 0.85, { fontSize: 14 });
  text(s, "기존 Figure 1(작업 시각 타임라인)은 그대로 두고, 이 그림을 그 앞에 넣는다. draw.io 원본이 있어 수정할 수 있다.", MX, TOP + ih + 0.25, CW, 0.5, { fontSize: 13, color: C.accent5 });
}

// ------------------------------------------------------------------ 6. operating assumptions
{
  const s = content("운영 가정을 단순화 가정으로 명시한다", ["R1-8", "R2-2"], null, "문제 정의와 가정");
  const rows = [[HEAD("가정"), HEAD("성격"), HEAD("근거와 서술 방향")]];
  [
    ["도어당 병행 트럭 최대 1대", "단순화 가정", "원 모델을 따른다. \"동시에 1대\"가 아니라 계획기간 전체에서 1대이다. 운영상 제약이 아님을 2.2절에 밝힌다"],
    ["목적지 물량을 트럭 한 대가 운송", "단순화 가정", "차량 용량이 충분하다고 본다. 분할 운송은 다루지 않는다"],
    ["각 도어 앞의 보관 공간", "원 모델의 가정", "화물은 중앙 저장 구역을 거치지 않고 목적 도어 앞에서 기다린다"],
    ["모든 트럭이 시각 0에 가용", "본 연구에서 완화", "트럭별 도착 시각과 연성 납기를 도입했다"],
  ].forEach((r) => rows.push([CELL(r[0], { bold: true }), CELL(r[1]), CELL(r[2])]));
  table(s, rows, MX, TOP, CW, [3.3, 2.0, 6.83], { rowH: 0.7 });
  card(s, MX, 5.4, CW, 1.3, { name: "caveat card" });
  text(s, "함께 밝힐 점", MX + 0.25, 5.52, 3, 0.35, { fontSize: 15, bold: true, color: C.text2 });
  text(s, "도착 시각이 서로 다른 본 문제에서는 한 도어에서 병행 트럭을 차례로 받는 운영이 의미가 있다. 실험은 도어 수와 병행 트럭 수를 같게 두었으므로 이 가정의 영향을 지금 데이터로는 평가할 수 없다. 7장의 한계로 적는다.", MX + 0.25, 5.9, CW - 0.5, 0.75, { fontSize: 14 });
}

// ------------------------------------------------------------------ 7. transfer time (decision 2)
{
  const s = content("이송시간 계산이 원 모델과 다르다", ["R2-3"], "결정 2", "문제 정의와 가정");
  const rows = [[HEAD(""), HEAD("원 모델 (2020)"), HEAD("본 연구")]];
  [
    ["t_mn의 정의", "화물 한 단위를 옮기는 시간", "도어 쌍별 배치 이송시간"],
    ["이송에 걸리는 시간", "물량 × t_mn", "t_mn (물량과 무관)"],
    ["물량이 반영되는 곳", "하역·적재, 이송", "하역·적재"],
  ].forEach((r) => rows.push([CELL(r[0], { bold: true }), CELL(r[1]), CELL(r[2], { bold: true, color: HEX.accent1 })]));
  table(s, rows, MX, TOP, 7.4, [2.3, 2.6, 2.5], { rowH: 0.55 });
  bullets(s, [
    "심사위원이 예로 든 \"단위 이동시간 × 물량\"이 원 모델의 방식이다",
    "제출본에는 이 차이가 적혀 있지 않고, 4.2절은 none 조건이 \"원 모델과 같다\"고 쓴다",
  ], MX, 4.15, 7.4, 1.1);
  const iw = 4.2, ih = iw * 1676 / 1795;
  s.addImage({ path: path.join(FIG, "fig_transfer_example.png"), x: 8.53, y: TOP - 0.1, w: iw, h: ih, altText: "도어 간 직접 이송의 수치 예시 평면도", objectName: "figure transfer example" });
  card(s, MX, 5.4, 7.4, 1.3, { name: "decision card" });
  text(s, "결정해 주실 것", MX + 0.25, 5.5, 3, 0.35, { fontSize: 15, bold: true, color: C.accent3 });
  bullets(s, [
    "안 1 (권고): 차이를 2.2절에 밝히고 \"원 모델과 같다\"는 표현을 고친다",
    "안 2: 물량 비례 이송시간으로 민감도 실험을 추가한다",
  ], MX + 0.25, 5.9, 6.9, 0.75);
  s.addNotes("배치 이송을 택한 이유의 기록이 저장소에 없다. 근거로 쓸 설명을 교수님과 확인한다. 예시 그림은 R2-3이 요청한 화물 이동 예시이다.");
}

// ------------------------------------------------------------------ 8. VAA regret
pres.addSection({ title: "알고리즘 설명" });
{
  const s = content("VAA 후회도를 식과 예시로 제시한다", ["R2-9"], null, "알고리즘 설명");
  const steps = [
    ["1", "비용 (원 모델의 식)", "c(i,d) = (H_i − h_id) + L_id", "트럭 i가 목적지 d를 유지할 때 하역할 나머지 화물과 받아 실을 화물의 처리시간"],
    ["2", "후회도 (표준 Vogel 근사법)", "R = 두 번째로 작은 비용 − 가장 작은 비용", "트럭마다, 목적지마다 계산한다"],
    ["3", "선택", "후회도가 가장 큰 쪽의 최소 비용 짝을 확정", "확정한 트럭과 목적지를 빼고 반복한다"],
  ];
  steps.forEach((st, i) => {
    const y = TOP + i * 1.42;
    card(s, MX, y, 6.2, 1.27, { name: `step ${st[0]}` });
    s.addText(st[0], { x: MX + 0.2, y: y + 0.2, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: C.background1, fill: { color: C.accent1 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `step no ${st[0]}` });
    text(s, st[1], MX + 0.8, y + 0.13, 5.2, 0.3, { fontSize: 14, bold: true, color: C.text2 });
    text(s, st[2], MX + 0.8, y + 0.47, 5.2, 0.3, { fontSize: 14, bold: true });
    text(s, st[3], MX + 0.8, y + 0.83, 5.2, 0.35, { fontSize: 12, color: C.accent5 });
  });
  text(s, "예시: 병행 트럭 3대, 목적지 4개의 비용과 1회차 후회도", 7.2, TOP, 5.53, 0.35, { fontSize: 14, bold: true, color: C.text2 });
  const hi = { bold: true, color: "FFFFFF", fill: { color: HEX.accent2 }, align: "center" };
  const ce = { align: "center" };
  const rows = [
    [HEAD("c(i,d)", ce), HEAD("d1", ce), HEAD("d2", ce), HEAD("d3", ce), HEAD("d4", ce), HEAD("R(트럭)", ce)],
    [CELL("i1", { bold: true, align: "center" }), CELL("15", ce), CELL("26", ce), CELL("26", ce), CELL("23", ce), CELL("8", ce)],
    [CELL("i2", { bold: true, align: "center" }), CELL("30", ce), CELL("15", hi), CELL("23", ce), CELL("28", ce), CELL("8", ce)],
    [CELL("i3", { bold: true, align: "center" }), CELL("25", ce), CELL("30", ce), CELL("20", ce), CELL("19", ce), CELL("1", ce)],
    [CELL("R(목적지)", { bold: true, align: "center" }), CELL("10", ce), CELL("11", hi), CELL("3", ce), CELL("4", ce), CELL("", ce)],
  ];
  table(s, rows, 7.2, TOP + 0.5, 5.53, [1.33, 0.8, 0.8, 0.8, 0.8, 1.0], { rowH: 0.46 });
  bullets(s, [
    "최대 후회도는 목적지 d2의 11이므로 i2가 d2를 유지한다",
    "원 논문은 후회도 계산식을 주지 않는다. 비용은 원 모델, 계산 절차는 본 연구의 구현으로 구분해 쓴다",
    "참고문헌 1건 추가: Korukoğlu and Ballı (2011)",
  ], 7.2, 5.0, 5.53, 1.75, { fontSize: 14, paraSpaceAfter: 4 });
}

// ------------------------------------------------------------------ 9. pseudocode + definitions
{
  const s = content("의사코드와 병목의 정의를 추가한다", ["R1-11", "R1-12", "R2-9"], null, "알고리즘 설명");
  card(s, MX, TOP, 6.5, 4.95, { fill: C.text2, line: C.text2, name: "code card" });
  const code = [
    "Algorithm 1. VAA-GILS",
    " 1  s ← Descent(VAA(instance));  s* ← s;  c ← 0",
    " 4  for n = 1 to N do",
    " 5      select ω ∈ Ω uniformly at random",
    " 6      s′ ← GuidedMove(s, ω) if ω ∈ Ω_G else ω(s)",
    " 7      if J(s′) < J(s*) then",
    " 8          s′ ← Descent(s′);  s* ← s′;  c ← 0",
    "10      else c ← c + 1",
    "13      if J(s′) < J(s) then s ← s′",
    "16      if c ≥ P then",
    "17          s ← s*;  apply K random generic moves;  c ← 0",
    "24  return Descent(s*)",
  ].join("\n");
  s.addText(code, { x: MX + 0.25, y: TOP + 0.2, w: 6.0, h: 4.55, fontFace: "Courier New", fontSize: 12, color: C.background1, align: "left", valign: "top", margin: 0, isTextBox: true, objectName: "pseudocode" });
  text(s, "의사코드가 밝히는 순서", 7.5, TOP, 5.23, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "하강 탐색은 후보가 최선해보다 좋을 때만 적용한다 (7~8행)",
    "수락은 현재 해보다 엄격히 좋을 때만 한다 (13행)",
    "병목 유도 연산자는 6행의 GuidedMove로 들어간다",
  ], 7.5, TOP + 0.45, 5.23, 1.6);
  text(s, "병목의 정의", 7.5, TOP + 2.2, 5.23, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "병목 도어: 마지막 작업의 완료 시각이 가장 늦은 도어",
    "병목 트럭: 완료 시각이 가장 늦은 트럭",
    "최대 지연 트럭: 납기지연이 가장 큰 트럭",
  ], 7.5, TOP + 2.65, 5.23, 1.5);
  card(s, 7.5, 5.95, 5.23, 0.75, { name: "fix card" });
  text(s, "본문 수정: \"30회 연속 개선이 없으면\" → \"최선해가 30회 연속 갱신되지 않으면\"", 7.7, 6.03, 4.85, 0.6, { fontSize: 13, valign: "middle" });
  s.addNotes("의사코드 전체(25행)와 Descent, GuidedMove 절차는 R1-11_R2-9_algorithm1_pseudocode.md에 있다. g3는 병행 트럭일 때 도어 이동을 하므로 g1과 동일 이동이 아니다. 본문 문장을 함께 고친다.");
}

// ------------------------------------------------------------------ 10. flowchart
{
  const s = content("흐름도에서 병목 유도 연산자를 강조한다", ["R1-10", "R2-9"], null, "알고리즘 설명");
  const ih = 5.05, iw = ih * 2632 / 2298;
  s.addImage({ path: path.join(FIG, "fig_algorithm_flow.png"), x: MX, y: TOP, w: iw, h: ih, altText: "VAA-GILS 알고리즘 흐름도", objectName: "figure flowchart" });
  const x = MX + iw + 0.45, w = W - MX - x;
  text(s, "그림의 구성", x, TOP, w, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "초기화, 반복 탐색, 종료의 세 구역",
    "분기 순서는 의사코드와 같다: 새 최선해 → 수락 → 재시작 → 종료",
    "진한 파란 상자가 본 연구가 더한 병목 유도 연산자이다",
    "오른쪽 GuidedMove 표가 g1~g4의 대상 트럭과 이동을 보인다",
  ], x, TOP + 0.5, w, 2.6);
  card(s, x, 4.75, w, 2.0, { name: "role card" });
  text(s, "두 심사위원의 요구를 나누어 맡긴다", x + 0.22, 4.87, w - 0.44, 0.35, { fontSize: 15, bold: true, color: C.text2 });
  text(s, "흐름도는 전체 순서를, 의사코드는 정확한 조건을 보인다. R1-10은 흐름도를, R1-11은 의사코드를 각각 요구했으므로 둘 다 넣는다.", x + 0.22, 5.3, w - 0.44, 1.35, { fontSize: 14 });
}

// ------------------------------------------------------------------ 11. ablation wording (decision 3)
pres.addSection({ title: "분석과 추가 실험" });
{
  const s = content("\"세 가지 통제된 ablation\"은 5.2절에 두 개뿐이다", ["R1-15"], "결정 3", "분석과 추가 실험");
  const rows = [[HEAD("분석"), HEAD("표"), HEAD("위치"), HEAD("표본")]];
  [
    ["① 연산자 집합", "Table 6", "5.2절", "조건당 5개"],
    ["② 엔진 구성요소", "Table 7", "5.2절", "조건당 5개"],
    ["③ 연산자 선택 정책", "Table 8", "5.3절 (보조 분석)", "조건당 20개"],
  ].forEach((r, i) => rows.push(r.map((c) => CELL(c, i === 2 ? { color: HEX.accent3, bold: true } : {}))));
  table(s, rows, MX, TOP, CW, [4.2, 2.2, 3.3, 2.43], { rowH: 0.5 });
  const opts = [
    ["안 A (권고)", "\"두 가지\"로 고친다", ["5.2절 첫 문장 하나만 수정", "4.3절의 용어, 절 구성과 그대로 맞는다", "③은 지금처럼 보조 분석으로 남는다"], C.accent2],
    ["안 B", "\"세 가지 통제 비교\"로 유지한다", ["5.2절, 5.3절, 4.3절을 함께 수정", "1장과 3장이 ③을 ablation으로 부르는 것과 맞는다", "③이 주요 분석으로 올라간다"], C.accent1],
  ];
  opts.forEach((o, i) => {
    const x = MX + i * 6.17, w = 5.96, y = 4.0;
    card(s, x, y, w, 2.7, { name: `option ${i + 1}` });
    s.addText(o[0], { x: x + 0.25, y: y + 0.2, w: 1.7, h: 0.34, fontSize: 13, bold: true, color: C.background1, fill: { color: o[3] }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `option tag ${i + 1}` });
    text(s, o[1], x + 2.1, y + 0.2, w - 2.3, 0.34, { fontSize: 16, bold: true, valign: "middle" });
    bullets(s, o[2], x + 0.25, y + 0.8, w - 0.5, 1.8);
  });
}

// ------------------------------------------------------------------ 12. individual ablation
{
  const s = content("g1과 g2는 각각 독립적으로 기여한다", ["R1-16"], null, "분석과 추가 실험");
  const ce = { align: "center" };
  const rows = [[HEAD("없는 쪽 → 있는 쪽"), HEAD("개선(%)", ce), HEAD("Holm p", ce), HEAD("판정")]];
  [
    ["generic → generic+g1", "+0.038", "0.006", "g1을 넣은 쪽이 좋다", 1],
    ["generic → generic+g2", "+0.064", "0.001", "g2를 넣은 쪽이 좋다", 1],
    ["generic → generic+g3", "−0.002", "0.269", "차이 없음", 0],
    ["generic → generic+g4", "+0.049", "0.041", "g4를 넣은 쪽이 좋다", 1],
    ["full−g1 → full", "+0.035", "0.002", "g1이 있는 쪽이 좋다", 1],
    ["full−g2 → full", "+0.051", "0.006", "g2가 있는 쪽이 좋다", 1],
    ["full−g3 → full", "+0.015", "0.269", "차이 없음", 0],
    ["full−g4 → full", "+0.048", "0.269", "차이 없음", 0],
  ].forEach((r) => rows.push([CELL(r[0], { bold: true }), CELL(r[1], ce), CELL(r[2], ce), CELL(r[3], r[4] ? GOOD : { color: HEX.accent5 })]));
  table(s, rows, MX, TOP, 7.6, [2.9, 1.2, 1.2, 2.3], { rowH: 0.47 });
  text(s, "시간 제약 조건 30쌍. 양수이면 유도 연산자가 있는 쪽의 목적값이 낮다. 새 집합 8개, 1,800회 실행.", MX, TOP + 4.4, 7.6, 0.55, { fontSize: 12, color: C.accent5 });
  const x = 8.5, w = W - MX - x;
  text(s, "읽는 법", x, TOP, w, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, [
    "g1, g2: 단독으로 더해도, 전체에서 빼도 유의하다",
    "g4: 단독으로는 유의하나 다른 연산자가 대신할 수 있다",
    "g3: 개별 효과가 확인되지 않았다",
  ], x, TOP + 0.45, w, 2.2);
  card(s, x, 4.45, w, 2.25, { name: "position card" });
  text(s, "원고에서의 입장", x + 0.22, 4.57, w - 0.44, 0.35, { fontSize: 15, bold: true, color: C.text2 });
  text(s, "\"g3, g4는 보조적인 효과\"라는 제출본의 서술을 유지하고, 그 효과가 주로 g4에서 온다는 점을 덧붙인다. 시험 집합의 결과이므로 최종 엔진에서 g3를 빼지 않는다.", x + 0.22, 5.0, w - 0.44, 1.6, { fontSize: 14 });
}

// ------------------------------------------------------------------ 13. (rho, delta) factorial (decision 4)
{
  const s = content(S13 ? S13.title : "도착 분산과 납기 여유를 따로 켜고 끄는 실험을 설계했다", ["R1-13", "R2-11"], "결정 4", "분석과 추가 실험");
  const ce = { align: "center" };
  const dl = ["δ = ∞ (납기 없음)", "δ = 1.00", "δ = 0.60", "δ = 0.35"];
  const rl = ["ρ = 0 (모두 시각 0)", "ρ = 0.10", "ρ = 0.25", "ρ = 0.50"];
  const base = [
    ["none (원 모델)", "납기만", "납기만", "납기만"],
    ["도착 분산만", "loose", "", ""],
    ["도착 분산만", "", "medium", ""],
    ["도착 분산만", "", "", "tight"],
  ];
  const rows = [[HEAD(S13 ? S13.gridLabel : "설계 (4 × 4)"), ...dl.map((d) => HEAD(d, ce))]];
  rl.forEach((r, i) => {
    rows.push([CELL(r, { bold: true }), ...dl.map((_, j) => {
      const v = S13 ? S13.grid[i][j] : base[i][j];
      const single = (i === 0) !== (j === 0);
      const o = Object.assign({}, ce);
      if (i === 0 && j === 0) Object.assign(o, { fill: { color: HEX.lt2 } });
      else if (single) Object.assign(o, { fill: { color: HEX.accent6 } });
      return CELL(v, o);
    })]);
  });
  table(s, rows, MX, TOP, 7.9, [2.3, 1.6, 1.3, 1.35, 1.35], { rowH: 0.52 });
  text(s, S13 ? S13.gridNote : "파란 칸이 한 요인만 켠 조건이다. 한 인스턴스의 16칸은 화물과 도어 배치가 같고 ρ, δ만 다르다. 규모 3개 × 인스턴스 20개, 10,560회 실행.", MX, TOP + 2.75, 7.9, 0.75, { fontSize: 12, color: C.accent5 });
  const x = 8.8, w = W - MX - x;
  text(s, S13 ? "결과" : "왜 이 설계인가", x, TOP, w, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, S13 ? S13.findings : [
    "제출본은 medium, tight 두 조합뿐이라 두 요인이 함께 바뀐다",
    "첫 행과 첫 열에서 한 요인만의 효과를, 안쪽 아홉 칸에서 겹칠 때의 효과를 본다",
    "측정: 총 작업완료시간, 총 납기지연, VAA와 Extended SA-RL5 대비 개선율",
  ], x, TOP + 0.45, w, 3.0, { fontSize: 14 });
  card(s, MX, 5.4, CW, 1.3, { name: "decision card" });
  text(s, "결정해 주실 것", MX + 0.25, 5.5, 3, 0.35, { fontSize: 15, bold: true, color: C.accent3 });
  bullets(s, [
    "수준 값과 범위(4 × 4)가 적절한지",
    "원고에 넣을 분량: 본문 표 하나와 4.2절·5장의 서술, 또는 부록",
  ], MX + 0.25, 5.9, CW - 0.5, 0.75);
  if (S13 && S13.notes) s.addNotes(S13.notes);
}

// ------------------------------------------------------------------ 14. not started
pres.addSection({ title: "남은 일" });
{
  const s = content("17건은 아직 착수하지 않았다", [], null, "남은 일");
  const groups = [
    ["수리모형 설명", "6건", ["제약식별 운영 조건 설명 (R2-6)", "인덱스·변수 범위 점검 (R2-7)", "λ = 1을 실험 설정으로 이동 (R2-8)", "Δbo, Gain 계산식 (R2-12, R2-13)", "수식 안 영문 서술어 (R1-9)"]],
    ["표현", "5건", ["국문·영문 용어 통일 (R1-2)", "구어체를 학술체로 (R1-3)", "복수 저자 표기 통일 (R1-4)", "Table 1 열 폭, 약어 각주 (R1-7, R2-4)"]],
    ["구성", "3건", ["관련 연구 소제목 (R1-5)", "소제목·문단 구분 (R2-5)", "비교 방법 설명을 실험 설정으로 이동 (R2-10)"]],
    ["논의·정의", "3건", ["성능 차이의 의미 논의 (R2-11)", "한계와 향후 연구 (R2-14)", "Li 등(2026) 선정 기준 (R1-6)"]],
  ];
  groups.forEach((g, i) => {
    const w = 2.88, x = MX + i * (w + 0.2);
    card(s, x, TOP, w, 4.2, { name: `group ${i + 1}` });
    text(s, g[1], x + 0.2, TOP + 0.15, w - 0.4, 0.7, { fontSize: 36, bold: true, color: C.accent1 });
    text(s, g[0], x + 0.2, TOP + 0.9, w - 0.4, 0.35, { fontSize: 15, bold: true, color: C.text2 });
    bullets(s, g[2], x + 0.2, TOP + 1.4, w - 0.4, 2.7, { fontSize: 12, paraSpaceAfter: 6 });
  });
  text(s, "새 실험이 필요한 항목은 없다. R2-11과 R2-14는 CP-SAT 재실행과 R1-13 실험 결과를 근거로 쓴다. Figure 2와 Figure 3은 재실험 이전 그림이어서 최신 그림으로 바꿔야 한다 (R1-17).", MX, 6.15, CW, 0.6, { fontSize: 14 });
}

// ------------------------------------------------------------------ 15. decisions and next steps
{
  const s = content("오늘 정할 것과 다음 단계", [], null, "남은 일", "CLOSING");
  const rows = [[HEAD("결정", { fill: { color: HEX.accent3 } }), HEAD("내용", { fill: { color: HEX.accent3 } }), HEAD("권고", { fill: { color: HEX.accent3 } })]];
  [
    ["1", "CP-SAT 서술의 자체 정정, 초록 0.10 → 0.11", "정정하고 답변서에 밝힌다"],
    ["2", "이송시간 계산이 원 모델과 다른 점", "차이를 2.2절에 밝힌다 (새 실험 없음)"],
    ["3", "\"세 가지 통제된 ablation\"", "\"두 가지\"로 고친다"],
    ["4", "도착 분산·납기 여유 실험의 범위와 분량", "4 × 4 설계, 본문 표 하나"],
  ].forEach((r) => rows.push([CELL(r[0], { bold: true, align: "center", fill: { color: "FFFFFF" } }), CELL(r[1], { fill: { color: "FFFFFF" } }), CELL(r[2], { bold: true, fill: { color: "FFFFFF" } })]));
  table(s, rows, MX, TOP, CW, [1.0, 6.2, 4.93], { rowH: 0.55 });
  const steps = ["결정 반영", "원고 수정", "남은 17건 처리", "답변서 작성", "재제출"];
  steps.forEach((st, i) => {
    const w = 2.2, x = MX + i * (w + 0.28), y = 5.2;
    s.addShape(pres.ShapeType.rect, { x, y, w, h: 1.1, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0.75 }, objectName: `next step ${i + 1}` });
    text(s, String(i + 1), x + 0.18, y + 0.12, 0.5, 0.4, { fontSize: 18, bold: true, color: C.accent6 });
    text(s, st, x + 0.18, y + 0.55, w - 0.36, 0.4, { fontSize: 15, bold: true, color: C.background1 });
  });
  text(s, "수정 기한과 단계별 일정은 면담에서 정한다", MX, 6.5, CW, 0.35, { fontSize: 13, color: C.accent6 });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT, "slides", slideNo);
})();
