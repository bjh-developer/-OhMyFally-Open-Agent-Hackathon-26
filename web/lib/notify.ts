"use client";

// One toast API for the app. Call sites use notify(); the engine behind it can be switched
// with NEXT_PUBLIC_TOAST=sonner (fallback) without touching any caller. Default: Sileo.
import { createElement } from "react";
import { CircleAlert, CircleCheck, CircleX, Info } from "lucide-react";
import { sileo } from "sileo";
import { toast as sonner } from "sonner";

export type Tone = "success" | "info" | "warning" | "error";
export type NotifyOptions = { description?: string; action?: { label: string; onClick: () => void } };

export const TOAST_ENGINE: "sileo" | "sonner" = process.env.NEXT_PUBLIC_TOAST === "sonner" ? "sonner" : "sileo";

const ICON = { success: CircleCheck, info: Info, warning: CircleAlert, error: CircleX } as const;
// MASTER: amber and red are icon colours only; text stays in foreground tokens.
const ICON_COLOR = { success: "var(--success)", info: "var(--primary)", warning: "var(--warning)", error: "var(--destructive)" } as const;
const DURATION = { success: 5000, info: 5000, warning: 6000, error: 8000 } as const;

export function notify(tone: Tone, title: string, opts: NotifyOptions = {}): string | number {
  const icon = createElement(ICON[tone], { className: "size-4", strokeWidth: 1.75, style: { color: ICON_COLOR[tone] }, "aria-hidden": true });
  if (TOAST_ENGINE === "sonner") {
    return sonner[tone](title, {
      description: opts.description,
      icon,
      duration: DURATION[tone],
      action: opts.action && { label: opts.action.label, onClick: opts.action.onClick },
    });
  }
  return sileo[tone]({
    title,
    description: opts.description,
    icon,
    duration: DURATION[tone],
    button: opts.action && { title: opts.action.label, onClick: opts.action.onClick },
  });
}

export function dismissAllNotify(): void {
  if (TOAST_ENGINE === "sonner") sonner.dismiss();
  else sileo.clear();
}
