"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { STRENGTH_TIP, strengthOf } from "@/lib/copy";

// The tooltip also opens on tap; the same explanation is repeated in the item sheet ("How sure are we").
export function StrengthChip({ confidence }: { confidence: number }) {
  const [open, setOpen] = useState(false);
  const s = strengthOf(confidence);
  return (
    <Tooltip open={open} onOpenChange={setOpen}>
      <TooltipTrigger asChild>
        <button type="button" onClick={() => setOpen((o) => !o)} className="inline-flex min-h-11 items-center rounded-lg px-1" aria-label={`Strength: ${s}. ${STRENGTH_TIP}`}>
          <Badge variant="outline">Strength: {s}</Badge>
        </button>
      </TooltipTrigger>
      <TooltipContent>{STRENGTH_TIP}</TooltipContent>
    </Tooltip>
  );
}
