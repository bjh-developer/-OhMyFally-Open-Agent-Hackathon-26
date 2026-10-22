"use client";

import { useState } from "react";
import { LoaderCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import { PATTERN_TAGS, flagTitle, formatMoney, groupTitle, type Item } from "@/lib/copy";
import { postDecision } from "@/lib/api";
import type { DecisionRecord } from "@/lib/types";
import { useRunCtx } from "@/components/run-provider";

const DEFAULT_CONFIRM_REASON = "Confirmed by auditor as needing follow-up.";

export function DecisionDialog() {
  const { target, setTarget, restoreFocus } = useRunCtx();
  return (
    <Dialog open={!!target} onOpenChange={(o) => !o && setTarget(null)}>
      {target && <DecisionForm key={target.item.id + target.kind} item={target.item} kind={target.kind} restoreFocus={restoreFocus} />}
    </Dialog>
  );
}

function DecisionForm({ item, kind, restoreFocus }: { item: Item; kind: "confirm" | "dismiss"; restoreFocus: (e: Event) => void }) {
  const { setTarget, runId, memo, isMock, recordDecision } = useRunCtx();
  const dismiss = kind === "dismiss";
  const [reason, setReason] = useState("");
  const [tag, setTag] = useState("other");
  const [scope, setScope] = useState<"agency" | "global">("agency");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(false);
  const [tried, setTried] = useState(false);

  const title = item.kind === "group" && item.group ? groupTitle(item.group) : flagTitle(item.flag_id);
  const finalReason = reason.trim() || (dismiss ? "" : DEFAULT_CONFIRM_REASON);
  const members = item.members.filter((m) => !!m.uen);
  const missing = dismiss && !finalReason;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setTried(true);
    if (missing || members.length === 0) return;
    const rid = memo?.run_id ?? runId;
    if (!rid) return;
    setBusy(true);
    setErr(false);
    try {
      const pattern_tag = dismiss && tag !== "other" ? tag : undefined;
      let memoryId = "sample";
      if (!isMock) {
        const ids: string[] = [];
        for (const m of members) {
          const r = await postDecision({ runId: rid, finding_id: m.finding_id, uen: m.uen as string, flag_id: m.flag_id, agency: m.agency, decision: kind, reason: finalReason, scope, ...(pattern_tag ? { pattern_tag } : {}) });
          ids.push(r.memoryId);
        }
        memoryId = ids.join(", ");
      }
      const rec: DecisionRecord = { decision: kind, reason: finalReason, pattern_tag, scope, memoryId, at: new Date().toISOString() };
      recordDecision(item.members, rec);
      toast(isMock ? "Sample review: decisions aren't saved." : "Decision saved. We'll remember it for next time.");
      setTarget(null);
    } catch {
      setErr(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <DialogContent className="max-h-[92dvh] overflow-y-auto" onCloseAutoFocus={restoreFocus}>
      <form onSubmit={submit} noValidate className="grid gap-5">
        <DialogHeader>
          <DialogTitle className="text-xl leading-7 font-semibold tracking-[-0.4px]">{dismiss ? "Dismiss this item" : "Confirm this needs follow-up"}</DialogTitle>
          <DialogDescription className="text-base">
            {title} · {item.supplierLabel}
            {item.amount != null ? ` · ${formatMoney(item.amount)}` : ""}
            {item.members.length > 1 ? `. This applies to all ${members.length} suppliers in the group.` : ""}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-2">
          <Label htmlFor="reason">Reason {dismiss ? "(required)" : "(optional)"}</Label>
          <Textarea id="reason" value={reason} onChange={(e) => setReason(e.target.value)} rows={3} aria-invalid={tried && missing} aria-describedby="reason-help" autoFocus />
          {tried && missing ? (
            <p role="alert" id="reason-help" className="text-sm font-semibold text-destructive">Add a short reason so the next reviewer knows why.</p>
          ) : (
            <p id="reason-help" className="text-sm text-muted-foreground">Your note is saved with the decision.</p>
          )}
        </div>

        {dismiss && (
          <fieldset className="grid gap-1">
            <legend className="mb-1 text-base font-semibold">What explains it? <span className="font-normal text-muted-foreground">(optional)</span></legend>
            <RadioGroup value={tag} onValueChange={setTag}>
              {PATTERN_TAGS.map((t) => (
                <label key={t.value || "other"} className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg px-1 hover:bg-muted">
                  <RadioGroupItem value={t.value || "other"} />
                  <span className="text-base">{t.label}</span>
                </label>
              ))}
            </RadioGroup>
          </fieldset>
        )}

        <fieldset className="grid gap-1">
          <legend className="mb-1 text-base font-semibold">Apply to</legend>
          <RadioGroup value={scope} onValueChange={(v) => setScope(v as "agency" | "global")}>
            <label className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg px-1 hover:bg-muted">
              <RadioGroupItem value="agency" />
              <span className="text-base">This agency only</span>
            </label>
            <label className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg px-1 hover:bg-muted">
              <RadioGroupItem value="global" />
              <span className="text-base">All agencies</span>
            </label>
          </RadioGroup>
          <p className="text-sm text-muted-foreground">Next time, ProcureLens will skip matching items.</p>
        </fieldset>

        {isMock && <p className="rounded-lg bg-warning-subtle px-4 py-3 text-base text-warning-foreground">Sample review: decisions aren't saved.</p>}
        {err && (
          <p role="alert" className="rounded-lg border border-destructive px-4 py-3 text-base text-destructive">
            We couldn't save your decision. Try again, or open the Technical view for details.
          </p>
        )}

        <DialogFooter className="gap-2 sm:gap-2">
          <Button type="button" variant="outline" onClick={() => setTarget(null)} disabled={busy}>
            Cancel
          </Button>
          <Button type="submit" disabled={busy}>
            {busy && <LoaderCircle aria-hidden className="animate-spin" />}
            {busy ? "Saving…" : dismiss ? "Dismiss" : "Confirm"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
