// Shared theme, layouts and helpers for the experiment-result decks.
// Same visual language as docs/revision_drafts/make_advisor_deck.js.
const path = require("path");
const pptxgen = require("pptxgenjs");
const SKILL = "/Users/yskim/.claude/skills/synced/43f8ff3f-425d-47cd-846e-dcd535a56441_dc04b54d-4e19-4577-9604-39fffa15168a/pptx";
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));

const THEME = {
  name: "VAA-GILS Revision",
  headFontFace: "맑은 고딕",
  bodyFontFace: "맑은 고딕",
  colors: {
    dk1: "1B1F24", lt1: "FFFFFF", dk2: "1F3A5F", lt2: "F2F4F7",
    accent1: "2F5D8A", accent2: "3A9E7E", accent3: "B23A48", accent4: "7B5EA7",
    accent5: "6B7785", accent6: "C9D8EA", hlink: "2F5D8A", folHlink: "7B5EA7",
  },
};

const W = 13.33, MX = 0.6, CW = W - 2 * MX, TOP = 1.75;

function newDeck(title) {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = title;
  pres.author = "yskim";
  const C = pres.SchemeColor;
  const HEX = THEME.colors;

  pres.defineSlideMaster({
    title: "COVER",
    background: { color: HEX.dk2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 2.35, w: CW, h: 1.5, fontSize: 40, bold: true, fontFace: THEME.headFontFace, color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: MX, y: 4.05, w: CW, h: 1.2, fontSize: 18, fontFace: THEME.bodyFontFace, color: C.accent6, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: HEX.lt1 },
    margin: [TOP, MX, 0.7, MX],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.72, w: CW, h: 0.85, fontSize: 30, bold: true, fontFace: THEME.headFontFace, color: C.text2, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: W - MX - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, fontFace: THEME.bodyFontFace, color: HEX.accent5, align: "right" },
  });
  pres.defineSlideMaster({
    title: "CLOSING",
    background: { color: HEX.dk2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.72, w: CW, h: 0.85, fontSize: 30, bold: true, fontFace: THEME.headFontFace, color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: W - MX - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, fontFace: THEME.bodyFontFace, color: HEX.accent6, align: "right" },
  });

  // Reviewer-item chips above the title.
  function chips(slide, ids, tag) {
    let x = MX;
    if (tag) {
      slide.addText(tag, { x, y: 0.3, w: 1.55, h: 0.3, fontSize: 11, bold: true, fontFace: THEME.bodyFontFace, color: C.background1, fill: { color: C.accent3 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "tag" });
      x += 1.67;
    }
    for (const id of ids || []) {
      const w = 0.34 + 0.085 * id.length;
      slide.addText(id, { x, y: 0.3, w, h: 0.3, fontSize: 11, bold: true, fontFace: THEME.bodyFontFace, color: C.accent1, fill: { color: C.accent6 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `chip ${id}` });
      x += w + 0.1;
    }
  }
  function content(title, ids, tag, section) {
    const slide = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
    slide.addText(title, { placeholder: "title" });
    chips(slide, ids, tag);
    return slide;
  }
  function closing(title, section) {
    const slide = pres.addSlide({ masterName: "CLOSING", sectionTitle: section });
    slide.addText(title, { placeholder: "title" });
    return slide;
  }
  function card(slide, x, y, w, h, opts = {}) {
    slide.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: opts.fill || C.background2 }, line: { color: opts.line || C.background2, width: 0.75 }, objectName: opts.name || "card" });
  }
  function text(slide, t, x, y, w, h, o = {}) {
    slide.addText(t, Object.assign({ x, y, w, h, fontSize: 14, fontFace: THEME.bodyFontFace, color: C.text1, align: "left", valign: "top", margin: 0, isTextBox: true }, o));
  }
  function bullets(slide, items, x, y, w, h, o = {}) {
    const runs = items.map((it, i) => ({ text: it, options: { bullet: true, breakLine: i < items.length - 1 } }));
    slide.addText(runs, Object.assign({ x, y, w, h, fontSize: 14, fontFace: THEME.bodyFontFace, color: C.text1, align: "left", valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true }, o));
  }
  const HEAD = (t, extra = {}) => ({ text: t, options: Object.assign({ bold: true, color: "FFFFFF", fill: { color: HEX.accent1 }, fontSize: 13, fontFace: THEME.bodyFontFace, valign: "middle" }, extra) });
  const CELL = (t, extra = {}) => ({ text: t, options: Object.assign({ fontSize: 13, fontFace: THEME.bodyFontFace, color: HEX.dk1, valign: "middle" }, extra) });
  function table(slide, rows, x, y, w, colW, o = {}) {
    slide.addTable(rows, Object.assign({ x, y, w, colW, border: { type: "solid", pt: 0.5, color: "C8CED6" }, margin: [0.06, 0.1, 0.06, 0.1], fontFace: THEME.bodyFontFace, autoPage: false }, o));
  }
  // Three stat cards across the content width.
  function stats(slide, items, y, h) {
    items.forEach((st, i) => {
      const x = MX + i * (CW + 0.22) / items.length;
      const w = (CW + 0.22) / items.length - 0.22;
      card(slide, x, y, w, h, { name: `stat ${i + 1}` });
      text(slide, st[0], x + 0.25, y + 0.15, w - 0.5, 0.95, { fontSize: 44, bold: true, color: st[3] || C.accent1 });
      text(slide, st[1], x + 0.25, y + 1.15, w - 0.5, 0.35, { fontSize: 15, bold: true });
      text(slide, st[2], x + 0.25, y + 1.55, w - 0.5, 0.6, { fontSize: 12.5, color: C.accent5 });
    });
  }
  function source(slide, t) {
    text(slide, t, MX, 7.0, CW - 0.8, 0.3, { fontSize: 10, color: C.accent5 });
  }

  return { pres, C, HEX, W, MX, CW, TOP, chips, content, closing, card, text, bullets, HEAD, CELL, table, stats, source,
           GOOD: { color: HEX.accent2, bold: true }, WARN: { color: HEX.accent3, bold: true } };
}

module.exports = { newDeck, applyTheme, THEME };
