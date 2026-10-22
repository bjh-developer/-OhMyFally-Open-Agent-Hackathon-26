import type { AuditorDecisionBody, RunRequest, RunView } from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

async function readError(res: Response): Promise<string> {
  try {
    const j = await res.json();
    const d = j.detail ?? j.error;
    return typeof d === "string" ? d : JSON.stringify(d);
  } catch {
    return `HTTP ${res.status}`;
  }
}

export async function startRun(req: RunRequest): Promise<RunView> {
  const res = await fetch(`${API_URL}/run`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(req),
    signal: AbortSignal.timeout(20_000),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function getRun(runId: string): Promise<RunView> {
  const res = await fetch(`${API_URL}/runs/${encodeURIComponent(runId)}`, { signal: AbortSignal.timeout(20_000) });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export const eventsUrl = (runId: string) => `${API_URL}/runs/${encodeURIComponent(runId)}/events`;

export async function postDecision(body: AuditorDecisionBody): Promise<{ memoryId: string }> {
  const res = await fetch("/api/auditor-decision", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(15_000),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}
