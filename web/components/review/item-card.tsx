"use client";

import { Ellipsis } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { StatusBadge } from "@/components/review/status-badge";
import { StrengthChip } from "@/components/review/strength-chip";
import { flagTitle, formatDate, formatMoney, groupTitle, whyFlagged, type Item } from "@/lib/copy";
import { flagIcon } from "@/lib/icons";
import { cn } from "@/lib/utils";
import type { DecisionRecord } from "@/lib/types";

export function RecordMenu({ item, title, onDecide, iconOnly = false }: { item: Item; title: string; onDecide: (i: Item, kind: "confirm" | "dismiss") => void; iconOnly?: boolean }) {
  const remember = canRemember(item);
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {iconOnly ? (
          <Button variant="ghost" size="icon" aria-label={`More actions for ${title}`}>
            <Ellipsis aria-hidden strokeWidth={1.75} />
          </Button>
        ) : (
          <Button variant="outline" disabled={!remember}>Record a decision</Button>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Record a decision</DropdownMenuLabel>
        <DropdownMenuItem disabled={!remember} onSelect={() => onDecide(item, "confirm")}>Confirm this needs follow-up</DropdownMenuItem>
        <DropdownMenuItem disabled={!remember} onSelect={() => onDecide(item, "dismiss")}>Dismiss this item</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function canRemember(item: Item) {
  return item.members.some((m) => !!m.uen);
}

export function ItemCard({
  item,
  decision,
  onOpen,
  onDecide,
}: {
  item: Item;
  decision?: DecisionRecord;
  onOpen: (i: Item) => void;
  onDecide: (i: Item, kind: "confirm" | "dismiss") => void;
}) {
  const Icon = flagIcon(item.flag_id);
  const needs = item.status === "escalated";
  const title = item.kind === "group" && item.group ? groupTitle(item.group) : flagTitle(item.flag_id);
  const why = item.kind === "group" ? `${item.members.length} awards, together ${formatMoney(item.amount)}.` : whyFlagged(item.finding);
  const decided = decision ? (decision.decision === "confirm" ? "confirmed" : "dismissed") : null;
  const remember = canRemember(item);

  return (
    <article className={cn("fade-up grid gap-4 rounded-lg border border-border bg-card p-6", needs && !decided && "border-l-4 border-l-warning")} aria-label={title}>
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <h3 className="flex items-start gap-2 text-lg leading-7 font-semibold">
          <Icon aria-hidden size={20} strokeWidth={1.75} className="mt-1 shrink-0 text-muted-foreground" />
          {title}
        </h3>
        <StatusBadge status={decided ?? item.status} />
      </div>

      <p className="text-base">
        <span className="font-semibold">{item.supplierLabel}</span>
        {item.amount != null && <span className="tabular-nums"> · {formatMoney(item.amount)}</span>}
        {item.date && <span className="text-muted-foreground"> · {formatDate(item.date)}</span>}
      </p>

      <p className="text-base">{why}</p>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <StrengthChip confidence={item.confidence} />
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => onOpen(item)}>
            View details
          </Button>
          {needs && !decided && (
            <>
              <Button variant="outline" size="sm" disabled={!remember} onClick={() => onDecide(item, "confirm")}>
                Confirm
              </Button>
              <Button variant="outline" size="sm" disabled={!remember} onClick={() => onDecide(item, "dismiss")}>
                Dismiss
              </Button>
            </>
          )}
          {item.status === "accepted" && !decided && (
            <RecordMenu item={item} title={title} onDecide={onDecide} iconOnly />
          )}
        </div>
      </div>
      {needs && !decided && !remember && <p className="text-sm text-muted-foreground">This item has no company registration number, so a decision can't be saved for next time.</p>}
    </article>
  );
}

// A one-line row for items that are collapsed by default (cleared earlier, set aside).
export function CompactRow({ item, onOpen, note }: { item: Item; onOpen: (i: Item) => void; note: string }) {
  const Icon = flagIcon(item.flag_id);
  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2">
      <Icon aria-hidden size={20} strokeWidth={1.75} className="shrink-0 text-muted-foreground" />
      <span className="min-w-0 flex-1 text-base">
        <span className="font-semibold">{item.supplierLabel}</span>
        <span className="text-muted-foreground">
          {" "}
          · {flagTitle(item.flag_id)}
          {item.amount != null ? ` · ${formatMoney(item.amount)}` : ""} · {note}
        </span>
      </span>
      <Button variant="ghost" size="sm" onClick={() => onOpen(item)}>
        View details
      </Button>
    </li>
  );
}
