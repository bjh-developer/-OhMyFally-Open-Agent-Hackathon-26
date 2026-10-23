"use client";

import { useEffect } from "react";
import { Toaster as SileoToaster } from "sileo";
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { TOAST_ENGINE, dismissAllNotify } from "@/lib/notify";

// Mounts whichever toast engine notify() uses. Sileo has no Escape handler, so we add one.
export function NotifyToaster() {
  useEffect(() => {
    if (TOAST_ENGINE !== "sileo") return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && document.activeElement?.closest("[data-sileo-viewport]")) dismissAllNotify();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (TOAST_ENGINE === "sonner") return <SonnerToaster />;
  return (
    <SileoToaster
      position="top-right"
      theme="light"
      offset={{ top: 16, right: 16 }}
      options={{ duration: 5000, fill: "#ffffff", roundness: 8 }}
    />
  );
}
