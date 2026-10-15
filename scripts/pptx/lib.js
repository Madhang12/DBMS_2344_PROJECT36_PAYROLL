// Shared helpers for the Review 2 / Review 3 decks (pptxgenjs, native shapes, theme colours)
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const path = require("path");
const fs = require("fs");

const ROOT = path.resolve(__dirname, "..", "..");
const SHOTS = path.join(ROOT, "screenshots");

// Palette taken from the Review 1 deck: navy + gold on a pale blue-white
const THEME = {
  name: "Payroll Review",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2146", lt1: "FFFFFF", dk2: "141B41", lt2: "F2F5FC",
    accent1: "3D5A9B", accent2: "C9971C", accent3: "1E2761",
    accent4: "8AA4D6", accent5: "16643A", accent6: "B3261E",
    hlink: "3D5A9B", folHlink: "1E2761",
  },
};

// hex values are needed ONLY where pptxgenjs cannot take a scheme colour
const HEX = { navy: "141B41", gold: "C9971C", blue: "3D5A9B", line: "D9E2F5", muted: "6B7694", ink: "1B2146" };

async function icon(name, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

function makePres(deckLabel, title, opts = {}) {
  const shotsDir = opts.shots || SHOTS;
  const cropsDir = opts.crops || path.join(ROOT, "presentations", "assets", "crops");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = title;
  pres.author = "G Madhan (25WU0102344)";
  pres.subject = "DBMS Project 36 - Employee Payroll and Statutory Deduction Management System";
  const C = pres.SchemeColor;
  const footer = `PROJECT 36  |  EMPLOYEE PAYROLL AND STATUTORY DEDUCTION MANAGEMENT SYSTEM  |  ${deckLabel}`;

  pres.defineSlideMaster({
    title: "CONTENT", background: { color: C.background2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 1.3, y: 0.28, w: 8.2, h: 0.7, fontSize: 30, bold: true,
          color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
      { text: { text: footer, options: { x: 0.5, y: 5.3, w: 8.4, h: 0.22, fontSize: 9, color: C.text1, transparency: 35, margin: 0 } } },
    ],
    slideNumber: { x: 9.1, y: 5.28, w: 0.5, h: 0.25, fontSize: 10, color: C.accent1, bold: true, align: "right" },
  });
  pres.defineSlideMaster({
    title: "DARK", background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 1.3, y: 0.28, w: 8.2, h: 0.7, fontSize: 30, bold: true,
          color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
      { text: { text: footer, options: { x: 0.5, y: 5.3, w: 8.4, h: 0.22, fontSize: 9, color: C.background1, transparency: 45, margin: 0 } } },
    ],
    slideNumber: { x: 9.1, y: 5.28, w: 0.5, h: 0.25, fontSize: 10, color: C.accent2, bold: true, align: "right" },
  });
  pres.defineSlideMaster({ title: "COVER", background: { color: C.text2 }, objects: [] });

  const notes = [];
  const H = { pres, C, notes };

  // slide factory: records the speaker notes for the script file
  const seen = new Set();
  H.slide = (master, section, titleText, speakerNotes) => {
    if (!seen.has(section)) { pres.addSection({ title: section }); seen.add(section); }
    const s = pres.addSlide({ masterName: master, sectionTitle: section });
    if (titleText) s.addText(titleText, { placeholder: "title" });
    s.addNotes(speakerNotes);
    notes.push({ title: titleText || "(cover)", text: speakerNotes });
    return s;
  };

  const shadow = () => ({ type: "outer", color: "141B41", opacity: 0.12, blur: 6, offset: 2, angle: 90 });

  H.text = (s, t, o = {}) => s.addText(t, Object.assign({ isTextBox: true, margin: 0, valign: "top" }, o));

  H.card = (s, x, y, w, h, o = {}) => {
    s.addShape(pres.ShapeType.roundRect, Object.assign({ x, y, w, h, rectRadius: 0.08, fill: { color: C.background1 },
      line: { color: HEX.line, width: 0.75 }, shadow: shadow() }, o));
  };

  H.dark = (s, x, y, w, h, o = {}) => {
    s.addShape(pres.ShapeType.roundRect, Object.assign({ x, y, w, h, rectRadius: 0.08, fill: { color: C.accent3 }, line: { color: C.accent3, width: 0 } }, o));
  };

  H.circleIcon = async (s, iconName, x, y, d, fillColor, iconColor = "#FFFFFF") => {
    s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fillColor }, line: { color: fillColor, width: 0 } });
    const pad = d * 0.26;
    s.addImage({ data: await icon(iconName, iconColor), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad });
  };

  H.titleIcon = (s, iconName, dark = false) =>
    H.circleIcon(s, iconName, 0.5, 0.3, 0.66, dark ? C.accent2 : C.accent3, "#FFFFFF");

  H.pill = (s, t, x, y, w, o = {}) => {
    s.addText(t, Object.assign({ isTextBox: true, x, y, w, h: 0.3, shape: pres.ShapeType.roundRect, rectRadius: 0.15,
      fill: { color: C.accent1, transparency: 85 }, color: C.accent3, fontSize: 11, bold: true, align: "center", valign: "middle", margin: 0 }, o));
  };

  H.shot = (s, file, x, y, w) => {
    const h = w * 1215 / 2160;
    s.addShape(pres.ShapeType.rect, { x: x - 0.04, y: y - 0.04, w: w + 0.08, h: h + 0.08, fill: { color: C.background1 },
      line: { color: HEX.line, width: 1 }, shadow: shadow() });
    s.addImage({ path: path.join(shotsDir, file), x, y, w, h, altText: "Screenshot of the running application: " + file.replace(/^\d+_|\.png$/g, "").replace(/_/g, " ") });
    return h;
  };

  // pre-cropped screenshot (sidebar removed) from presentations/assets/crops
  H.shotC = (s, file, x, y, w) => {
    const p = path.join(cropsDir, file);
    const h = w * 1016 / 1806;
    s.addShape(pres.ShapeType.rect, { x: x - 0.04, y: y - 0.04, w: w + 0.08, h: h + 0.08, fill: { color: C.background1 },
      line: { color: HEX.line, width: 1 }, shadow: shadow() });
    s.addImage({ path: p, x, y, w, h, altText: "Screenshot of the running application: " + file.replace(/^\d+_|\.png$/g, "").replace(/_/g, " ") });
    return h;
  };

  H.stat = (s, big, label, x, y, w, h, o = {}) => {
    H.card(s, x, y, w, h);
    H.text(s, big, { x, y: y + h * 0.14, w, h: h * 0.5, fontSize: o.size || 30, bold: true, color: C.accent3, align: "center", valign: "middle", fontFace: "Cambria" });
    H.text(s, label, { x: x + 0.1, y: y + h * 0.62, w: w - 0.2, h: h * 0.3, fontSize: 12, color: C.text1, align: "center", valign: "top" });
  };

  // bullets with a bold lead word:  [["Lead", " rest"], ...]
  H.bullets = (s, items, x, y, w, h, o = {}) => {
    const runs = [];
    items.forEach((it, i) => {
      const last = i === items.length - 1;
      if (Array.isArray(it)) {
        runs.push({ text: it[0], options: { bold: true, bullet: { indent: 14 }, breakLine: false, color: o.leadColor || C.text2 } });
        runs.push({ text: it[1], options: { breakLine: !last, color: o.color || C.text1 } });
      } else runs.push({ text: it, options: { bullet: { indent: 14 }, breakLine: !last, color: o.color || C.text1 } });
    });
    const oo = Object.assign({}, o); delete oo.leadColor; delete oo.color;
    H.text(s, runs, Object.assign({ x, y, w, h, fontSize: 14, paraSpaceAfter: 7, valign: "top" }, oo));
  };

  // straight connector between two points
  H.line = (s, x1, y1, x2, y2, o = {}) => {
    const x = Math.min(x1, x2), y = Math.min(y1, y2), w = Math.abs(x2 - x1), h = Math.abs(y2 - y1);
    const flipV = (x2 - x1) * (y2 - y1) < 0;
    s.addShape(pres.ShapeType.line, { x, y, w, h, flipV, line: Object.assign({ color: C.accent1, width: 1.5 }, o) });
  };

  H.arrow = (s, x1, y1, x2, y2, o = {}) => H.line(s, x1, y1, x2, y2, Object.assign({ endArrowType: "triangle" }, o));

  // simple SQL highlighter -> text runs
  const KW = /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|HAVING|JOIN|LEFT JOIN|ON|AS|AND|OR|NOT EXISTS|EXISTS|IN|INSERT INTO|VALUES|UPDATE|SET|DELETE|CREATE TABLE|PRIMARY KEY|FOREIGN KEY|REFERENCES|CHECK|UNIQUE|NOT NULL|DEFAULT|CONSTRAINT|LIMIT|DESC|ASC|COUNT|SUM|AVG|MAX|MIN|ROUND|COALESCE|ON DELETE|RESTRICT|CASCADE|DISTINCT|VIEW)\b/g;
  H.sql = (s, code, x, y, w, h, fs = 11) => {
    H.dark(s, x, y, w, h, { fill: { color: C.text2 }, line: { color: C.text2, width: 0 } });
    const lines = code.split("\n");
    const KWG = new RegExp(KW.source, "g");
    const runs = [];
    lines.forEach((ln, li) => {
      let last = 0;
      for (const m of ln.matchAll(KWG)) {
        if (m.index > last) runs.push({ text: ln.slice(last, m.index), options: { color: C.background2 } });
        runs.push({ text: m[0], options: { color: C.accent2, bold: true } });
        last = m.index + m[0].length;
      }
      if (last < ln.length) runs.push({ text: ln.slice(last), options: { color: C.background2 } });
      runs.push({ text: "", options: { breakLine: li < lines.length - 1 } });
    });
    s.addText(runs, { isTextBox: true, x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h - 0.2, fontFace: "Courier New", fontSize: fs, valign: "top", margin: 0 });
  };

  // table helper (header navy, zebra rows)
  H.table = (s, header, rows, x, y, w, colW, o = {}) => {
    const fs = o.fontSize || 11;
    const head = header.map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.accent3 }, fontSize: fs } }));
    const body = rows.map((r, ri) => r.map((c) => {
      const cell = typeof c === "object" && c !== null && c.text !== undefined ? c : { text: String(c) };
      return { text: cell.text, options: Object.assign({ color: C.text1, fontSize: fs, fill: { color: ri % 2 ? C.background2 : C.background1 } }, cell.options || {}) };
    }));
    s.addTable([head, ...body], { x, y, w, colW, border: { type: "solid", pt: 0.5, color: HEX.line }, valign: "middle",
      rowH: o.rowH || 0.3, margin: [0.03, 0.08, 0.03, 0.08] });
  };

  return H;
}

// ---------------------------------------------------------------- ER diagram (native shapes)
const ER = {
  // name: [x, y, w, kind]   kind: master | input | output
  Department: [1.95, 1.2, 1.5, "master"], Designation: [4.95, 1.2, 1.5, "master"],
  "Payroll Config": [0.35, 1.2, 1.35, "master"],
  "Salary Structure": [0.35, 2.55, 1.5, "master"], Employee: [3.45, 2.55, 1.7, "core"],
  "Payroll Period": [7.1, 1.2, 1.55, "master"], "Payroll Detail": [6.35, 2.55, 1.55, "core"],
  Payslip: [8.6, 2.2, 1.1, "output"], "Bank Transfer": [8.6, 3.0, 1.1, "output"],
  Attendance: [0.35, 4.2, 1.5, "input"], Earnings: [2.05, 4.2, 1.5, "input"], Deductions: [3.75, 4.2, 1.5, "input"],
  Loan: [5.45, 4.2, 1.5, "input"], "Loan Repayment": [7.5, 4.2, 1.7, "output"],
};
const ER_H = 0.52;
function anchor(name, side) {
  const [x, y, w] = ER[name];
  return { T: [x + w / 2, y], B: [x + w / 2, y + ER_H], L: [x, y + ER_H / 2], R: [x + w, y + ER_H / 2] }[side];
}
const ER_RELS = [
  ["Department", "B", "Employee", "T", "1 : N"], ["Designation", "B", "Employee", "T", "1 : N"],
  ["Salary Structure", "R", "Employee", "L", "1 : 1"], ["Employee", "R", "Payroll Detail", "L", "1 : N"],
  ["Payroll Period", "B", "Payroll Detail", "T", "1 : N"], ["Payroll Detail", "R", "Payslip", "L", "1 : 1"],
  ["Payroll Detail", "R", "Bank Transfer", "L", "1 : 1"],
  ["Employee", "B", "Attendance", "T", "1 : N"], ["Employee", "B", "Earnings", "T", "1 : N"],
  ["Employee", "B", "Deductions", "T", "1 : N"], ["Employee", "B", "Loan", "T", "1 : N"],
  ["Loan", "R", "Loan Repayment", "L", "1 : N"], ["Payroll Detail", "B", "Loan Repayment", "T", "1 : N"],
];

function drawER(H, s, opts = {}) {
  const { pres, C } = H;
  const fillFor = (k) => ({ core: C.accent3, master: C.accent1, input: C.background1, output: C.background1 }[k]);
  // lines first (under the boxes)
  ER_RELS.forEach(([a, sa, b, sb, lab]) => {
    const [x1, y1] = anchor(a, sa), [x2, y2] = anchor(b, sb);
    H.line(s, x1, y1, x2, y2, { color: C.accent4, width: 1.5 });
  });
  Object.entries(ER).forEach(([name, [x, y, w, kind]]) => {
    const dark = kind === "core" || kind === "master";
    s.addText(name, { isTextBox: true, x, y, w, h: ER_H, shape: pres.ShapeType.roundRect, rectRadius: 0.07,
      fill: { color: fillFor(kind) }, line: { color: kind === "output" ? C.accent2 : C.accent3, width: kind === "output" ? 1.75 : 1 },
      color: dark ? C.background1 : C.text2, bold: true, fontSize: 12, align: "center", valign: "middle", margin: 0.03 });
  });
  ER_RELS.forEach(([a, sa, b, sb, lab]) => {
    const [x1, y1] = anchor(a, sa), [x2, y2] = anchor(b, sb);
    let mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
    // keep labels clear of box edges on long diagonals
    if (a === "Payroll Detail" && b === "Loan Repayment") { mx = x1 + (x2 - x1) * 0.55; my = y1 + (y2 - y1) * 0.55; }
    s.addText(lab, { isTextBox: true, x: mx - 0.27, y: my - 0.1, w: 0.54, h: 0.2, shape: pres.ShapeType.roundRect, rectRadius: 0.05,
      fill: { color: C.background1 }, line: { color: C.accent1, width: 0.75 }, color: C.accent3, bold: true, fontSize: 9,
      align: "center", valign: "middle", margin: 0 });
  });
  if (opts.legend !== false) {
    const lx = 0.35, ly = 5.0;
    [["Core entity", C.accent3], ["Master data", C.accent1], ["Monthly input", C.background1], ["Payroll output", C.background1]].forEach(([t, col], i) => {
      s.addShape(pres.ShapeType.roundRect, { x: lx + i * 1.55, y: ly, w: 0.2, h: 0.16, rectRadius: 0.03, fill: { color: col },
        line: { color: i === 3 ? C.accent2 : C.accent3, width: i === 3 ? 1.75 : 1 } });
      H.text(s, t, { x: lx + i * 1.55 + 0.27, y: ly - 0.02, w: 1.25, h: 0.2, fontSize: 10, color: C.text1, valign: "middle" });
    });
  }
}

// ---------------------------------------------------------------- relational schema cards
const SCHEMA = {
  department: { pk: ["department_id"], cols: [["department_name", "UNIQUE"], ["location", ""]] },
  designation: { pk: ["designation_id"], cols: [["title", "UNIQUE"], ["grade_level", "CHECK 1-10"]] },
  employee: { pk: ["employee_id"], cols: [["emp_code", "UNIQUE"], ["first_name, last_name", ""], ["email", "UNIQUE"], ["date_of_joining", ""],
    ["department_id", "FK"], ["designation_id", "FK"], ["bank_name, account, ifsc", ""], ["status", "CHECK"]] },
  salary_structure: { pk: ["salary_structure_id"], cols: [["employee_id", "FK, UNIQUE"], ["basic_salary", "CHECK >0"], ["hra, da", ""], ["special_allowance", ""], ["effective_from", ""]] },
  payroll_period: { pk: ["payroll_period_id"], cols: [["period_name", "UNIQUE"], ["period_month, period_year", "UNIQUE"], ["start_date, end_date", ""], ["status", "OPEN/PROCESSED/PAID"]] },
  payroll_config: { pk: ["config_key"], cols: [["config_value", "rate / limit"], ["description", ""]] },
  attendance_summary: { pk: ["attendance_id"], cols: [["employee_id", "FK"], ["payroll_period_id", "FK"], ["working_days", ""], ["days_present", ""], ["paid_leave_days", "CHECK total"]] },
  earnings: { pk: ["earning_id"], cols: [["employee_id", "FK"], ["payroll_period_id", "FK"], ["earning_type", "CHECK"], ["amount", "CHECK >0"], ["remarks", ""]] },
  deductions: { pk: ["deduction_id"], cols: [["employee_id", "FK"], ["payroll_period_id", "FK"], ["deduction_type", ""], ["amount", "CHECK >0"], ["is_statutory", "0/1"], ["source", "MANUAL/AUTO"]] },
  loan: { pk: ["loan_id"], cols: [["employee_id", "FK"], ["loan_amount, emi_amount", "CHECK >0"], ["outstanding_balance", "CHECK"], ["start_date", ""], ["status", "ACTIVE/CLOSED"]] },
  payroll_detail: { pk: ["payroll_id"], cols: [["employee_id", "FK"], ["payroll_period_id", "FK"], ["basic, hra, da, special", ""], ["lop_days, lop_amount", ""], ["other_earnings", ""], ["gross_salary", ""], ["statutory / loan / other ded.", ""], ["total_deductions, net_salary", "CHECK >=0"]] },
  loan_repayment: { pk: ["repayment_id"], cols: [["loan_id", "FK"], ["payroll_id", "FK, NULL=manual"], ["amount", "CHECK >0"], ["repayment_date", ""], ["balance_after", ""]] },
  payslip: { pk: ["payslip_id"], cols: [["payroll_id", "FK, UNIQUE"], ["payslip_no", "UNIQUE"], ["generated_on", ""]] },
  bank_transfer: { pk: ["transfer_id"], cols: [["payroll_id", "FK, UNIQUE"], ["bank_name, account_no, ifsc", ""], ["amount", ""], ["reference_no", "UNIQUE"], ["transfer_date", ""], ["status", "PENDING/SUCCESS/FAILED"]] },
};

// draws one table card; returns nothing. cols shown at 10.5pt
function schemaCard(H, s, name, x, y, w, h) {
  const { pres, C } = H;
  const t = SCHEMA[name];
  H.card(s, x, y, w, h);
  s.addText(name, { isTextBox: true, x, y, w, h: 0.32, shape: pres.ShapeType.roundRect, rectRadius: 0.08, fill: { color: C.accent1 },
    color: C.background1, bold: true, fontSize: 12, align: "left", valign: "middle", margin: [0, 0, 0, 0.1] });
  const runs = [];
  runs.push({ text: "PK  ", options: { bold: true, color: C.accent2 } });
  runs.push({ text: t.pk[0], options: { bold: true, color: C.text2, breakLine: true } });
  t.cols.forEach(([c, tag], i) => {
    const isFk = /FK/.test(tag);
    runs.push({ text: isFk ? "FK  " : "      ", options: { bold: true, color: C.accent1 } });
    runs.push({ text: c, options: { color: C.text1 } });
    if (tag && !isFk) runs.push({ text: "  " + tag, options: { color: C.accent1, italic: true, fontSize: 9.5 } });
    else if (tag && isFk && tag !== "FK") runs.push({ text: "  " + tag.replace("FK, ", ""), options: { color: C.accent1, italic: true, fontSize: 9.5 } });
    runs.push({ text: "", options: { breakLine: i < t.cols.length - 1 } });
  });
  s.addText(runs, { isTextBox: true, x: x + 0.1, y: y + 0.4, w: w - 0.15, h: h - 0.45, fontSize: 10.5, valign: "top", margin: 0, paraSpaceAfter: 1 });
}

async function save(H, file, THEME_) {
  await H.pres.writeFile({ fileName: file });
  const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");
  await applyTheme(file, THEME_ || THEME);
}

function writeNotes(H, file, heading) {
  const md = [`# ${heading}`, "", "_Speaker notes / presentation script - one section per slide. The same text is stored in the PowerPoint speaker notes._", ""];
  H.notes.forEach((n, i) => { md.push(`## Slide ${i + 1} - ${n.title}`, "", n.text, ""); });
  fs.writeFileSync(file, md.join("\n"));
}

module.exports = { makePres, THEME, HEX, icon, drawER, schemaCard, SCHEMA, ER, save, writeNotes, ROOT, SHOTS };
