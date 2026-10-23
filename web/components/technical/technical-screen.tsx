"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ArrowRight, Download, RotateCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { CopyButton } from "@/components/technical/copy-button";
import { BehaviourPanel } from "@/components/technical/behaviour-panel";
import { AgentDiagram } from "@/components/technical/agent-diagram";
import { H1 } from "@/components/review/review-screen";
import { formatDuration } from "@/lib/copy";
import { downloadText, technicalMarkdown, traceJsonl } from "@/lib/report-md";
import type { TraceEvent, TraceStatus } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useRunCtx } from "@/components/run-provider";

const KEY: TraceStatus[] = ["needs_revision", "retrying", "escalated", "failed"];

const rowStyle: Record<TraceStatus, string> = {
  success: "border-l-border",
  needs_revision: "border-l-warning",
  retrying: "border-l-warning",
  escalated: "border-l-warning",
  partial_success: "border-l-chart-4",
  failed: "border-l-destructive",
};

const statusVariant = (s: TraceStatus) => (s === "success" ? "success" : s === "failed" ? "destructive" : s === "partial_success" ? "muted" : "warning") as "success" | "destructive" | "muted" | "warning";

const clock = (iso: string) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleTimeString("en-GB");
};

function IdChip({ id, label }: { id: string; label: string }) {
  return (
    <span className="inline-flex max-w-full items-center rounded-lg bg-muted pl-2 font-mono text-sm">
      <span className="truncate">{label} {id}</span>
      <CopyButton value={id} label={label} />
    </span>
  );
}

function Line({ ev }: { ev: TraceEvent }) {
  const receipts = ev.meterless_receipt_ids?.length ? ev.meterless_receipt_ids : ev.meterless_receipt_id ? [ev.meterless_receipt_id] : [];
  return (
    <li className={cn("grid gap-1 border border-l-4 border-border bg-card px-4 py-3", rowStyle[ev.status])}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="font-mono text-sm text-muted-foreground">{clock(ev.timestamp)}</span>
        <span className="text-base font-semibold">{ev.agent_name}</span>
        <span className="font-mono text-sm break-all">{ev.action}</span>
        {ev.target_agent && <span className="inline-flex items-center gap-1 text-sm text-muted-foreground"><ArrowRight aria-hidden size={16} strokeWidth={1.75} /> {ev.target_agent}</span>}
        <span className="ml-auto flex items-center gap-2">
          {!!ev.retry_count && <Badge variant="warning"><RotateCw aria-hidden strokeWidth={1.75} />Retry {ev.retry_count}</Badge>}
          <Badge variant={statusVariant(ev.status)}>{ev.status.replace("_", " ")}</Badge>
        </span>
      </div>
      {ev.output_summary && <p className="text-base break-words">{ev.output_summary}</p>}
      {ev.input_summary && <p className="line-clamp-2 text-sm break-words text-muted-foreground">{ev.input_summary}</p>}
      {(ev.zetaris_query_ids?.length || receipts.length || ev.confidence != null || ev.routed_model) && (
        <div className="flex flex-wrap items-center gap-2">
          {ev.confidence != null && <Badge variant="muted">Confidence {Math.round(ev.confidence * 100)}%</Badge>}
          {ev.zetaris_query_ids?.map((q) => <IdChip key={q} id={q} label="query" />)}
          {receipts.map((r) => <IdChip key={r} id={r} label="receipt" />)}
          {ev.routed_model && <span className="font-mono text-sm text-muted-foreground">{ev.routed_model}{ev.latency_ms ? ` · ${(ev.latency_ms / 1000).toFixed(1)}s` : ""}</span>}
        </div>
      )}
    </li>
  );
}

function Fact({ label, value, copy }: { label: string; value: string | number; copy?: string }) {
  return (
    <div className="grid min-w-0 gap-1 rounded-lg bg-muted p-4">
      <dt className="text-sm font-semibold text-muted-foreground">{label}</dt>
      <dd className="flex min-w-0 items-center text-xl leading-7 font-semibold tabular-nums">
        <span className={cn("truncate", copy && "font-mono text-base")}>{value}</span>
        {copy && <CopyButton value={copy} label={label} />}
      </dd>
    </div>
  );
}

export function TechnicalScreen() {
  const { runId, events, memo, state, error, isMock } = useRunCtx();
  const [onlyKey, setOnlyKey] = useState(false);

  const facts = useMemo(() => {
    const ids = (e: TraceEvent) => (e.meterless_receipt_ids?.length ? e.meterless_receipt_ids : e.meterless_receipt_id ? [e.meterless_receipt_id] : []);
    const receipts = new Set(events.flatMap(ids));
    const queries = new Set(events.flatMap((e) => e.zetaris_query_ids ?? []));
    const t = events.map((e) => Date.parse(e.timestamp)).filter((n) => !Number.isNaN(n));
    const calls = typeof memo?.stats?.llm_calls === "number" ? (memo.stats.llm_calls as number) : receipts.size;
    return {
      time: t.length > 1 ? formatDuration((Math.max(...t) - Math.min(...t)) / 1000) : "–",
      calls,
      receipts: receipts.size,
      queries: queries.size,
      critiques: events.filter((e) => e.status === "needs_revision").length,
      retries: events.filter((e) => e.status === "retrying").length,
      escalations: events.filter((e) => e.status === "escalated").length,
    };
  }, [events, memo]);

  const shown = onlyKey ? events.filter((e) => KEY.includes(e.status)) : events;

  if (!runId && state === "idle") {
    return (
      <div className="grid gap-6">
        <h1 className={H1}>Technical view</h1>
        <div className="grid justify-items-start gap-3 rounded-lg border border-dashed border-border p-6">
          <h2 className="text-lg leading-7 font-semibold">No review yet</h2>
          <p className="text-base text-muted-foreground">Everything the system did for a review shows up here, step by step.</p>
          <Button asChild variant="outline"><Link href="/">Go to Review</Link></Button>
        </div>
        <AgentDiagram />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-8">
      <div className="grid gap-2">
        <h1 className={H1}>Technical view</h1>
        <p className="text-base text-muted-foreground">Everything the system did for this review, step by step.</p>
      </div>

      <section aria-labelledby="facts" className="grid gap-4">
        <h2 id="facts" className="text-xl leading-7 font-semibold tracking-[-0.4px]">Run facts</h2>
        <dl className="grid grid-cols-[repeat(2,minmax(0,1fr))] gap-4 lg:grid-cols-[repeat(4,minmax(0,1fr))]">
          {runId && <Fact label="Run ID" value={runId} copy={runId} />}
          <Fact label="Time taken" value={facts.time} />
          <Fact label="Model calls" value={facts.calls} />
          <Fact label="Nemotron receipts" value={facts.receipts} />
          <Fact label="Zetaris queries" value={facts.queries} />
          <Fact label="Critiques" value={facts.critiques} />
          <Fact label="Retries" value={facts.retries} />
          <Fact label="Escalations" value={facts.escalations} />
        </dl>
        {isMock && <p className="text-base text-muted-foreground">This is the recorded sample, with fictional suppliers.</p>}
        {error && (
          <p role="alert" className="rounded-lg border border-destructive px-4 py-3 font-mono text-sm break-words text-destructive">{error}</p>
        )}
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" disabled={events.length === 0} onClick={() => downloadText(`${runId ?? "run"}.jsonl`, traceJsonl(events), "application/x-ndjson")}>
            <Download aria-hidden strokeWidth={1.75} /> Raw trace (JSONL)
          </Button>
          <Button variant="outline" size="sm" disabled={!memo} onClick={() => memo && downloadText(`${memo.run_id}-technical.md`, technicalMarkdown(memo))}>
            <Download aria-hidden strokeWidth={1.75} /> Technical memo (Markdown)
          </Button>
        </div>
      </section>

      <BehaviourPanel runId={runId} state={state} isMock={isMock} />

      <section aria-labelledby="timeline" className="grid gap-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 id="timeline" className="text-xl leading-7 font-semibold tracking-[-0.4px]">Agent timeline ({shown.length})</h2>
          <label className="flex min-h-11 cursor-pointer items-center gap-3">
            <Checkbox checked={onlyKey} onCheckedChange={(c) => setOnlyKey(c === true)} />
            <Label className="cursor-pointer font-normal">Only critiques, retries and escalations</Label>
          </label>
        </div>
        {shown.length === 0 ? (
          <p className="text-base text-muted-foreground">{state === "running" ? "Waiting for the first step…" : "No steps to show."}</p>
        ) : (
          <ol className="grid gap-2" aria-live="off">{shown.map((e, i) => <Line key={`${e.timestamp}-${i}`} ev={e} />)}</ol>
        )}
      </section>

      <AgentDiagram />
    </div>
  );
}
