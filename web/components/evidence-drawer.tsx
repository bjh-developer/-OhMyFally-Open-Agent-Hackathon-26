"use client";

import { Brain, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogDescription, DialogTitle, SheetContent } from "@/components/ui/dialog";
import { agoChunk } from "@/lib/ago";
import { FLAG_NAMES, findingLabel, findingTone } from "@/lib/status";
import type { DecisionRecord, Evidence, Finding } from "@/lib/types";

function RowsTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (rows.length === 0) return <p className="text-xs text-muted">No rows returned.</p>;
  const cols = [...new Set(rows.flatMap((r) => Object.keys(r)))];
  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full text-left text-xs">
        <thead className="bg-surface-2 text-muted">
          <tr>
            {cols.map((c) => (
              <th key={c} className="px-2 py-1.5 font-medium whitespace-nowrap">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-border">
              {cols.map((c) => (
                <td key={c} className="px-2 py-1.5 font-mono whitespace-nowrap">
                  {r[c] == null ? "–" : String(r[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EvidenceBlock({ e, n }: { e: Evidence; n: number }) {
  return (
    <section className="grid gap-2 rounded-lg border border-border p-3">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-semibold">Query {n}</span>
        <Badge>{e.row_count} row{e.row_count === 1 ? "" : "s"}</Badge>
        {e.rows.length < e.row_count && <Badge tone="warn">showing first {e.rows.length}</Badge>}
      </div>
      <p className="text-xs text-muted">
        Zetaris <span className="text-fg">query_id</span> <span className="font-mono text-fg select-all">{e.query_id}</span>
      </p>
      {e.source_objects.length > 0 && (
        <p className="flex flex-wrap gap-1 text-xs text-muted">
          Sources: {e.source_objects.map((s) => <Badge key={s} tone="info" className="font-mono">{s}</Badge>)}
        </p>
      )}
      <pre className="max-h-64 overflow-auto rounded-md bg-surface-2 p-3 font-mono text-xs leading-relaxed whitespace-pre-wrap">{e.sql}</pre>
      <RowsTable rows={e.rows} />
    </section>
  );
}

export function EvidenceDrawer({
  finding: f,
  decision,
  onClose,
}: {
  finding: Finding | null;
  decision?: DecisionRecord;
  onClose: () => void;
}) {
  return (
    <Dialog open={!!f} onOpenChange={(o) => !o && onClose()}>
      {f && (
        <SheetContent aria-describedby="evidence-desc">
          <div className="grid gap-5 p-6 pt-12">
            <header className="grid gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="info">{f.flag_id}</Badge>
                <Badge tone={findingTone[f.status]}>{findingLabel[f.status]}</Badge>
                {decision && (
                  <Badge tone={decision.decision === "confirm" ? "ok" : "neutral"}>
                    <Brain size={11} /> {decision.decision === "confirm" ? "Confirmed" : "Dismissed"}
                  </Badge>
                )}
              </div>
              <DialogTitle className="text-lg font-semibold">
                {FLAG_NAMES[f.flag_id] ?? f.flag_id}: {f.supplier_name}
              </DialogTitle>
              <DialogDescription id="evidence-desc" className="text-sm leading-relaxed">
                {f.summary}
              </DialogDescription>
              <p className="text-xs text-muted">
                <span className="font-mono">{f.tender_no}</span> · {f.agency} · UEN <span className="font-mono">{f.uen ?? "unresolved"}</span>
                {f.detail ? ` · ${f.detail}` : ""}
              </p>
            </header>

            <section className="grid gap-3">
              <h3 className="text-sm font-semibold">Evidence from Zetaris ({f.evidence.length})</h3>
              {f.evidence.length === 0 && <p className="text-sm text-muted">No query evidence was attached to this finding.</p>}
              {f.evidence.map((e, i) => (
                <EvidenceBlock key={`${e.query_id}-${i}`} e={e} n={i + 1} />
              ))}
            </section>

            <section className="grid gap-3">
              <h3 className="text-sm font-semibold">Auditor-General references ({f.ago_refs.length})</h3>
              {f.ago_refs.length === 0 && <p className="text-sm text-muted">No AGO excerpt was cited for this finding.</p>}
              {f.ago_refs.map((id) => {
                const c = agoChunk(id);
                if (!c) {
                  return (
                    <p key={id} className="font-mono text-xs text-muted">
                      {id} (excerpt not bundled in this UI)
                    </p>
                  );
                }
                return (
                  <figure key={id} className="grid gap-1 rounded-lg border border-border p-3">
                    <figcaption className="flex flex-wrap items-center gap-2 text-xs">
                      <Badge tone="info">{c.fy}</Badge>
                      <span className="text-muted">{c.section}</span>
                      <a href={c.url} target="_blank" rel="noreferrer" className="ml-auto inline-flex items-center gap-1 text-accent hover:underline">
                        p. {c.page} <ExternalLink size={11} />
                      </a>
                    </figcaption>
                    <blockquote className="max-h-40 overflow-auto text-xs leading-relaxed text-muted">{c.text}</blockquote>
                    <p className="font-mono text-[11px] text-muted">{id}</p>
                  </figure>
                );
              })}
            </section>

            <section className="grid gap-2">
              <h3 className="text-sm font-semibold">Auditor memory (H-MEM) ({f.memory_refs.length})</h3>
              {f.memory_refs.length === 0 ? (
                <p className="text-sm text-muted">No earlier auditor decision matched this finding.</p>
              ) : (
                <p className="text-sm">
                  This finding cites {f.memory_refs.map((m) => <Badge key={m} tone="info" className="mx-0.5 font-mono">{m}</Badge>)}
                  {f.status === "suppressed" ? " from an earlier auditor dismissal, so it was suppressed." : "."}
                </p>
              )}
              {decision && (
                <p className="rounded-md bg-surface-2 p-3 text-xs">
                  Your decision just now: <strong>{decision.decision}</strong> ({decision.scope}) · memory{" "}
                  <span className="font-mono">{decision.memoryId}</span>
                  <br />
                  Reason: {decision.reason}
                  {decision.pattern_tag ? ` · pattern ${decision.pattern_tag}` : ""}
                </p>
              )}
            </section>
          </div>
        </SheetContent>
      )}
    </Dialog>
  );
}
