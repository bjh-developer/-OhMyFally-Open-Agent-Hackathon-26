"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DecisionActions } from "@/components/finding-card";
import { FLAG_NAMES } from "@/lib/status";
import { fmtMoney } from "@/lib/utils";
import type { DecisionRecord, Finding } from "@/lib/types";
import { FileSearch } from "lucide-react";

// Escalated findings wait here for a human; a decision moves them to "decided".
export function ReviewQueue({
  findings,
  decisions,
  onOpen,
  onDecide,
}: {
  findings: Finding[];
  decisions: Record<string, DecisionRecord>;
  onOpen: (f: Finding) => void;
  onDecide: (f: Finding, kind: "confirm" | "dismiss") => void;
}) {
  const pending = findings.filter((f) => !decisions[f.finding_id]);
  const decided = findings.filter((f) => decisions[f.finding_id]);

  if (findings.length === 0) {
    return <p className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted">Nothing was escalated for human review in this run.</p>;
  }

  const row = (f: Finding) => (
    <li key={f.finding_id} className="rounded-xl border border-border bg-surface p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="info">{f.flag_id}</Badge>
        <span className="font-semibold">{FLAG_NAMES[f.flag_id] ?? f.flag_id}</span>
        <span className="ml-auto text-xs text-muted">confidence {Math.round(f.confidence * 100)}%</span>
      </div>
      <p className="mt-1 text-sm font-medium">{f.supplier_name}</p>
      <p className="text-xs text-muted">
        <span className="font-mono">{f.tender_no}</span> · {fmtMoney(f.awarded_amt)}
      </p>
      <p className="mt-2 text-sm">{f.summary}</p>
      {f.notes && f.notes.length > 0 && <p className="mt-1 text-xs text-muted">{f.notes.join(" ")}</p>}
      <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-border pt-3">
        <Button size="sm" variant="outline" onClick={() => onOpen(f)}>
          <FileSearch size={14} /> Evidence
        </Button>
        <DecisionActions finding={f} decision={decisions[f.finding_id]} onDecide={onDecide} />
      </div>
    </li>
  );

  return (
    <div className="grid gap-3">
      <h2 className="text-sm font-semibold">Waiting for review ({pending.length})</h2>
      {pending.length === 0 && <p className="text-sm text-muted">All escalated items have a decision.</p>}
      <ul className="grid gap-3">{pending.map(row)}</ul>
      {decided.length > 0 && (
        <>
          <h2 className="mt-2 text-sm font-semibold text-muted">Decided ({decided.length})</h2>
          <ul className="grid gap-3 opacity-80">{decided.map(row)}</ul>
        </>
      )}
    </div>
  );
}
