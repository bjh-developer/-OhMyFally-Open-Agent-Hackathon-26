"use client";

import { CircleAlert, ScanSearch } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { RequestCard } from "@/components/review/request-card";
import { RequestSummary } from "@/components/review/request-summary";
import { ProgressCard, ResultsSkeleton } from "@/components/review/progress-card";
import { Results } from "@/components/review/results";
import { useRunCtx } from "@/components/run-provider";

export const H1 = "text-2xl leading-7 font-semibold tracking-[-0.4px] lg:text-[26px] lg:leading-8 2xl:text-[28px]";

function EmptyState() {
  return (
    <div className="grid justify-items-center gap-2 rounded-lg border border-dashed border-border px-6 py-10 text-center">
      <ScanSearch aria-hidden size={24} strokeWidth={1.75} className="text-primary" />
      <h3 className="text-lg leading-7 font-semibold">Ready when you are</h3>
      <p className="max-w-md text-base text-muted-foreground">Pick an agency and a period to see which awards need a second look.</p>
    </div>
  );
}

export function ReviewScreen() {
  const { state, memo, events, startedAt, request, isMock, begin, beginMock, clear } = useRunCtx();
  const failed = state === "failed" || state === "rejected";
  const done = state === "done" && memo;
  const retry = () => (isMock ? beginMock() : request ? begin(request) : clear());

  return (
    <div className="grid gap-8">
      <h1 className={H1}>Review procurement awards</h1>

      {state === "idle" && (
        <>
          <RequestCard />
          <EmptyState />
        </>
      )}

      {state === "running" && (
        <>
          <RequestSummary canChange={false} />
          <ProgressCard agents={events.map((e) => e.agent_name)} startedAt={startedAt} />
          <ResultsSkeleton />
        </>
      )}

      {failed && (
        <>
          <RequestSummary canChange />
          <Alert variant="destructive" role="alert" className="border-destructive">
            <CircleAlert aria-hidden strokeWidth={1.75} />
            <AlertTitle>We couldn't finish this review</AlertTitle>
            <AlertDescription>
              <p>Try again, or open the Technical view for details.</p>
              <Button variant="outline" size="sm" className="mt-2" onClick={retry}>
                Try again
              </Button>
            </AlertDescription>
          </Alert>
        </>
      )}

      {done && (
        <>
          <RequestSummary canChange />
          <Results memo={memo} />
        </>
      )}

      {state === "done" && !memo && (
        <>
          <RequestSummary canChange />
          <EmptyState />
        </>
      )}
    </div>
  );
}
