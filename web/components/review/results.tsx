"use client";

import { useMemo, useState } from "react";
import { Download } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { CompactRow, ItemCard } from "@/components/review/item-card";
import { Charts } from "@/components/review/charts";
import { StatTile } from "@/components/review/stat-tile";
import { SECTION_COPY, buildItems, flagTitle, formatMoney, formatPeriod, headline, strengthOf, strengthRank, summarise, type Item } from "@/lib/copy";
import { flagIcon } from "@/lib/icons";
import { downloadText, summaryMarkdown } from "@/lib/report-md";
import type { Memo } from "@/lib/types";
import { useRunCtx } from "@/components/run-provider";

type Sort = "strength" | "amount" | "date";

const sorters: Record<Sort, (a: Item, b: Item) => number> = {
  strength: (a, b) => strengthRank(strengthOf(b.confidence)) - strengthRank(strengthOf(a.confidence)) || (b.amount ?? 0) - (a.amount ?? 0),
  amount: (a, b) => (b.amount ?? 0) - (a.amount ?? 0),
  date: (a, b) => (b.date ?? "").localeCompare(a.date ?? ""),
};

export function Results({ memo }: { memo: Memo }) {
  const { decisions, setOpenItem, setTarget } = useRunCtx();
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState<Sort>("strength");

  const items = useMemo(() => buildItems(memo), [memo]);
  const summary = useMemo(() => summarise(items), [items]);
  const reasons = summary.byFlag.map((f) => f.flag_id);

  const visible = items.filter((i) => filter === "all" || (filter === "needs" ? i.status === "escalated" : i.flag_id === filter));
  const section = (st: Item["status"]) => visible.filter((i) => i.status === st).sort(sorters[sort]);
  const needs = section("escalated");
  const flagged = section("accepted");
  const cleared = section("suppressed");
  const aside = section("rejected");

  const card = (i: Item) => <ItemCard key={i.id} item={i} decision={decisions[i.finding.finding_id]} onOpen={setOpenItem} onDecide={(it, kind) => setTarget({ item: it, kind })} />;
  const toolsShown = items.some((i) => i.status === "accepted" || i.status === "escalated");

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-8">
      <section aria-labelledby="headline" className="grid gap-2">
        <h2 id="headline" className="text-xl leading-7 font-semibold tracking-[-0.4px] lg:text-[22px] lg:leading-7 2xl:text-2xl">
          {headline(memo.agency, summary)}
        </h2>
        <p className="text-base text-muted-foreground">
          {formatPeriod(memo.date_from, memo.date_to)}
          {summary.value != null ? ` · ${formatMoney(summary.value)} involved` : ""}
        </p>
        <div>
          <Button variant="outline" size="sm" onClick={() => downloadText(`procurelens-${memo.run_id}.md`, summaryMarkdown(memo))}>
            <Download aria-hidden strokeWidth={1.75} /> Download summary
          </Button>
        </div>
      </section>

      <section aria-label="Key numbers" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile label="Worth a second look" value={summary.worth} />
        <StatTile label="Need your decision" value={summary.needDecision} />
        {summary.value != null && <StatTile label="Value involved" value={summary.value} prefix="S$" wide />}
        <StatTile label="Cleared using your past decisions" value={summary.cleared} />
      </section>

      {summary.worth > 0 && <Charts summary={summary} />}

      {toolsShown && (
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="grid gap-2">
            <Label id="filter-label">Show</Label>
            <ToggleGroup type="single" value={filter} onValueChange={(v) => setFilter(v || "all")} aria-labelledby="filter-label" variant="outline" spacing={2} className="flex-wrap">
              <ToggleGroupItem value="all">All</ToggleGroupItem>
              {summary.needDecision > 0 && <ToggleGroupItem value="needs">Needs decision</ToggleGroupItem>}
              {reasons.length > 1 &&
                reasons.map((r) => {
                  const Icon = flagIcon(r);
                  return (
                    <ToggleGroupItem key={r} value={r} aria-label={flagTitle(r)} title={flagTitle(r)}>
                      <Icon aria-hidden strokeWidth={1.75} />
                      <span className="hidden sm:inline">{flagTitle(r)}</span>
                    </ToggleGroupItem>
                  );
                })}
            </ToggleGroup>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="sort">Sort by</Label>
            <Select value={sort} onValueChange={(v) => setSort(v as Sort)}>
              <SelectTrigger id="sort" className="w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="strength">Strength</SelectItem>
                <SelectItem value="amount">Amount</SelectItem>
                <SelectItem value="date">Date</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {summary.worth === 0 && (
        <p className="rounded-lg border border-border bg-card p-6 text-base">Nothing in this period needs a second look. You can try another agency or period.</p>
      )}

      {needs.length > 0 && (
        <section aria-labelledby="sec-needs" className="grid gap-4">
          <h2 id="sec-needs" className="text-xl leading-7 font-semibold tracking-[-0.4px]">{SECTION_COPY.escalated.title} ({needs.length})</h2>
          {needs.map(card)}
        </section>
      )}
      {flagged.length > 0 && (
        <section aria-labelledby="sec-flagged" className="grid gap-4">
          <h2 id="sec-flagged" className="text-xl leading-7 font-semibold tracking-[-0.4px]">{SECTION_COPY.accepted.title} ({flagged.length})</h2>
          {flagged.map(card)}
        </section>
      )}

      {(cleared.length > 0 || aside.length > 0) && (
        <Accordion type="multiple" className="grid gap-4">
          {cleared.length > 0 && (
            <AccordionItem value="cleared" className="rounded-lg border border-border bg-card px-6">
              <AccordionTrigger><h2 className="text-xl leading-7 font-semibold tracking-[-0.4px]">{SECTION_COPY.suppressed.title} ({cleared.length})</h2></AccordionTrigger>
              <AccordionContent>
                <ul className="divide-y divide-border">
                  {cleared.map((i) => (
                    <CompactRow key={i.id} item={i} onOpen={setOpenItem} note="Cleared by a decision you made in an earlier review" />
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>
          )}
          {aside.length > 0 && (
            <AccordionItem value="aside" className="rounded-lg border border-border bg-card px-6">
              <AccordionTrigger><h2 className="text-xl leading-7 font-semibold tracking-[-0.4px]">{SECTION_COPY.rejected.title} ({aside.length})</h2></AccordionTrigger>
              <AccordionContent>
                <ul className="divide-y divide-border">
                  {aside.map((i) => (
                    <CompactRow key={i.id} item={i} onOpen={setOpenItem} note="Not enough evidence" />
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>
          )}
        </Accordion>
      )}
    </div>
  );
}
