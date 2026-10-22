"use client";

import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RequestBar } from "@/components/request-bar";
import { Timeline } from "@/components/timeline";
import { MemoView } from "@/components/memo-view";
import { ReviewQueue } from "@/components/review-queue";
import { EvidenceDrawer } from "@/components/evidence-drawer";
import { DecisionDialog, type DecisionTarget } from "@/components/decision-dialog";
import { useRun } from "@/lib/use-run";
import type { DecisionRecord, Finding } from "@/lib/types";

export default function Home() {
  const run = useRun();
  const [decisions, setDecisions] = useState<Record<string, DecisionRecord>>({});
  const [open, setOpen] = useState<Finding | null>(null);
  const [target, setTarget] = useState<DecisionTarget | null>(null);

  // Decisions belong to one run: clear them when a new run starts or the page is cleared.
  useEffect(() => {
    setDecisions({});
    setOpen(null);
    setTarget(null);
  }, [run.runId]);

  const escalated = run.memo?.findings.filter((f) => f.status === "escalated") ?? [];
  const pending = escalated.filter((f) => !decisions[f.finding_id]).length;
  const running = run.state === "running";
  const hasRun = run.state !== "idle";

  return (
    <main className="mx-auto grid max-w-7xl gap-5 px-4 py-6 md:px-6">
      <header className="flex flex-wrap items-center gap-3">
        <ShieldCheck className="text-accent" size={26} aria-hidden />
        <div>
          <h1 className="text-lg font-semibold leading-tight">Procurement Integrity Investigator</h1>
          <p className="text-xs text-muted">Anomalies for review, with the SQL, rows and memory behind each one. Requires auditor judgement.</p>
        </div>
        {run.runId && <Badge className="ml-auto font-mono">{run.runId}</Badge>}
      </header>

      <RequestBar running={running} hasRun={hasRun} onRun={run.start} onMock={run.startMock} onReset={run.reset} />

      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <Timeline events={run.events} state={run.state} error={run.error} isMock={run.isMock} />

        <Tabs defaultValue="memo">
          <TabsList>
            <TabsTrigger value="memo">Review memo</TabsTrigger>
            <TabsTrigger value="queue">
              Human review {pending > 0 && <Badge tone="esc">{pending}</Badge>}
            </TabsTrigger>
          </TabsList>
          <TabsContent value="memo">
            {run.memo ? (
              <MemoView memo={run.memo} decisions={decisions} onOpen={setOpen} onDecide={(finding, kind) => setTarget({ finding, kind })} />
            ) : (
              <p className="rounded-xl border border-dashed border-border p-10 text-center text-sm text-muted">
                {running ? "The memo appears here when the Reporter finishes." : "No memo yet. Run an investigation, or replay the mock run to see the layout."}
              </p>
            )}
          </TabsContent>
          <TabsContent value="queue">
            <ReviewQueue findings={escalated} decisions={decisions} onOpen={setOpen} onDecide={(finding, kind) => setTarget({ finding, kind })} />
          </TabsContent>
        </Tabs>
      </div>

      <EvidenceDrawer finding={open} decision={open ? decisions[open.finding_id] : undefined} onClose={() => setOpen(null)} />
      <DecisionDialog
        target={target}
        runId={run.memo?.run_id ?? run.runId}
        isMock={run.isMock}
        onClose={() => setTarget(null)}
        onDone={(id, rec) => setDecisions((d) => ({ ...d, [id]: rec }))}
      />
    </main>
  );
}
