"use client";

import { useEffect, useRef } from "react";
import { ArrowRight, Copy, RotateCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn, fmtTime, shortId } from "@/lib/utils";
import { rowStyle, traceTone } from "@/lib/status";
import type { TraceEvent } from "@/lib/types";
import type { RunState } from "@/lib/use-run";

function CopyId({ id, label }: { id: string; label: string }) {
  return (
    <button
      type="button"
      onClick={() => void navigator.clipboard?.writeText(id)}
      title={`${label}: ${id} (click to copy)`}
      className="inline-flex cursor-pointer items-center gap-1 rounded bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-muted hover:text-fg"
    >
      {label} {shortId(id)} <Copy size={10} />
    </button>
  );
}

function Line({ ev }: { ev: TraceEvent }) {
  const receipts = ev.meterless_receipt_ids?.length ? ev.meterless_receipt_ids : ev.meterless_receipt_id ? [ev.meterless_receipt_id] : [];
  const bad = ev.status === "needs_revision" || ev.status === "failed";
  return (
    <li className={cn("slide-in rounded-lg border-l-4 border-y border-r bg-surface px-3 py-2", rowStyle[ev.status])}>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <span className="font-mono text-[11px] text-muted">{fmtTime(ev.timestamp)}</span>
        <span className="font-semibold">{ev.agent_name}</span>
        <span className="font-mono text-xs text-muted">{ev.action}</span>
        {ev.target_agent && (
          <span className="inline-flex items-center gap-1 text-xs text-muted">
            <ArrowRight size={12} /> {ev.target_agent}
          </span>
        )}
        <span className="ml-auto flex items-center gap-1.5">
          {!!ev.retry_count && (
            <Badge tone="warn">
              <RotateCw size={10} /> retry {ev.retry_count}
            </Badge>
          )}
          <Badge tone={traceTone[ev.status]}>{ev.status.replace("_", " ")}</Badge>
        </span>
      </div>
      {ev.output_summary && <p className={cn("mt-1 text-sm", bad && "font-medium text-bad")}>{ev.output_summary}</p>}
      {ev.input_summary && <p className="mt-0.5 line-clamp-2 text-xs text-muted">{ev.input_summary}</p>}
      {(ev.zetaris_query_ids?.length || receipts.length || ev.confidence != null || ev.routed_model) && (
        <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
          {ev.confidence != null && <Badge>confidence {Math.round(ev.confidence * 100)}%</Badge>}
          {ev.zetaris_query_ids?.map((q) => <CopyId key={q} id={q} label="query" />)}
          {receipts.map((r) => <CopyId key={r} id={r} label="receipt" />)}
          {ev.routed_model && (
            <span className="text-[11px] text-muted">
              {ev.routed_model}
              {ev.latency_ms ? ` · ${(ev.latency_ms / 1000).toFixed(1)}s` : ""}
            </span>
          )}
        </div>
      )}
    </li>
  );
}

export function Timeline({ events, state, error, isMock }: { events: TraceEvent[]; state: RunState; error: string | null; isMock: boolean }) {
  const list = useRef<HTMLOListElement>(null);
  // Scroll only the list, not the page, so the memo stays where the reader left it.
  useEffect(() => {
    const el = list.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [events.length]);

  const critiques = events.filter((e) => e.status === "needs_revision" || e.status === "failed").length;
  const retries = events.filter((e) => e.status === "retrying").length;
  const escalations = events.filter((e) => e.status === "escalated").length;

  return (
    <section aria-label="Run timeline" className="flex min-h-0 flex-col rounded-xl border border-border bg-surface-2/50">
      <header className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold">Run timeline</h2>
        {isMock && <Badge tone="warn">mock replay</Badge>}
        {state === "running" && <Badge tone="info">live</Badge>}
        <span className="ml-auto flex gap-1.5">
          {critiques > 0 && <Badge tone="bad">{critiques} critique{critiques > 1 ? "s" : ""}</Badge>}
          {retries > 0 && <Badge tone="warn">{retries} retr{retries > 1 ? "ies" : "y"}</Badge>}
          {escalations > 0 && <Badge tone="esc">{escalations} escalated</Badge>}
        </span>
      </header>
      <ol ref={list} className="flex max-h-[70vh] min-h-48 flex-col gap-2 overflow-y-auto p-3" aria-live="polite">
        {events.length === 0 && (
          <li className="px-2 py-8 text-center text-sm text-muted">
            {state === "running" ? "Waiting for the first agent step…" : "Start a run to watch the agents work. Every Zetaris query and Nemotron call is logged here."}
          </li>
        )}
        {events.map((ev, i) => (
          <Line key={`${ev.timestamp}-${i}`} ev={ev} />
        ))}
        {state === "failed" && error && (
          <li className="rounded-lg border border-bad bg-bad-bg px-3 py-2 text-sm text-bad" role="alert">
            Run failed: {error}
          </li>
        )}
        {state === "rejected" && (
          <li className="rounded-lg border border-warn bg-warn-bg px-3 py-2 text-sm text-warn">Request rejected{error ? `: ${error}` : "."}</li>
        )}
      </ol>
    </section>
  );
}
