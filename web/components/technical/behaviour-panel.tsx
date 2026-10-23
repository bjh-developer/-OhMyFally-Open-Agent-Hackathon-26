"use client";

import { useEffect, useState } from "react";
import { ArrowUpLeft, History } from "lucide-react";
import { Bar, BarChart, LabelList, XAxis, YAxis } from "recharts";
import { ChartContainer, type ChartConfig } from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";
import { getRunSummary } from "@/lib/api";
import { formatDuration } from "@/lib/copy";
import type { RunSummary } from "@/lib/types";

const NAMES: Record<string, string> = {
  GateAgent: "Gate",
  PlannerAgent: "Planner",
  ResolverAgent: "Resolver",
  AnalystAgent: "Analyst",
  CriticAgent: "Critic",
  RiskAgent: "Risk",
  ReporterAgent: "Reporter",
};
const nice = (a: string) => NAMES[a] ?? a.replace(/Agent$/, "");
const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

export function loopSentence(l: RunSummary["loops"][number]): string {
  const from = nice(l.from_agent);
  const to = nice(l.to_agent);
  const reason = l.reason ? `: ${l.reason}` : "";
  if (from === "Risk" && to === "Planner") return `Risk asked Planner for a wider plan${reason}`;
  const what = l.claims ? `${plural(l.claims, "claim", "claims")} ` : "work ";
  return `${from} sent ${what}back to ${to}${reason}`;
}

function Tile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="grid min-w-0 gap-1 rounded-lg bg-muted p-4">
      <dt className="text-sm font-semibold text-muted-foreground">{label}</dt>
      <dd className="text-xl leading-7 font-semibold tabular-nums">{value}</dd>
    </div>
  );
}

function PanelSkeleton() {
  return (
    <div className="grid gap-4" aria-busy="true" aria-label="Loading how the agents worked">
      <div className="grid grid-cols-[repeat(2,minmax(0,1fr))] gap-4 lg:grid-cols-[repeat(4,minmax(0,1fr))]">
        {Array.from({ length: 1 }, (_, i) => <Skeleton key={i} className="h-[76px]" />)}
      </div>
      <Skeleton className="h-40" />
    </div>
  );
}

export function BehaviourPanel({ runId, state, isMock }: { runId: string | null; state: string; isMock: boolean }) {
  const [data, setData] = useState<RunSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const finished = state === "done" || state === "rejected" || state === "failed";

  useEffect(() => {
    setData(null);
    if (!runId || isMock || !finished) return;
    let live = true;
    setLoading(true);
    getRunSummary(runId)
      .then((d) => live && setData(d))
      .catch(() => live && setData(null)) // old or unknown run: show nothing rather than something broken
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, [runId, isMock, finished]);

  if (!runId || isMock) return null;
  const running = state === "running";
  if (!running && !loading && !data) return null;

  const agents = (data?.per_agent ?? []).map((a) => ({ label: nice(a.agent), steps: a.calls, time: a.time_s }));
  const config = { steps: { label: "Steps", color: "var(--chart-1)" } } satisfies ChartConfig;
  const cleared = data?.cleared_by_memory ?? 0;

  return (
    <section aria-labelledby="behaviour" className="grid gap-4">
      <h2 id="behaviour" className="text-xl leading-7 font-semibold tracking-[-0.4px]">How the agents worked</h2>
      {!data ? (
        running ? <p className="text-base text-muted-foreground">Ready when the review finishes.</p> : <PanelSkeleton />
      ) : (
        <>
          {/* Model calls, critiques, retries, escalations, Zetaris queries and time are in Run facts above. */}
          <dl className="grid grid-cols-[repeat(2,minmax(0,1fr))] gap-4 lg:grid-cols-[repeat(4,minmax(0,1fr))]">
            <Tile label="Memories used" value={data.memory_tracked ? (data.memory_hits ?? 0) : "–"} />
          </dl>

          {cleared > 0 && (
            <p className="flex items-center gap-2 text-base">
              <History aria-hidden size={20} strokeWidth={1.75} className="shrink-0 text-muted-foreground" />
              Cleared by a past decision: <span className="font-semibold tabular-nums">{cleared}</span>
            </p>
          )}

          {agents.length > 0 && (
            <div className="grid gap-2">
              <h3 className="text-lg leading-7 font-semibold">Steps per agent</h3>
              <ChartContainer config={config} className="aspect-auto w-full" style={{ height: 36 * agents.length + 8 }} role="img" aria-label="Steps per agent">
                <BarChart accessibilityLayer data={agents} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 0 }} barCategoryGap={8}>
                  <XAxis type="number" hide domain={[0, Math.max(...agents.map((a) => a.steps), 1) * 1.8]} />
                  <YAxis type="category" dataKey="label" width={84} tickLine={false} axisLine={false} tick={{ fill: "var(--foreground)", fontSize: 14 }} />
                  <Bar dataKey="steps" fill="var(--chart-1)" radius={4} isAnimationActive={false}>
                    <LabelList dataKey="steps" position="right" fill="var(--foreground)" fontSize={14} fontWeight={600}
                      formatter={(v: unknown, _e?: unknown) => String(v)} />
                  </Bar>
                </BarChart>
              </ChartContainer>
              <ul className="grid gap-1 text-sm text-muted-foreground" aria-label="Time per agent">
                {agents.filter((a) => a.time > 0).map((a) => (
                  <li key={a.label}>{a.label}: {a.time.toFixed(1)} s waiting on the model</li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid gap-2">
            <h3 className="text-lg leading-7 font-semibold">Loops</h3>
            {data.loops.length === 0 ? (
              <p className="text-base text-muted-foreground">No agent sent work back. Every step passed on the first go.</p>
            ) : (
              <ul className="grid gap-2">
                {data.loops.map((l, i) => (
                  <li key={i} className="flex items-start gap-2 rounded-lg border border-border border-l-4 border-l-warning bg-card p-3 text-base">
                    <ArrowUpLeft aria-hidden size={20} strokeWidth={1.75} className="mt-0.5 shrink-0 text-muted-foreground" />
                    <span className="min-w-0 break-words">{loopSentence(l)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {(data.plan_notes?.length ?? 0) > 0 && (
            <div className="grid gap-2">
              <h3 className="text-lg leading-7 font-semibold">Plan review</h3>
              <ul className="grid gap-2">
                {data.plan_notes!.map((n, i) => (
                  <li key={i} className="rounded-lg border border-border bg-card p-3 text-base break-words">Plan review noted: {n}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
}
