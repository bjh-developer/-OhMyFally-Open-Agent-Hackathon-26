// Mirrors app/schemas.py on stream-a-core (CONTRACTS section 7.4 and 8). Optional fields are the additive extras.

export type FindingStatus = "accepted" | "escalated" | "rejected" | "suppressed";
export type TraceStatus = "success" | "needs_revision" | "retrying" | "escalated" | "partial_success" | "failed";

export interface Evidence {
  query_id: string;
  sql: string;
  row_count: number;
  rows: Record<string, unknown>[];
  source_objects: string[];
}

export interface Finding {
  finding_id: string;
  flag_id: string;
  tender_no: string;
  agency: string;
  supplier_name: string;
  uen: string | null;
  summary: string;
  confidence: number;
  status: FindingStatus;
  evidence: Evidence[];
  ago_refs: string[];
  memory_refs: string[];
  wording_checked: boolean;
  awarded_amt?: number | null;
  award_date?: string | null;
  metric_name?: string | null;
  metric_value?: string | null;
  threshold?: string | null;
  detail?: string | null;
  notes?: string[];
}

// Additive: findings that describe one pattern (R3: several awards at one shared address).
export interface FindingGroup {
  group_id: string;
  flag_id: string;
  title: string;
  detail: string;
  finding_ids: string[];
  suppliers: string[];
  n_awards: number;
  total_amt: number;
  status: FindingStatus;
  priority: number;
}

export interface Memo {
  run_id: string;
  agency: string;
  date_from: string;
  date_to: string;
  summary: string;
  findings: Finding[];
  groups?: FindingGroup[];
  limitations: string[];
  disclaimer: string;
  escalated: string[];
  stats: Record<string, unknown>;
  markdown: string;
}

export interface TraceEvent {
  timestamp: string;
  trace_id: string;
  agent_name: string;
  action: string;
  input_summary?: string;
  output_summary?: string;
  target_agent?: string | null;
  confidence?: number | null;
  retry_count?: number;
  status: TraceStatus;
  zetaris_query_ids?: string[];
  meterless_receipt_id?: string | null;
  meterless_receipt_ids?: string[];
  routed_model?: string | null;
  latency_ms?: number | null;
  egress?: unknown;
}

export interface RunRequest {
  agency: string;
  date_from: string;
  date_to: string;
  flags?: string[];
  question?: string | null;
}

// GET /runs/{id}
export interface RunView {
  run_id: string;
  status: "running" | "done" | "rejected" | "failed";
  error: string | null;
  trace_path?: string;
  memo: Memo | null;
  events: number;
}

export type Decision = "confirm" | "dismiss";
export interface DecisionRecord {
  decision: Decision;
  reason: string;
  pattern_tag?: string;
  scope: "agency" | "global";
  memoryId: string;
  at: string; // ISO time the decision was made in this browser
}

export interface AuditorDecisionBody {
  runId: string;
  finding_id: string;
  uen: string;
  flag_id: string;
  agency: string;
  decision: Decision;
  reason: string;
  pattern_tag?: string;
  scope: "agency" | "global";
}

// GET /runs/{id}/summary (app/run_summary.py). Fields added later may be missing on old runs.
export interface RunSummary {
  run_id: string;
  critiques: number;
  retries: number;
  escalations: number;
  replans: number;
  partial_success: number;
  llm_calls: number;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  duration_s: number;
  per_agent: { agent: string; calls: number; time_s: number; llm_calls: number }[];
  memory_hits?: number;
  memory_tracked?: boolean;
  cleared_by_memory?: number;
  zetaris_queries: number;
  loops: { from_agent: string; to_agent: string; reason: string; claims?: number }[];
}
