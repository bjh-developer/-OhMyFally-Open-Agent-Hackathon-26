import { FLAG_NAMES } from "./status";
import type { Memo } from "./types";

// Fallback when the API's memo.markdown is empty. The API's own rendering wins when present.
export function memoToMarkdown(memo: Memo): string {
  if (memo.markdown?.trim()) return memo.markdown;
  const L: string[] = [
    `# Procurement review memo: ${memo.agency}`,
    "",
    `Period: ${memo.date_from} to ${memo.date_to}  `,
    `Run: ${memo.run_id}`,
    "",
    `> ${memo.disclaimer}`,
    "",
    "## Summary",
    memo.summary,
    "",
    "## Findings",
  ];
  memo.findings.forEach((f, i) => {
    L.push(
      "",
      `### ${i + 1}. ${f.flag_id} ${FLAG_NAMES[f.flag_id] ?? ""}: ${f.supplier_name} (${f.status})`,
      "",
      `- Tender: ${f.tender_no}`,
      `- UEN: ${f.uen ?? "unresolved"}`,
      `- Confidence: ${Math.round(f.confidence * 100)}%`,
      "",
      f.summary
    );
    if (f.metric_name) L.push("", `Metric: ${f.metric_name} = ${f.metric_value} (threshold ${f.threshold})`);
    if (f.evidence.length) L.push("", "Evidence:", ...f.evidence.map((e) => `- Zetaris query \`${e.query_id}\` returned ${e.row_count} row(s)`));
    if (f.ago_refs.length) L.push("", `AGO references: ${f.ago_refs.join(", ")}`);
    if (f.memory_refs.length) L.push("", `H-MEM references: ${f.memory_refs.join(", ")}`);
  });
  if (memo.limitations.length) L.push("", "## Limitations", ...memo.limitations.map((x) => `- ${x}`));
  return L.join("\n") + "\n";
}

export function downloadText(filename: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/markdown;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
