// HTTP front for H-MEM: implements docs/agents/CONTRACTS.md section 6.
// All memory behaviour lives in src/index.ts (HMEM); this file only maps the
// contract onto it, tags records with agency/uen/flag_id scoping, and mirrors
// the trust ledger to logs/hmem-ledger.jsonl.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Hono } from "hono";
import type { Context } from "hono";
import { serve } from "@hono/node-server";
import { HMEM } from "./index.ts";
import type { FeedbackKind, LedgerEntry, MemoryLayer, MemoryRecord, MemoryType } from "./index.ts";

const here = path.dirname(fileURLToPath(import.meta.url));

const MEMORY_TYPES: MemoryType[] = ["personal", "factual", "preference", "general"];
const MEMORY_LAYERS: MemoryLayer[] = ["short_term", "working", "long_term"];
const SIGNALS: FeedbackKind[] = ["helpful", "not_helpful", "wrong"];
const META_KEYS = ["agency", "uen", "flag_id", "tender_no"] as const;

export interface AppOptions {
  stateDir: string;            // state.json + ledger.jsonl live here (Docker volume)
  ledgerLog?: string;          // JSONL mirror for the repo's logs/ folder; skipped when unset
  clock?: () => number;
  conformanceStatusFile?: string;
}

class HttpError extends Error {
  constructor(public status: 400 | 404, message: string) {
    super(message);
  }
}

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);

function str(body: Record<string, unknown>, key: string, required = false): string | undefined {
  const v = body[key];
  if (v === undefined || v === null || v === "") {
    if (required) throw new HttpError(400, `${key} is required`);
    return undefined;
  }
  if (typeof v !== "string") throw new HttpError(400, `${key} must be a string`);
  return v;
}

function strList(body: Record<string, unknown>, key: string): string[] | undefined {
  const v = body[key];
  if (v === undefined || v === null) return undefined;
  if (!Array.isArray(v) || v.some((x) => typeof x !== "string")) throw new HttpError(400, `${key} must be an array of strings`);
  return v as string[];
}

function oneOf<T extends string>(body: Record<string, unknown>, key: string, allowed: readonly T[], required = false): T | undefined {
  const v = str(body, key, required);
  if (v === undefined) return undefined;
  if (!(allowed as readonly string[]).includes(v)) throw new HttpError(400, `${key} must be one of: ${allowed.join(", ")}`);
  return v as T;
}

// Meta values are stored as strings; numbers (e.g. a tender amount) are coerced rather than rejected.
function metaFrom(v: unknown): Record<string, string> {
  if (v === undefined || v === null) return {};
  if (!isObj(v)) throw new HttpError(400, "meta must be an object");
  const out: Record<string, string> = {};
  for (const [k, val] of Object.entries(v)) if (val !== undefined && val !== null) out[k] = String(val);
  return out;
}

async function readBody(c: Context): Promise<Record<string, unknown>> {
  let body: unknown;
  try {
    body = await c.req.json();
  } catch {
    throw new HttpError(400, "request body must be JSON");
  }
  if (!isObj(body)) throw new HttpError(400, "request body must be a JSON object");
  return body;
}

export function createApp(opts: AppOptions) {
  const hmem = new HMEM({ clock: opts.clock, persistDir: opts.stateDir, actor: "hmem-service" });
  const ts = (e: LedgerEntry) => ({ ...e, ts: new Date(e.timestamp).toISOString() });

  if (opts.ledgerLog) {
    const file = opts.ledgerLog;
    fs.mkdirSync(path.dirname(file), { recursive: true });
    hmem.ledger.onEntry = (e) => fs.appendFileSync(file, JSON.stringify(ts(e)) + "\n", "utf-8");
  }

  // Everything is synchronous, so setting the ledger context around one call is race-free.
  const withContext = <T>(runId: string | undefined, agentId: string | undefined, fn: () => T): T => {
    hmem.ledger.context = { ...(runId ? { runId } : {}), ...(agentId ? { agentId } : {}) };
    try {
      return fn();
    } finally {
      hmem.ledger.context = {};
    }
  };

  const app = new Hono();

  app.onError((err, c) => {
    if (err instanceof HttpError) return c.json({ error: err.message }, err.status);
    // The reference throws plain Errors for unknown ids and sourceless records; surface those as client errors.
    if (/^H-MEM: unknown memory id/.test(err.message)) return c.json({ error: err.message }, 404);
    if (/^H-MEM:/.test(err.message)) return c.json({ error: err.message }, 400);
    console.error(err);
    return c.json({ error: "internal error" }, 500);
  });

  app.get("/healthz", (c) => {
    let conformance: "pass" | "unknown" = "unknown";
    try {
      if (opts.conformanceStatusFile && fs.readFileSync(opts.conformanceStatusFile, "utf-8").trim() === "pass") conformance = "pass";
    } catch {
      /* no status file: conformance has not been recorded for this build */
    }
    return c.json({ ok: true, conformance });
  });

  app.post("/add", async (c) => {
    const body = await readBody(c);
    const content = str(body, "content", true)!;
    const source = str(body, "source", true)!;
    const type = oneOf(body, "type", MEMORY_TYPES);
    const layer = oneOf(body, "layer", MEMORY_LAYERS);
    const confidence = body.confidence;
    if (confidence !== undefined && (typeof confidence !== "number" || confidence < 0 || confidence > 1)) {
      throw new HttpError(400, "confidence must be a number between 0 and 1");
    }
    const agentId = str(body, "agentId");
    const runId = str(body, "runId");
    const meta = metaFrom(body.meta);
    const now = hmem.clock();
    const record = withContext(runId, agentId, () =>
      hmem.store.add({
        content,
        type,
        layer,
        tags: strList(body, "tags"),
        confidence: confidence as number | undefined,
        source,
        provenance: { origin: "model_response", learnedAt: now, label: source, ...(runId ? { refs: [runId] } : {}) },
        entities: strList(body, "entities"),
        meta,
        agentId,
        runId,
      })
    );
    return c.json({ id: record.id });
  });

  app.post("/query", async (c) => {
    const body = await readBody(c);
    const filters = isObj(body.filters) ? body.filters : {};
    const f = {
      agency: str(filters, "agency"),
      uen: str(filters, "uen"),
      flag_id: str(filters, "flag_id"),
      pattern_tag: str(filters, "pattern_tag"), // optional extension: same-pattern recall
    };
    const query = str(body, "query") ?? Object.values(f).filter(Boolean).join(" ");
    if (!query) throw new HttpError(400, "query or filters is required");
    const topN = body.topN === undefined ? 5 : body.topN;
    if (typeof topN !== "number" || !Number.isInteger(topN) || topN < 1) throw new HttpError(400, "topN must be a positive integer");

    // Scoping: uen / flag_id / pattern_tag must match exactly. A memory recorded for another agency is
    // invisible unless it was stored with scope=global; memories with no agency are not agency-bound.
    const visible = (m: MemoryRecord): boolean => {
      const meta = m.meta ?? {};
      if (f.agency && meta.agency && meta.agency !== f.agency && meta.scope !== "global") return false;
      if (f.uen && meta.uen !== f.uen) return false;
      if (f.flag_id && meta.flag_id !== f.flag_id) return false;
      if (f.pattern_tag && meta.pattern_tag !== f.pattern_tag) return false;
      return true;
    };
    // An exact identity filter is itself the match, so it bypasses the semantic score threshold.
    const exact = Boolean(f.uen || f.flag_id || f.pattern_tag);

    const result = withContext(str(body, "runId"), str(body, "agentId"), () => {
      const r = hmem.retrieval.query(query, { topN, filter: visible, ...(exact ? { threshold: 0 } : {}) });
      hmem.store.persist(); // reads bump accessCount; keep it across restarts
      return r;
    });
    return c.json({
      memories: result.memories.map(({ memory: m, relevance }) => ({
        id: m.id,
        content: m.content,
        score: Number(relevance.toFixed(4)),
        meta: m.meta ?? {},
        provenance: m.provenance,
        confidence: m.confidence,
        layer: m.layer,
        tags: m.tags,
        supersededBy: m.supersededBy ?? null,
      })),
      trace: { retrievalReason: result.trace.retrievalReason, strategy: result.trace.strategy },
    });
  });

  app.post("/feedback", async (c) => {
    const body = await readBody(c);
    const memoryId = str(body, "memoryId", true)!;
    const signal = oneOf(body, "signal", SIGNALS, true)!;
    withContext(str(body, "runId"), str(body, "agentId"), () => hmem.retrieval.feedback(memoryId, signal));
    return c.json({ ok: true, confidence: hmem.store.get(memoryId)!.confidence });
  });

  app.post("/auditor-decision", async (c) => {
    const body = await readBody(c);
    const runId = str(body, "runId", true)!;
    const finding_id = str(body, "finding_id", true)!;
    const uen = str(body, "uen", true)!;
    const flag_id = str(body, "flag_id", true)!;
    const agency = str(body, "agency", true)!;
    const decision = oneOf(body, "decision", ["confirm", "dismiss"] as const, true)!;
    const reason = str(body, "reason", true)!;
    const scope = oneOf(body, "scope", ["agency", "global"] as const, true)!;
    const pattern_tag = str(body, "pattern_tag");
    const now = hmem.clock();

    const record = withContext(runId, "auditor", () => {
      // A later decision on the same (uen, flag_id, agency) supersedes the earlier one, so the
      // reference's superseded-penalty ranks the latest ruling first.
      const prior = hmem.store
        .all()
        .filter((m) => m.provenance.origin === "auditor" && !m.supersededBy)
        .filter((m) => m.meta?.uen === uen && m.meta?.flag_id === flag_id && m.meta?.agency === agency);
      const rec = hmem.store.add({
        content: reason,
        type: "factual",
        layer: "long_term",
        confidence: 0.95,
        source: `auditor:${runId}:${finding_id}`,
        provenance: { origin: "auditor", learnedAt: now, label: `auditor ${decision} ${flag_id} ${uen}`, refs: [runId, finding_id] },
        tags: [`decision:${decision}`, flag_id, ...(pattern_tag ? [pattern_tag] : [])],
        entities: [uen, flag_id],
        meta: { decision, finding_id, uen, flag_id, agency, scope, reason, decided_at: new Date(now).toISOString(), ...(pattern_tag ? { pattern_tag } : {}) },
        agentId: "auditor",
        runId,
        ...(prior[0] ? { supersedes: prior[0].id } : {}),
      });
      for (const old of prior) hmem.store.update(old.id, { supersededBy: rec.id });
      return rec;
    });
    return c.json({ memoryId: record.id });
  });

  app.get("/ledger", (c) => {
    const runId = c.req.query("runId");
    const lines = hmem.ledger
      .all()
      .filter((e) => !runId || e.runId === runId)
      .map((e) => JSON.stringify(ts(e)));
    return c.body(lines.length ? lines.join("\n") + "\n" : "", 200, { "content-type": "application/x-ndjson" });
  });

  return { app, hmem };
}

// Run as a server only when executed directly (tests import createApp).
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT ?? 7070);
  const stateDir = path.resolve(process.env.HMEM_STATE_DIR ?? path.join(here, "..", "state"));
  const ledgerLog = path.resolve(process.env.HMEM_LEDGER_LOG ?? path.join(here, "..", "..", "..", "logs", "hmem-ledger.jsonl"));
  const conformanceStatusFile = path.resolve(process.env.HMEM_CONFORMANCE_FILE ?? path.join(here, "..", "conformance.status"));
  const { app } = createApp({ stateDir, ledgerLog, conformanceStatusFile });
  serve({ fetch: app.fetch, port, hostname: process.env.HOST ?? "0.0.0.0" }, (info) => {
    console.log(`hmem listening on :${info.port} state=${stateDir} ledger=${ledgerLog}`);
  });
}
