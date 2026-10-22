"use client";

import { BookOpen, Brain, Check, FileSearch, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FLAG_NAMES, findingLabel, findingTone } from "@/lib/status";
import { fmtMoney } from "@/lib/utils";
import type { DecisionRecord, Finding } from "@/lib/types";

export function DecisionActions({
  finding,
  decision,
  onDecide,
}: {
  finding: Finding;
  decision?: DecisionRecord;
  onDecide: (f: Finding, kind: "confirm" | "dismiss") => void;
}) {
  const noUen = !finding.uen;
  const why = noUen ? "No UEN: H-MEM recalls decisions by UEN, flag and agency, so this one could not be remembered." : undefined;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button size="sm" variant="ok" disabled={noUen} title={why} onClick={() => onDecide(finding, "confirm")}>
        <Check size={14} /> Confirm
      </Button>
      <Button size="sm" variant="danger" disabled={noUen} title={why} onClick={() => onDecide(finding, "dismiss")}>
        <X size={14} /> Dismiss
      </Button>
      {decision && (
        <Badge tone={decision.decision === "confirm" ? "ok" : "neutral"} title={decision.reason}>
          <Brain size={11} /> {decision.decision === "confirm" ? "Confirmed" : "Dismissed"} · {decision.memoryId}
        </Badge>
      )}
      {noUen && <span className="text-xs text-muted">No UEN, so it cannot be remembered.</span>}
    </div>
  );
}

export function FindingCard({
  rank,
  finding: f,
  decision,
  onOpen,
  onDecide,
}: {
  rank: number;
  finding: Finding;
  decision?: DecisionRecord;
  onOpen: (f: Finding) => void;
  onDecide: (f: Finding, kind: "confirm" | "dismiss") => void;
}) {
  const pct = Math.round(f.confidence * 100);
  return (
    <article className={`rounded-xl border border-border bg-surface p-4 ${f.status === "suppressed" ? "opacity-80" : ""}`}>
      <header className="flex flex-wrap items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-surface-2 text-xs font-semibold text-muted">{rank}</span>
        <Badge tone="info">{f.flag_id}</Badge>
        <h3 className="font-semibold">{FLAG_NAMES[f.flag_id] ?? f.flag_id}</h3>
        <Badge tone={findingTone[f.status]} className="ml-auto">
          {findingLabel[f.status]}
        </Badge>
      </header>

      <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-sm md:grid-cols-4">
        <div>
          <dt className="text-xs text-muted">Supplier</dt>
          <dd className="font-medium break-words">{f.supplier_name}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">UEN</dt>
          <dd className="font-mono">{f.uen ?? "unresolved"}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Tender</dt>
          <dd className="font-mono break-all">{f.tender_no}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Award</dt>
          <dd>
            {fmtMoney(f.awarded_amt)} {f.award_date ? `· ${f.award_date}` : ""}
          </dd>
        </div>
      </dl>

      <p className="mt-3 text-sm leading-relaxed">{f.summary}</p>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted">
        <span className="flex items-center gap-2">
          Confidence
          <span className="h-1.5 w-24 overflow-hidden rounded-full bg-surface-2" role="img" aria-label={`${pct}% confidence`}>
            <span className="block h-full rounded-full bg-accent" style={{ width: `${pct}%` }} />
          </span>
          <span className="font-medium text-fg">{pct}%</span>
        </span>
        {f.metric_name && (
          <span>
            {f.metric_name}: <span className="font-mono text-fg">{f.metric_value}</span> (threshold <span className="font-mono">{f.threshold}</span>)
          </span>
        )}
        {f.ago_refs.length > 0 && (
          <span className="inline-flex items-center gap-1">
            <BookOpen size={12} /> {f.ago_refs.length} AGO ref{f.ago_refs.length > 1 ? "s" : ""}
          </span>
        )}
        {f.memory_refs.length > 0 && (
          <span className="inline-flex items-center gap-1 text-info">
            <Brain size={12} /> memory {f.memory_refs.join(", ")}
          </span>
        )}
      </div>

      {f.notes && f.notes.length > 0 && (
        <ul className="mt-2 list-disc pl-5 text-xs text-muted">
          {f.notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      )}

      <footer className="mt-4 flex flex-wrap items-center gap-3 border-t border-border pt-3">
        <Button size="sm" variant="outline" onClick={() => onOpen(f)}>
          <FileSearch size={14} /> Evidence
        </Button>
        {f.status !== "rejected" && <DecisionActions finding={f} decision={decision} onDecide={onDecide} />}
      </footer>
    </article>
  );
}
