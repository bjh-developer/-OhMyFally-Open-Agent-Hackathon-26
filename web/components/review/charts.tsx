"use client";

import { Bar, BarChart, LabelList, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, type ChartConfig } from "@/components/ui/chart";
import { flagIcon } from "@/lib/icons";
import { flagTitle, formatMoney, moneySummary, reasonSummary, type Summary } from "@/lib/copy";

const SHORT: Record<string, string> = {
  R1: "Recently registered",
  R2: "No longer active",
  R3: "Shared address",
  R4: "Just under limit",
  R5: "Business mismatch",
  R6: "One supplier dominates",
  R7: "Name change",
  R8: "Not in registry",
  R9: "Not top-scored",
};

interface Row {
  key: string;
  label: string;
  value: number;
}

// At most 5 bars: the smallest reasons fold into "Other".
function rowsFor(s: Summary, pick: (f: Summary["byFlag"][number]) => number): { rows: Row[]; legend: Row[] } {
  const all = s.byFlag.map((f) => ({ key: f.flag_id, label: SHORT[f.flag_id] ?? flagTitle(f.flag_id), value: pick(f) })).sort((a, b) => b.value - a.value);
  const legend = all;
  if (all.length <= 5) return { rows: all, legend };
  const top = all.slice(0, 4);
  return { rows: [...top, { key: "other", label: "Other reasons", value: all.slice(4).reduce((t, r) => t + r.value, 0) }], legend };
}

function BarCard({ id, title, rows, legend, summary, fill, format }: { id: string; title: string; rows: Row[]; legend: Row[]; summary: string; fill: string; format: (n: number) => string }) {
  const max = Math.max(...rows.map((r) => r.value), 1);
  const config = { value: { label: title, color: fill } } satisfies ChartConfig;
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h3 className="text-lg leading-7 font-semibold">{title}</h3>
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <ChartContainer config={config} className="aspect-auto w-full" style={{ height: 44 * rows.length + 8 }} role="img" aria-label={title} aria-describedby={`${id}-sum`}>
          <BarChart accessibilityLayer data={rows} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 0 }} barCategoryGap={10}>
            <XAxis type="number" hide domain={[0, max * 1.7]} />
            <YAxis type="category" dataKey="label" width={118} tickLine={false} axisLine={false} tick={{ fill: "var(--foreground)", fontSize: 14 }} />
            <Bar dataKey="value" fill={fill} radius={4} isAnimationActive={false}>
              <LabelList dataKey="value" position="right" formatter={(v: unknown) => format(Number(v))} fill="var(--foreground)" fontSize={14} fontWeight={600} />
            </Bar>
          </BarChart>
        </ChartContainer>
        <ul className="grid gap-1 text-sm text-muted-foreground" aria-label={`${title}: legend`}>
          {legend.map((r) => {
            const Icon = flagIcon(r.key);
            return (
              <li key={r.key} className="flex items-center gap-2">
                <Icon aria-hidden size={16} strokeWidth={1.75} className="shrink-0" />
                <span>
                  {flagTitle(r.key)}: <span className="font-semibold text-foreground tabular-nums">{format(r.value)}</span>
                </span>
              </li>
            );
          })}
        </ul>
        <p id={`${id}-sum`} className="text-base">{summary}</p>
      </CardContent>
    </Card>
  );
}

export function Charts({ summary: s }: { summary: Summary }) {
  if (s.byFlag.length < 2) {
    const only = s.byFlag[0];
    if (!only) return null;
    return (
      <p className="rounded-lg bg-muted p-5 text-base">
        All {s.worth} {s.worth === 1 ? "item is" : "items are"} "{flagTitle(only.flag_id).toLowerCase()}"{only.amount ? `, worth ${formatMoney(only.amount)}` : ""}.
      </p>
    );
  }
  const counts = rowsFor(s, (f) => f.count);
  const money = rowsFor(s, (f) => f.amount);
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <BarCard id="by-reason" title="By reason" {...counts} summary={reasonSummary(s)} fill="var(--chart-1)" format={(n) => String(n)} />
      {s.value ? <BarCard id="by-money" title="Where the money is" {...money} summary={moneySummary(s)} fill="var(--chart-2)" format={formatMoney} /> : null}
    </div>
  );
}
