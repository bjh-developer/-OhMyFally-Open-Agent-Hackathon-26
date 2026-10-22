// Plain-language layer (design-system/MASTER.md §5). Every on-screen word for the Review tab and the mappings from
// internal terms live here. Pure functions only (no React, no icons) so they can be unit-tested.
import type { Evidence, Finding, FindingGroup, FindingStatus, Memo } from "./types";

export const DISCLAIMER = "ProcureLens points out awards worth a second look. It doesn't decide if anything is wrong.";
export const PROTOTYPE_NOTE = "Prototype for Open Agent Hackathon 2026. Not a government service.";

export const AGENCIES = ["Housing and Development Board", "People's Association", "National Parks Board"];

// ---------- Flags ----------

export interface FlagCopy {
  title: string; // plain reason, used as the card title
  check: string; // label in "Choose which checks to run"
  hint: string; // one line under the check label
}

export const FLAG_COPY: Record<string, FlagCopy> = {
  R1: { title: "Registered shortly before the award", check: "Registered shortly before the award", hint: "The company was set up less than 6 months before it won." },
  R2: { title: "Supplier no longer active", check: "Supplier no longer active", hint: "The company registry shows it as struck off or closed." },
  R3: { title: "Shares an address with another supplier", check: "Shares an address with another supplier", hint: "Two or more winners are registered at the same address." },
  R4: { title: "Several awards just under the approval limit", check: "Several awards just under the approval limit", hint: "Smaller awards to one supplier that add up to more than the limit." },
  R5: { title: "Business type doesn't match the purchase", check: "Business type doesn't match the purchase", hint: "The company's registered activity looks unrelated to what was bought." },
  R6: { title: "One supplier wins most awards", check: "One supplier wins most awards", hint: "A single supplier takes most of the awards in a category." },
  R7: { title: "Supplier changed its name", check: "Supplier changed its name", hint: "The company has used other names before." },
  R8: { title: "Not found in the company registry", check: "Not found in the company registry", hint: "A local-looking supplier has no match in the registry." },
  R9: { title: "Winner wasn't the top-scored bid", check: "Winner wasn't the top-scored bid", hint: "Another bid scored higher under the published criteria." },
};

export const CHECK_IDS = ["R1", "R2", "R3", "R4", "R8"];

export const flagTitle = (id: string) => FLAG_COPY[id]?.title ?? "Worth a second look";

// ---------- Status ----------

export type StatusKey = FindingStatus | "confirmed" | "dismissed";
export type Tone = "warning" | "muted" | "success";

export const STATUS_COPY: Record<StatusKey, { label: string; tone: Tone }> = {
  escalated: { label: "Needs your decision", tone: "warning" },
  accepted: { label: "Flagged for review", tone: "muted" },
  suppressed: { label: "Cleared earlier", tone: "muted" },
  rejected: { label: "Set aside: not enough evidence", tone: "muted" },
  confirmed: { label: "Confirmed", tone: "success" },
  dismissed: { label: "Dismissed", tone: "muted" },
};

export const SECTION_COPY: Record<FindingStatus, { title: string; empty: string }> = {
  escalated: { title: "Needs your decision", empty: "Nothing needs your decision." },
  accepted: { title: "Flagged for review", empty: "No other items were flagged." },
  suppressed: { title: "Cleared earlier", empty: "" },
  rejected: { title: "Set aside: not enough evidence", empty: "" },
};

// ---------- Strength ----------

export type Strength = "High" | "Medium" | "Low";
export const strengthOf = (confidence: number): Strength => (confidence >= 0.75 ? "High" : confidence >= 0.5 ? "Medium" : "Low");
export const strengthRank = (s: Strength) => (s === "High" ? 3 : s === "Medium" ? 2 : 1);
export const STRENGTH_TIP = "How strongly the records support this";

// ---------- Formatting ----------

const money = new Intl.NumberFormat("en-SG", { maximumFractionDigits: 0 });
export function formatMoney(v: number | string | null | undefined): string {
  if (v == null || v === "") return "";
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? `${n < 0 ? "-" : ""}S$${money.format(Math.abs(n))}` : "";
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
// "2025-06-20" -> "20 Jun 2025". Done by hand so the time zone can't shift the day.
export function formatDate(iso: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso ?? "");
  if (!m) return iso ?? "";
  return `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}`;
}

export function formatPeriod(from: string, to: string): string {
  return `${formatDate(from)} to ${formatDate(to)}`;
}

export function formatDuration(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

const NUM_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"];
const numWord = (n: number) => NUM_WORDS[n] ?? String(n);
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

function spanOf(days: number): string {
  if (days < 14) return `${Math.max(1, days)} ${days === 1 ? "day" : "days"}`;
  if (days < 70) return `${Math.round(days / 7)} weeks`;
  const months = Math.round(days / 30.4);
  return `${months} months`;
}

const joinAnd = (xs: string[]) => (xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`);
const dayDiff = (a: string, b: string) => Math.round((Date.parse(b) - Date.parse(a)) / 86_400_000);

// ---------- Why flagged ----------

const num = (v: unknown): number | null => {
  const n = typeof v === "number" ? v : typeof v === "string" && v.trim() !== "" ? Number(v) : NaN;
  return Number.isFinite(n) ? n : null;
};

function r4Rows(f: Finding): { amt: number; date: string }[] {
  const ev: Evidence | undefined = f.evidence[f.evidence.length - 1];
  if (!ev) return [];
  return ev.rows
    .filter((r) => !r.supplier_name || r.supplier_name === f.supplier_name)
    .map((r) => ({ amt: num(r.awarded_amt), date: String(r.award_date ?? "") }))
    .filter((r): r is { amt: number; date: string } => r.amt != null && /^\d{4}-\d{2}-\d{2}/.test(r.date))
    .sort((a, b) => a.date.localeCompare(b.date));
}

// One sentence, under 20 words, built only from fields the finding really has.
export function whyFlagged(f: Finding): string {
  const amt = formatMoney(f.awarded_amt);
  switch (f.flag_id) {
    case "R1": {
      let days: number | null = null;
      const months = num(f.metric_value);
      if (f.metric_name === "months_since_incorporation" && months != null) days = Math.round(months * 30.4);
      const d = /Incorporated (\d{4}-\d{2}-\d{2}); awarded (\d{4}-\d{2}-\d{2})/.exec(f.detail ?? "");
      if (d) days = dayDiff(d[1], d[2]);
      const lead = amt ? `Awarded ${amt}` : "Awarded";
      if (days == null || days < 0) return `${lead} shortly after the company was registered.`;
      if (days < 7) return `${lead} just days after the company was registered.`;
      return `${lead} about ${spanOf(days)} after the company was registered.`;
    }
    case "R2": {
      const st = f.metric_name === "entity_status" ? String(f.metric_value ?? "").toLowerCase() : "";
      return st && !st.includes("live") ? `The company registry now lists this supplier as ${st}.` : "The company registry no longer shows this supplier as active.";
    }
    case "R3": {
      const n = num(f.metric_value);
      return n && n >= 2 ? `Shares a registered address with ${numWord(n - 1)} other winning ${n - 1 === 1 ? "supplier" : "suppliers"}.` : "Shares a registered address with another winning supplier.";
    }
    case "R4": {
      const rows = r4Rows(f);
      const limit = num(f.threshold);
      const limitText = limit ? `the ${formatMoney(limit)} tender limit` : "the tender limit";
      if (rows.length >= 2) {
        const days = dayDiff(rows[0].date, rows[rows.length - 1].date);
        const list = rows.length <= 3 ? joinAnd(rows.map((r) => formatMoney(r.amt))) : formatMoney(rows.reduce((t, r) => t + r.amt, 0)) + " in total";
        const head = rows.length <= 3 ? `${cap(numWord(rows.length))} awards of ${list}` : `${rows.length} awards, ${list},`;
        return `${head} within ${spanOf(days)}: together over ${limitText}.`;
      }
      const total = num(f.metric_value);
      return total ? `Awards to this supplier within 90 days total ${formatMoney(total)}, over ${limitText}.` : `Several awards to this supplier within 90 days add up to more than ${limitText}.`;
    }
    case "R5":
      return "The company's registered business looks unrelated to what was bought.";
    case "R6":
      return "One supplier received most of the awards in this category.";
    case "R7":
      return "This supplier has used other company names before.";
    case "R8":
      return "We couldn't find this supplier in the company registry.";
    case "R9":
      return "The winning bid wasn't the top-scored one under the published criteria.";
    default:
      return flagTitle(f.flag_id) + ".";
  }
}

// ---------- Groups (R3 shared address) ----------

export function groupTitle(g: FindingGroup): string {
  g = { ...g, title: g.title.replace(/\s*#na-na/gi, "") };
  const m = /^(\d+) winning suppliers share (.+)$/.exec(g.title);
  return m ? `${m[1]} suppliers share ${m[2]}` : g.title.replace("winning suppliers", "suppliers");
}

export interface Item {
  id: string;
  kind: "finding" | "group";
  status: FindingStatus;
  flag_id: string;
  finding: Finding; // the finding itself, or the first of the group (the sheet opens on it)
  members: Finding[];
  group?: FindingGroup;
  supplierLabel: string;
  amount: number | null;
  date: string | null;
  confidence: number;
}

// Turn memo.findings + memo.groups into display items: a group is one item, every other finding is its own.
export function buildItems(memo: Memo): Item[] {
  const byId = new Map(memo.findings.map((f) => [f.finding_id, f]));
  const grouped = new Set<string>();
  const items: Item[] = [];
  for (const g of memo.groups ?? []) {
    const members = g.finding_ids.map((id) => byId.get(id)).filter((f): f is Finding => !!f);
    if (members.length === 0) continue;
    members.forEach((m) => grouped.add(m.finding_id));
    const dates = members.map((m) => m.award_date).filter((d): d is string => !!d).sort();
    items.push({
      id: g.group_id,
      kind: "group",
      status: g.status,
      flag_id: g.flag_id,
      finding: members[0],
      members,
      group: g,
      supplierLabel: g.suppliers.length > 1 ? `${g.suppliers[0]} and ${g.suppliers.length - 1} more` : g.suppliers[0] ?? members[0].supplier_name,
      amount: g.total_amt || null,
      date: dates[0] ?? null,
      confidence: Math.max(...members.map((m) => m.confidence)),
    });
  }
  for (const f of memo.findings) {
    if (grouped.has(f.finding_id)) continue;
    items.push({
      id: f.finding_id,
      kind: "finding",
      status: f.status,
      flag_id: f.flag_id,
      finding: f,
      members: [f],
      supplierLabel: f.supplier_name,
      amount: f.awarded_amt ?? null,
      date: f.award_date ?? null,
      confidence: f.confidence,
    });
  }
  return items;
}

// ---------- Summary numbers ----------

export interface Summary {
  worth: number;
  needDecision: number;
  cleared: number;
  setAside: number;
  value: number | null;
  byFlag: { flag_id: string; count: number; amount: number }[];
}

export function summarise(items: Item[]): Summary {
  const shown = items.filter((i) => i.status === "accepted" || i.status === "escalated");
  const amountOf = (i: Item) => (i.kind === "group" ? i.members.reduce((t, m) => t + (m.awarded_amt ?? 0), 0) || (i.amount ?? 0) : i.amount ?? 0);
  const total = shown.reduce((t, i) => t + amountOf(i), 0);
  const flags = new Map<string, { count: number; amount: number }>();
  for (const i of shown) {
    const cur = flags.get(i.flag_id) ?? { count: 0, amount: 0 };
    cur.count += 1;
    cur.amount += amountOf(i);
    flags.set(i.flag_id, cur);
  }
  return {
    worth: shown.length,
    needDecision: items.filter((i) => i.status === "escalated").length,
    cleared: items.filter((i) => i.status === "suppressed").length,
    setAside: items.filter((i) => i.status === "rejected").length,
    value: shown.some((i) => amountOf(i) > 0) ? total : null,
    byFlag: [...flags.entries()].map(([flag_id, v]) => ({ flag_id, ...v })).sort((a, b) => b.count - a.count || b.amount - a.amount),
  };
}

export function headline(agency: string, s: Summary): string {
  if (s.worth === 0) return `No awards at ${agency} need a second look.`;
  const first = `${s.worth} ${s.worth === 1 ? "item" : "items"} worth a second look at ${agency}.`;
  const second = s.needDecision === 0 ? "" : s.needDecision === 1 ? " 1 needs your decision." : ` ${s.needDecision} need your decision.`;
  return first + second;
}

// "Most items are shared addresses (7 of 12)." / "Most of the money is in ..."
export function reasonSummary(s: Summary): string {
  const top = s.byFlag[0];
  if (!top) return "";
  const share = `${top.count} of ${s.worth}`;
  return top.count * 2 > s.worth ? `Most items are "${flagTitle(top.flag_id).toLowerCase()}" (${share}).` : `The most common reason is "${flagTitle(top.flag_id).toLowerCase()}" (${share}).`;
}

export function moneySummary(s: Summary): string {
  const top = [...s.byFlag].sort((a, b) => b.amount - a.amount)[0];
  if (!top || !s.value) return "";
  const pct = Math.round((top.amount / s.value) * 100);
  return `${pct}% of the value (${formatMoney(top.amount)}) is in "${flagTitle(top.flag_id).toLowerCase()}".`;
}

// ---------- Evidence table wording ----------

const COLUMN_LABELS: Record<string, string> = {
  flag_id: "Check",
  tender_no: "Tender reference",
  agency: "Agency",
  supplier_name: "Supplier",
  uen: "Company registration no.",
  award_date: "Award date",
  awarded_amt: "Amount",
  metric_name: "Measure",
  metric_value: "Value",
  threshold: "Limit",
  detail: "Note",
  entity_status: "Registry status",
  registration_incorporation_date: "Registered on",
};

export function friendlyColumn(name: string): string {
  if (COLUMN_LABELS[name]) return COLUMN_LABELS[name];
  const s = name.replace(/_/g, " ").trim();
  return s ? cap(s) : name;
}

export function friendlyCell(column: string, v: unknown): string {
  if (v == null || v === "") return "–";
  if (column === "awarded_amt" || column === "total_amt") return formatMoney(num(v)) || String(v);
  if (/_date$/.test(column)) return formatDate(String(v));
  return String(v);
}

export function isMoneyColumn(c: string) {
  return c === "awarded_amt" || c === "total_amt";
}

const SOURCE_NAMES: [RegExp, string][] = [
  [/awards$/i, "GeBIZ awards"],
  [/entities$/i, "ACRA company registry"],
  [/supplier_xwalk$/i, "Supplier-to-registry matches"],
  [/ago_chunks$/i, "Auditor-General report excerpts"],
  [/rules$/i, "Check rules"],
  [/^internal_pg\./i, "Agency internal records"],
];

export function sourceName(obj: string): string {
  return SOURCE_NAMES.find(([re]) => re.test(obj))?.[1] ?? obj;
}

// ---------- Notes -> plain bullets ----------

// The pipeline's notes mention agents and scores. Reword the known patterns, drop what we can't explain simply.
export function plainNotes(notes: string[] | undefined): string[] {
  const out: string[] = [];
  for (const raw of notes ?? []) {
    let n = raw.trim();
    if (!n) continue;
    n = n
      .replace(/Escalated by RiskAgent: R5 findings always go to a human\./, "This kind of check always needs a person to decide.")
      .replace(/Critic sent this back once: first count was (\d+) rows?, re-run returned (\d+)\./, "We re-checked this once. The first count was $1 records; the second was $2.")
      .replace(/Registry match was fuzzy \(([\d.]+)\), so confidence is capped at ([\d.]+)\./, (_m, _a, b) => `The company name only partly matched the registry, so we're less sure (${Math.round(Number(b) * 100)}%).`)
      .replace(/\bCriticAgent\b|\bCritic\b/g, "the double-check")
      .replace(/\bRiskAgent\b|\bAnalystAgent\b|\bResolverAgent\b|\bPlannerAgent\b|\bReporterAgent\b/g, "the review")
      .replace(/H-MEM/g, "your past decisions")
      .replace(/\bUEN\b/g, "company registration no.");
    out.push(n);
  }
  return out.slice(0, 3);
}

// ---------- AGO excerpt relevance ----------

// Only these excerpts say something about the reason. Anything else is hidden, never shown as filler.
export const AGO_FOR_FLAG: Record<string, string[]> = {
  R2: ["ago-fy2223-pa-debarred"],
  R4: ["ago-fy2122-irregular-quotations", "ago-fy2122-procurement-overview"],
  R6: ["ago-fy2122-procurement-overview", "ago-fy2122-wog-pcfa-spread"],
  R9: ["ago-fy2425-edb-evaluation", "ago-fy2425-mpa-scoring", "ago-fy2324-sportsg-evaluation", "ago-fy2223-mci-panel"],
};

export function relevantAgoRefs(flagId: string, refs: string[]): string[] {
  const ok = AGO_FOR_FLAG[flagId] ?? [];
  return refs.filter((r) => ok.includes(r));
}

// At most two sentences.
export function firstSentences(text: string, n = 2): string {
  const parts = text.replace(/^\d+\.\s*/, "").match(/[^.!?]+(?:\.\d+)?[.!?]+(?:\s|$)/g) ?? [text];
  return parts.slice(0, n).join("").trim();
}

// ---------- Decisions ----------

export const PATTERN_TAGS: { value: string; label: string }[] = [
  { value: "framework_contract", label: "Framework or panel contract" },
  { value: "shared_office", label: "Shared office building" },
  { value: "known_supplier", label: "Known, legitimate supplier" },
  { value: "", label: "Something else" },
];

// ---------- Loading steps ----------

export const STEPS = [
  { label: "Checking your request", agents: ["GateAgent"] },
  { label: "Planning the checks", agents: ["PlannerAgent"] },
  { label: "Matching suppliers to the company registry", agents: ["ResolverAgent"] },
  { label: "Running the checks", agents: ["AnalystAgent"] },
  { label: "Double-checking the results", agents: ["CriticAgent", "RiskAgent"] },
  { label: "Writing your summary", agents: ["ReporterAgent"] },
] as const;

export type StepState = "pending" | "active" | "done";

export function stepIndexFor(agent: string): number {
  return STEPS.findIndex((s) => (s.agents as readonly string[]).includes(agent));
}

// The furthest step any event has reached is the active one; everything before it is done. A retry that sends work
// back (Critic -> Analyst) never moves the stepper backwards.
export function stepStates(agentNames: string[], finished: boolean): StepState[] {
  const reached = Math.max(-1, ...agentNames.map(stepIndexFor));
  return STEPS.map((_, i) => (finished || i < reached ? "done" : i === reached ? "active" : "pending"));
}
