import type { FindingStatus, TraceStatus } from "./types";

export type Tone = "neutral" | "ok" | "warn" | "bad" | "esc" | "info";

export const traceTone: Record<TraceStatus, Tone> = {
  success: "ok",
  needs_revision: "bad",
  retrying: "warn",
  escalated: "esc",
  partial_success: "warn",
  failed: "bad",
};

export const findingTone: Record<FindingStatus, Tone> = {
  accepted: "ok",
  escalated: "esc",
  suppressed: "info",
  rejected: "bad",
};

export const findingLabel: Record<FindingStatus, string> = {
  accepted: "Accepted",
  escalated: "Escalated for human review",
  suppressed: "Suppressed by memory",
  rejected: "Rejected by Critic",
};

export const FLAG_NAMES: Record<string, string> = {
  R1: "Recently incorporated supplier",
  R2: "Registry status not live",
  R3: "Shared address across suppliers",
  R4: "Repeat sub-threshold awards",
  R5: "SSIC far from tender description",
  R6: "Supplier concentration",
  R7: "Former names (informational)",
  R8: "No registry match",
  R9: "Winner not best-scored",
};

// Row border/background classes for a timeline line.
export const rowStyle: Record<TraceStatus, string> = {
  success: "border-border",
  needs_revision: "border-bad bg-bad-bg",
  retrying: "border-warn bg-warn-bg",
  escalated: "border-esc bg-esc-bg",
  partial_success: "border-warn/50",
  failed: "border-bad bg-bad-bg",
};
