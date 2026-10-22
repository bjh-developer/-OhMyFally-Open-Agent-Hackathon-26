"use client";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatPeriod } from "@/lib/copy";
import { useRunCtx } from "@/components/run-provider";

// One line that replaces the request card once a review exists.
export function RequestSummary({ canChange }: { canChange: boolean }) {
  const { request, isMock, clear } = useRunCtx();
  if (!request) return null;
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-border bg-card px-5 py-2">
      <p className="text-base">
        <span className="font-semibold">{request.agency}</span>
        <span className="text-muted-foreground"> · {formatPeriod(request.date_from, request.date_to)}</span>
      </p>
      {isMock && <Badge variant="info">Sample review</Badge>}
      {canChange && (
        <Button variant="link" size="sm" className="ml-auto min-w-0" onClick={clear}>
          Change
        </Button>
      )}
    </div>
  );
}
