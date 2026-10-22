import { SECTION_COPY, STATUS_COPY, buildItems, flagTitle, formatDate, formatMoney, formatPeriod, headline, strengthOf, summarise, whyFlagged, DISCLAIMER } from "./copy";
import type { Memo, TraceEvent } from "./types";

// Plain-language summary for the Review tab's "Download summary".
export function summaryMarkdown(memo: Memo): string {
  const items = buildItems(memo);
  const s = summarise(items);
  const L = [`# Review of ${memo.agency}`, "", `Period: ${formatPeriod(memo.date_from, memo.date_to)}`, "", headline(memo.agency, s)];
  if (s.value != null) L.push("", `Value involved: ${formatMoney(s.value)}`);
  for (const st of ["escalated", "accepted", "suppressed", "rejected"] as const) {
    const rows = items.filter((i) => i.status === st);
    if (!rows.length) continue;
    L.push("", `## ${SECTION_COPY[st].title} (${rows.length})`);
    for (const i of rows) {
      const why = i.kind === "group" && i.group ? i.group.title : whyFlagged(i.finding);
      L.push("", `### ${flagTitle(i.flag_id)}`, "", `- Supplier: ${i.supplierLabel}`);
      if (i.amount != null) L.push(`- Amount: ${formatMoney(i.amount)}`);
      if (i.date) L.push(`- Award date: ${formatDate(i.date)}`);
      L.push(`- Strength: ${strengthOf(i.confidence)}`, `- Status: ${STATUS_COPY[i.status].label}`, "", why);
    }
  }
  if (memo.limitations.length) L.push("", "## Things to keep in mind", ...memo.limitations.map((x) => `- ${x}`));
  L.push("", "---", DISCLAIMER, "");
  return L.join("\n");
}

// Technical memo: the API's own markdown (with queries and receipts) when present.
export function technicalMarkdown(memo: Memo): string {
  if (memo.markdown?.trim()) return memo.markdown;
  const L = [`# Technical memo: ${memo.agency}`, "", `Run: ${memo.run_id}`, "", memo.summary, ""];
  for (const f of memo.findings) {
    L.push(`## ${f.finding_id} ${f.flag_id} ${f.supplier_name} (${f.status})`, "", `- Tender: ${f.tender_no}`, `- UEN: ${f.uen ?? "unresolved"}`, `- Confidence: ${f.confidence}`);
    for (const e of f.evidence) L.push(`- Zetaris query ${e.query_id}: ${e.row_count} row(s)`);
    if (f.memory_refs.length) L.push(`- H-MEM: ${f.memory_refs.join(", ")}`);
    L.push("");
  }
  return L.join("\n");
}

export const traceJsonl = (events: TraceEvent[]) => events.map((e) => JSON.stringify(e)).join("\n") + "\n";

export function downloadText(filename: string, text: string, type = "text/markdown;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
