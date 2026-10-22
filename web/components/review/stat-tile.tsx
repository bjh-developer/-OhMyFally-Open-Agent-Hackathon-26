"use client";

import CountUp from "@/components/CountUp";

// Muted tile, no border: label above a 32px tabular number. CountUp skips the animation under reduced motion.
export function StatTile({ label, value: raw, prefix, sub, wide }: { label: string; value: number; prefix?: string; sub?: string; wide?: boolean }) {
  const value = Math.round(raw);
  // Long money values step down a size so they stay inside the tile.
  const long = value >= 10_000_000;
  return (
    <div className={`grid content-start gap-1 rounded-lg bg-muted p-5 ${wide ? "col-span-2 lg:col-span-1" : ""}`}>
      <p className="text-sm font-semibold text-muted-foreground">{label}</p>
      <p className={`break-words font-semibold tabular-nums ${long ? "text-2xl leading-10 xl:text-[26px]" : "text-[32px] leading-10"}`} aria-label={`${prefix ?? ""}${value.toLocaleString("en-SG")}`}>
        <CountUp to={value} duration={1} separator="," prefix={prefix} trigger="load" />
      </p>
      {sub && <p className="text-sm text-muted-foreground">{sub}</p>}
    </div>
  );
}
