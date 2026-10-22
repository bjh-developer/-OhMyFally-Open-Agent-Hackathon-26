"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { postDecision } from "@/lib/api";
import type { DecisionRecord, Finding } from "@/lib/types";

export interface DecisionTarget {
  finding: Finding;
  kind: "confirm" | "dismiss";
}

const DEFAULT_CONFIRM_REASON = "Confirmed by auditor as warranting follow-up.";

export function DecisionDialog({
  target,
  runId,
  isMock,
  onClose,
  onDone,
}: {
  target: DecisionTarget | null;
  runId: string | null;
  isMock: boolean;
  onClose: () => void;
  onDone: (findingId: string, rec: DecisionRecord) => void;
}) {
  return (
    <Dialog open={!!target} onOpenChange={(o) => !o && onClose()}>
      {target && runId && <DecisionForm key={target.finding.finding_id + target.kind} target={target} runId={runId} isMock={isMock} onClose={onClose} onDone={onDone} />}
    </Dialog>
  );
}

function DecisionForm({
  target,
  runId,
  isMock,
  onClose,
  onDone,
}: {
  target: DecisionTarget;
  runId: string;
  isMock: boolean;
  onClose: () => void;
  onDone: (findingId: string, rec: DecisionRecord) => void;
}) {
  const { finding: f, kind } = target;
  const dismiss = kind === "dismiss";
  const [reason, setReason] = useState("");
  const [tag, setTag] = useState("");
  const [scope, setScope] = useState<"agency" | "global">("agency");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const finalReason = reason.trim() || (dismiss ? "" : DEFAULT_CONFIRM_REASON);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!finalReason || !f.uen) return;
    setBusy(true);
    setErr(null);
    try {
      const body = {
        runId,
        finding_id: f.finding_id,
        uen: f.uen,
        flag_id: f.flag_id,
        agency: f.agency,
        decision: kind,
        reason: finalReason,
        scope,
        ...(tag.trim() ? { pattern_tag: tag.trim() } : {}),
      };
      // Mock runs have no real run id in H-MEM's ledger, so they are not stored: say so instead of faking it.
      const memoryId = isMock ? "mock (not stored)" : (await postDecision(body)).memoryId;
      onDone(f.finding_id, { decision: kind, reason: finalReason, pattern_tag: body.pattern_tag, scope, memoryId });
      onClose();
    } catch (e2) {
      setErr((e2 as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <DialogContent>
      <form onSubmit={submit} className="grid gap-4">
        <div>
          <DialogTitle className="text-base font-semibold">{dismiss ? "Dismiss this finding" : "Confirm this finding"}</DialogTitle>
          <DialogDescription className="mt-1 text-sm text-muted">
            {f.flag_id} · {f.supplier_name} · <span className="font-mono">{f.uen}</span> at {f.agency}.{" "}
            {dismiss
              ? "H-MEM will remember this, and the next run for the same supplier, flag and agency will suppress it and cite your reason."
              : "H-MEM will record that you confirmed this finding."}
          </DialogDescription>
        </div>
        <label className="grid gap-1 text-xs font-medium text-muted">
          Reason {dismiss ? "(required)" : "(optional)"}
          <textarea
            autoFocus
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            required={dismiss}
            rows={3}
            placeholder={dismiss ? "Why is this not an anomaly? e.g. spin-off under an existing framework agreement" : DEFAULT_CONFIRM_REASON}
            className="rounded-md border border-border bg-bg p-2 text-sm font-normal text-fg"
          />
        </label>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="grid gap-1 text-xs font-medium text-muted">
            Pattern tag (optional)
            <input
              value={tag}
              onChange={(e) => setTag(e.target.value)}
              placeholder="e.g. framework-spinoff"
              className="h-9 rounded-md border border-border bg-bg px-2 text-sm font-normal text-fg"
            />
          </label>
          <label className="grid gap-1 text-xs font-medium text-muted">
            Remember for
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as "agency" | "global")}
              className="h-9 rounded-md border border-border bg-bg px-2 text-sm font-normal text-fg"
            >
              <option value="agency">This agency only</option>
              <option value="global">All agencies</option>
            </select>
          </label>
        </div>
        {isMock && <p className="rounded-md bg-warn-bg px-3 py-2 text-xs text-warn">Mock run: this decision is shown here but not sent to H-MEM.</p>}
        {err && (
          <p role="alert" className="rounded-md bg-bad-bg px-3 py-2 text-xs text-bad">
            Could not save: {err}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button type="submit" variant={dismiss ? "danger" : "ok"} disabled={busy || !finalReason}>
            {busy ? "Saving…" : dismiss ? "Dismiss and remember" : "Confirm and remember"}
          </Button>
        </div>
      </form>
    </DialogContent>
  );
}
