"use client";

import { useState } from "react";
import { FlaskConical, Play, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { FLAG_NAMES } from "@/lib/status";
import type { RunRequest } from "@/lib/types";

const FLAGS = ["R1", "R2", "R3", "R4", "R8"];

export function RequestBar({
  running,
  hasRun,
  onRun,
  onMock,
  onReset,
}: {
  running: boolean;
  hasRun: boolean;
  onRun: (r: RunRequest) => void;
  onMock: () => void;
  onReset: () => void;
}) {
  const [agency, setAgency] = useState("Housing and Development Board");
  const [from, setFrom] = useState("2025-01-01");
  const [to, setTo] = useState("2025-12-31");
  const [flags, setFlags] = useState<string[]>([]);
  const valid = agency.trim() && from && to && from <= to;

  const toggle = (f: string) => setFlags((cur) => (cur.includes(f) ? cur.filter((x) => x !== f) : [...cur, f]));

  return (
    <form
      className="rounded-xl border border-border bg-surface p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (valid && !running) onRun({ agency: agency.trim(), date_from: from, date_to: to, flags });
      }}
    >
      <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
        <label className="grid gap-1 text-xs font-medium text-muted">
          Agency
          <input
            value={agency}
            onChange={(e) => setAgency(e.target.value)}
            className="h-9 rounded-md border border-border bg-bg px-3 text-sm text-fg"
            placeholder="Agency name as it appears in GeBIZ"
            required
          />
        </label>
        <label className="grid gap-1 text-xs font-medium text-muted">
          From
          <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className="h-9 rounded-md border border-border bg-bg px-3 text-sm text-fg" required />
        </label>
        <label className="grid gap-1 text-xs font-medium text-muted">
          To
          <input type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} className="h-9 rounded-md border border-border bg-bg px-3 text-sm text-fg" required />
        </label>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-muted">Checks (none selected: planner decides)</span>
        {FLAGS.map((f) => (
          <button
            key={f}
            type="button"
            title={FLAG_NAMES[f]}
            aria-pressed={flags.includes(f)}
            onClick={() => toggle(f)}
            className={cn(
              "cursor-pointer rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
              flags.includes(f) ? "border-accent bg-accent text-accent-fg" : "border-border bg-bg text-muted hover:text-fg"
            )}
          >
            {f}
          </button>
        ))}
        <div className="ml-auto flex gap-2">
          {hasRun && (
            <Button type="button" variant="ghost" size="sm" onClick={onReset}>
              <RotateCcw size={14} /> Clear
            </Button>
          )}
          <Button type="button" variant="outline" size="sm" onClick={onMock} disabled={running} title="Replay a recorded demo run with fictional suppliers">
            <FlaskConical size={14} /> Replay mock run
          </Button>
          <Button type="submit" size="sm" disabled={!valid || running}>
            <Play size={14} /> {running ? "Running…" : "Run investigation"}
          </Button>
        </div>
      </div>
    </form>
  );
}
