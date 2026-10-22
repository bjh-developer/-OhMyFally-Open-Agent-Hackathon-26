"use client";

import CountUp from "@/components/CountUp";

// Muted tile, no border: label above a 32px tabular number. CountUp skips the animation under reduced motion.
export function StatTile({ label, value, prefix, sub, wide }: { label: string; value: number; prefix?: string; sub?: string; wide?: boolean }) {
  return (
    <div className={`grid content-start gap-1 rounded-lg bg-muted p-5 ${wide ? "col-span-2 lg:col-span-1" : ""}`}>
      <p className="text-sm font-semibold text-muted-foreground">{label}</p>
      <p className="text-[32px] leading-10 font-semibold tabular-nums" aria-label={`${prefix ?? ""}${value.toLocaleString("en-SG")}`}>
        <CountUp to={value} duration={1} separator="," prefix={prefix} trigger="load" />
      </p>
      {sub && <p className="text-sm text-muted-foreground">{sub}</p>}
    </div>
  );
}
