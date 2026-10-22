"use client";

import { useState } from "react";
import { Download } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FindingCard } from "@/components/finding-card";
import { downloadText, memoToMarkdown } from "@/lib/memo-md";
import { cn } from "@/lib/utils";
import type { DecisionRecord, Finding, FindingStatus, Memo } from "@/lib/types";

const FILTERS: (FindingStatus | "all")[] = ["all", "accepted", "escalated", "suppressed"];

export function MemoView({
  memo,
  decisions,
  onOpen,
  onDecide,
}: {
  memo: Memo;
  decisions: Record<string, DecisionRecord>;
  onOpen: (f: Finding) => void;
  onDecide: (f: Finding, kind: "confirm" | "dismiss") => void;
}) {
  const [filter, setFilter] = useState<FindingStatus | "all">("all");
  const count = (s: FindingStatus) => memo.findings.filter((f) => f.status === s).length;
  const shown = memo.findings.map((f, i) => ({ f, rank: i + 1 })).filter(({ f }) => filter === "all" || f.status === filter);

  return (
    <div className="grid gap-4">
      <section className="rounded-xl border border-border bg-surface p-4">
        <div className="flex flex-wrap items-start gap-3">
          <div>
            <h2 className="text-base font-semibold">Review memo · {memo.agency}</h2>
            <p className="text-xs text-muted">
              {memo.date_from} to {memo.date_to} · <span className="font-mono">{memo.run_id}</span>
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="ml-auto"
            onClick={() => downloadText(`${memo.run_id}.md`, memoToMarkdown(memo))}
          >
            <Download size={14} /> Download Markdown
          </Button>
        </div>
        <p className="mt-3 text-sm leading-relaxed">{memo.summary}</p>
        <p className="mt-3 rounded-md bg-warn-bg px-3 py-2 text-xs text-warn">{memo.disclaimer}</p>
        {memo.limitations.length > 0 && (
          <details className="mt-3 text-sm">
            <summary className="cursor-pointer text-xs font-medium text-muted">Limitations ({memo.limitations.length})</summary>
            <ul className="mt-2 list-disc pl-5 text-xs text-muted">
              {memo.limitations.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
          </details>
        )}
      </section>

      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Filter findings by status">
        {FILTERS.map((s) => {
          const n = s === "all" ? memo.findings.length : count(s);
          return (
            <button
              key={s}
              type="button"
              aria-pressed={filter === s}
              onClick={() => setFilter(s)}
              className={cn(
                "cursor-pointer rounded-full border px-3 py-1 text-xs font-medium capitalize",
                filter === s ? "border-accent bg-accent text-accent-fg" : "border-border bg-surface text-muted hover:text-fg"
              )}
            >
              {s} <Badge className="ml-1">{n}</Badge>
            </button>
          );
        })}
      </div>

      {shown.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted">No findings in this view.</p>
      ) : (
        shown.map(({ f, rank }) => (
          <FindingCard key={f.finding_id} rank={rank} finding={f} decision={decisions[f.finding_id]} onOpen={onOpen} onDecide={onDecide} />
        ))
      )}
    </div>
  );
}
