"use client";

import { useEffect, useRef, useState } from "react";
import { Circle, CircleCheck, LoaderCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { STEPS, formatDuration, stepStates } from "@/lib/copy";
import { cn } from "@/lib/utils";

export function ProgressCard({ agents, startedAt, finished = false }: { agents: string[]; startedAt: number | null; finished?: boolean }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (finished) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [finished]);

  const states = stepStates(agents, finished);
  const active = states.indexOf("active");
  const elapsed = startedAt ? (now - startedAt) / 1000 : 0;

  // Announce a step once, when it becomes the active one.
  const announced = useRef(-1);
  const [announcement, setAnnouncement] = useState("");
  useEffect(() => {
    if (active >= 0 && active !== announced.current) {
      announced.current = active;
      setAnnouncement(`Step ${active + 1} of ${STEPS.length}: ${STEPS[active].label}`);
    }
  }, [active]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2 className="text-xl leading-7 font-semibold tracking-[-0.4px]">Reviewing the awards</h2>
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Elapsed {formatDuration(elapsed)} · Usually takes 1–5 minutes
        </p>
      </CardHeader>
      <CardContent>
        <p className="sr-only" aria-live="polite" role="status">{announcement}</p>
        <ol className="grid gap-1" aria-label="Review progress">
          {STEPS.map((s, i) => {
            const st = states[i];
            return (
              <li key={s.label} className="flex min-h-11 items-center gap-3" aria-current={st === "active" ? "step" : undefined}>
                {st === "done" ? (
                  <CircleCheck aria-hidden size={20} strokeWidth={1.75} className="text-success" />
                ) : st === "active" ? (
                  <LoaderCircle aria-hidden size={20} strokeWidth={1.75} className="animate-spin text-primary" />
                ) : (
                  <Circle aria-hidden size={20} strokeWidth={1.75} className="text-muted-foreground" />
                )}
                <span className={cn("text-base", st === "pending" ? "text-muted-foreground" : "text-foreground", st === "active" && "font-semibold")}>
                  {s.label}
                  <span className="sr-only">{st === "done" ? " (done)" : st === "active" ? " (in progress)" : " (waiting)"}</span>
                </span>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}

// Shapes of what is coming: 4 stat tiles, one chart, three item cards.
export function ResultsSkeleton() {
  return (
    <div aria-hidden className="grid gap-8">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="grid gap-3 rounded-lg bg-muted p-5">
            <Skeleton className="h-4 w-24 bg-border" />
            <Skeleton className="h-8 w-20 bg-border" />
          </div>
        ))}
      </div>
      <div className="rounded-lg border border-border bg-card p-6">
        <Skeleton className="mb-5 h-6 w-40" />
        <div className="grid gap-3">
          {[80, 60, 45, 25].map((w) => (
            <Skeleton key={w} className="h-6" style={{ width: `${w}%` }} />
          ))}
        </div>
      </div>
      <div className="grid gap-4">
        {[0, 1, 2].map((i) => (
          <div key={i} className="grid gap-4 rounded-lg border border-border bg-card p-6">
            <div className="flex justify-between gap-4">
              <Skeleton className="h-6 w-2/3" />
              <Skeleton className="h-6 w-28" />
            </div>
            <Skeleton className="h-5 w-1/2" />
            <Skeleton className="h-5 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
