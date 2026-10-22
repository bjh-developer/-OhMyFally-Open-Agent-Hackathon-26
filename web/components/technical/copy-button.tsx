"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";

export function CopyButton({ value, label }: { value: string; label: string }) {
  const [done, setDone] = useState(false);
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      aria-label={done ? "Copied" : `Copy ${label}`}
      onClick={() => {
        void navigator.clipboard?.writeText(value);
        setDone(true);
        setTimeout(() => setDone(false), 1500);
      }}
    >
      {done ? <Check aria-hidden strokeWidth={1.75} className="text-success" /> : <Copy aria-hidden strokeWidth={1.75} />}
      <span className="sr-only" role="status">{done ? "Copied" : ""}</span>
    </Button>
  );
}

export function CopiedHint({ show }: { show: boolean }) {
  return show ? <span className="text-sm font-semibold text-success">Copied</span> : null;
}
