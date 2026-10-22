"use client";

import { BookOpen, Code, ExternalLink } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { StatusBadge } from "@/components/review/status-badge";
import { agoChunk } from "@/lib/ago";
import { STATUS_COPY, STRENGTH_TIP, firstSentences, flagTitle, formatDate, formatMoney, friendlyCell, friendlyColumn, groupTitle, isMoneyColumn, plainNotes, relevantAgoRefs, sourceName, strengthOf, whyFlagged, type Item } from "@/lib/copy";
import { flagIcon } from "@/lib/icons";
import type { DecisionRecord, Evidence, Finding } from "@/lib/types";
import { useRunCtx } from "@/components/run-provider";
import { RecordMenu, canRemember } from "@/components/review/item-card";

const H = "text-lg leading-7 font-semibold";

function facts(item: Item): [string, string][] {
  const f = item.finding;
  const rows = f.evidence.flatMap((e) => e.rows);
  const fromRows = (k: string) => rows.map((r) => r[k]).find((v) => v != null && v !== "");
  const inc = fromRows("registration_incorporation_date") ?? /Incorporated (\d{4}-\d{2}-\d{2})/.exec(f.detail ?? "")?.[1];
  const status = fromRows("entity_status") ?? (f.metric_name === "entity_status" ? f.metric_value : null);
  const out: [string, string | null | undefined][] = [
    ["Supplier", item.supplierLabel],
    ["Amount", item.amount != null ? formatMoney(item.amount) : null],
    ["Award date", item.date ? formatDate(item.date) : null],
    ["Agency", f.agency],
    ["Registered on", inc ? formatDate(String(inc)) : null],
    ["Registry status", status ? String(status) : null],
    ["Tender reference", item.kind === "group" ? null : f.tender_no],
    ["Company registration no.", item.kind === "group" ? null : f.uen],
  ];
  return out.filter((r): r is [string, string] => !!r[1]);
}

const HIDE = new Set(["flag_id", "agency"]);

function RecordTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (rows.length === 0) return <p className="text-base text-muted-foreground">No records came back.</p>;
  const cols = [...new Set(rows.flatMap((r) => Object.keys(r)))].filter((c) => !HIDE.has(c));
  return (
    <div className="overflow-x-auto border border-border">
      <table className="w-full text-left text-base">
        <thead className="bg-muted">
          <tr>
            {cols.map((c) => (
              <th key={c} scope="col" className={`px-3 py-2 text-sm font-semibold whitespace-nowrap ${isMoneyColumn(c) ? "text-right" : ""}`}>{friendlyColumn(c)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-border">
              {cols.map((c) => (
                <td key={c} className={`px-3 py-2 text-sm ${isMoneyColumn(c) ? "text-right tabular-nums" : ""}`}>{friendlyCell(c, r[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Specialists({ evidence, f }: { evidence: Evidence[]; f: Finding }) {
  return (
    <div className="grid gap-4">
      {evidence.map((e, i) => (
        <div key={`${e.query_id}-${i}`} className="grid gap-2">
          <p className="text-sm font-semibold">Query {i + 1}: {e.row_count} {e.row_count === 1 ? "row" : "rows"}</p>
          <pre className="max-h-64 overflow-auto bg-muted p-3 font-mono text-sm leading-5 whitespace-pre-wrap break-words">{e.sql}</pre>
          <p className="font-mono text-sm break-all">Query ID: {e.query_id}</p>
          {e.source_objects.length > 0 && <p className="font-mono text-sm break-all">Tables: {e.source_objects.join(", ")}</p>}
        </div>
      ))}
      {f.memory_refs.length > 0 && <p className="font-mono text-sm break-all">Memory IDs: {f.memory_refs.join(", ")}</p>}
    </div>
  );
}

function DecisionNote({ d }: { d: DecisionRecord }) {
  const key = d.decision === "confirm" ? "confirmed" : "dismissed";
  const when = new Date(d.at).toLocaleString("en-SG", { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" });
  return (
    <section className="grid gap-2 rounded-lg bg-muted p-4" aria-label="Your decision">
      <div><StatusBadge status={key} /></div>
      <p className="text-base">Reason: {d.reason}</p>
      <p className="text-sm text-muted-foreground">{when}{d.scope === "global" ? " · applies to all agencies" : ""}</p>
    </section>
  );
}

export function ItemSheet() {
  const { openItem: item, setOpenItem, setTarget, decisions } = useRunCtx();
  const f = item?.finding;
  const decision = f ? decisions[f.finding_id] : undefined;
  return (
    <Sheet open={!!item} onOpenChange={(o) => !o && setOpenItem(null)}>
      {item && f && <SheetBody item={item} decision={decision} close={() => setOpenItem(null)} decide={(kind) => setTarget({ item, kind })} />}
    </Sheet>
  );
}

function SheetBody({ item, decision, close, decide }: { item: Item; decision?: DecisionRecord; close: () => void; decide: (k: "confirm" | "dismiss") => void }) {
  const f = item.finding;
  const Icon = flagIcon(item.flag_id);
  const title = item.kind === "group" && item.group ? groupTitle(item.group) : flagTitle(item.flag_id);
  const why = item.kind === "group" && item.group ? `${item.members.length} awards, together ${formatMoney(item.amount)}.` : whyFlagged(f);
  const strength = strengthOf(item.confidence);
  const bullets = plainNotes([...new Set(item.members.flatMap((m) => m.notes ?? []))]);
  const ago = relevantAgoRefs(item.flag_id, [...new Set(item.members.flatMap((m) => m.ago_refs))]).map((id) => agoChunk(id)).filter((c) => !!c);
  const evidence = item.members.flatMap((m) => m.evidence);
  const sources = [...new Set(evidence.flatMap((e) => e.source_objects))].map(sourceName);
  const rows = item.members.length > 1 ? evidence.flatMap((e) => e.rows.slice(0, 1)) : (evidence[evidence.length - 1]?.rows ?? []);
  const needs = item.status === "escalated" && !decision;
  const remember = canRemember(item);

  return (
    <SheetContent aria-describedby="item-why" className="gap-0">
      <SheetHeader className="gap-3 border-b border-border p-6 pr-16">
        <SheetTitle className="flex items-start gap-2 text-xl leading-7 font-semibold tracking-[-0.4px]">
          <Icon aria-hidden size={24} strokeWidth={1.75} className="mt-0.5 shrink-0 text-muted-foreground" />
          {title}
        </SheetTitle>
        <div><StatusBadge status={decision ? (decision.decision === "confirm" ? "confirmed" : "dismissed") : item.status} /></div>
        <SheetDescription className="sr-only" id="item-why">{why}</SheetDescription>
      </SheetHeader>

      <div className="grid flex-1 content-start gap-6 overflow-y-auto p-6">
        {decision && <DecisionNote d={decision} />}

        <section className="grid gap-3" aria-labelledby="s-found">
          <h3 id="s-found" className={H}>What we found</h3>
          <p className="text-base">{why}</p>
          <dl className="grid gap-x-4 gap-y-3 text-base sm:grid-cols-[auto_1fr]">
            {facts(item).map(([k, v]) => (
              <div key={k} className="grid gap-0.5 sm:contents">
                <dt className="text-sm font-semibold text-muted-foreground sm:text-base sm:font-normal">{k}</dt>
                <dd className="break-words">{v}</dd>
              </div>
            ))}
          </dl>
          {item.members.length > 1 && (
            <ul className="grid gap-2 text-base">
              {item.members.map((m) => (
                <li key={m.finding_id} className="border-t border-border pt-2">
                  <span className="font-semibold">{m.supplier_name}</span>
                  <span className="tabular-nums text-muted-foreground"> · {formatMoney(m.awarded_amt)}{m.award_date ? ` · ${formatDate(m.award_date)}` : ""}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        {ago.length > 0 && (
          <section className="grid gap-3" aria-labelledby="s-matters">
            <h3 id="s-matters" className={H}>Why this matters</h3>
            {ago.map((c) => (
              <div key={c!.url} className="grid gap-2">
                <p className="text-base">{firstSentences(c!.text)}</p>
                <a href={c!.url} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center gap-2 text-base font-semibold text-secondary underline underline-offset-4 hover:no-underline">
                  <BookOpen aria-hidden size={20} strokeWidth={1.75} /> Read the report ({c!.fy}, page {c!.page.split(" ")[0]})
                  <ExternalLink aria-hidden size={16} strokeWidth={1.75} />
                  <span className="sr-only">(opens in a new tab)</span>
                </a>
              </div>
            ))}
          </section>
        )}

        <section className="grid gap-3" aria-labelledby="s-sure">
          <h3 id="s-sure" className={H}>How sure are we</h3>
          <p className="flex flex-wrap items-center gap-2 text-base"><Badge variant="outline">Strength: {strength}</Badge> {STRENGTH_TIP}.</p>
          {bullets.length > 0 && (
            <ul className="list-disc space-y-1 pl-6 text-base">
              {bullets.map((b) => <li key={b}>{b}</li>)}
            </ul>
          )}
        </section>

        {evidence.length > 0 && (
          <Accordion type="single" collapsible className="rounded-lg border border-border px-4">
            <AccordionItem value="how" className="border-0">
              <AccordionTrigger>
                <span className="flex items-center gap-2"><Code aria-hidden size={20} strokeWidth={1.75} /> How we checked this</span>
              </AccordionTrigger>
              <AccordionContent className="grid gap-4">
                {sources.length > 0 && <p className="text-base">We looked at: {sources.join(", ")}.</p>}
                <RecordTable rows={rows} />
                <Accordion type="single" collapsible>
                  <AccordionItem value="spec" className="border-0">
                    <AccordionTrigger className="text-sm">For specialists</AccordionTrigger>
                    <AccordionContent><Specialists evidence={evidence} f={f} /></AccordionContent>
                  </AccordionItem>
                </Accordion>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        )}
      </div>

      <SheetFooter className="flex-row flex-wrap gap-2 border-t border-border bg-card p-6">
        {needs ? (
          <>
            <Button disabled={!remember} onClick={() => decide("confirm")}>Confirm</Button>
            <Button variant="outline" disabled={!remember} onClick={() => decide("dismiss")}>Dismiss</Button>
          </>
        ) : (
          <>
            {!decision && item.status !== "rejected" && <RecordMenu item={item} title={title} onDecide={(_i, k) => decide(k)} />}
            <Button variant="outline" onClick={close}>Close</Button>
          </>
        )}
        {needs && !remember && <p className="basis-full text-sm text-muted-foreground">No company registration number, so a decision can't be saved.</p>}
      </SheetFooter>
    </SheetContent>
  );
}
