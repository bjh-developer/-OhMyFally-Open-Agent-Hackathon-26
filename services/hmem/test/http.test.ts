import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createApp } from "../src/server.ts";

let dir: string;
let ledgerLog: string;
const open = () => createApp({ stateDir: path.join(dir, "state"), ledgerLog }).app;
type App = ReturnType<typeof open>;

const post = async (app: App, url: string, body: unknown) => {
  const res = await app.request(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  return { status: res.status, json: (await res.json()) as any };
};

const dismiss = (app: App, over: Record<string, unknown> = {}) =>
  post(app, "/auditor-decision", {
    runId: "run_1",
    finding_id: "F-1",
    uen: "201912345A",
    flag_id: "R1",
    agency: "Ministry of Health",
    decision: "dismiss",
    reason: "Newly incorporated vendor is a known spin-off of the incumbent under a framework agreement.",
    scope: "agency",
    ...over,
  });

const ids = (r: { json: any }) => r.json.memories.map((m: any) => m.id);

beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), "hmem-http-"));
  ledgerLog = path.join(dir, "logs", "hmem-ledger.jsonl");
});
afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));

describe("health", () => {
  it("reports ok and conformance unknown when no status file was recorded", async () => {
    const res = await open().request("/healthz");
    expect(await res.json()).toEqual({ ok: true, conformance: "unknown" });
  });

  it("reports conformance pass when the build recorded it", async () => {
    const file = path.join(dir, "conformance.status");
    fs.writeFileSync(file, "pass\n");
    const { app } = createApp({ stateDir: path.join(dir, "state"), conformanceStatusFile: file });
    expect(await (await app.request("/healthz")).json()).toEqual({ ok: true, conformance: "pass" });
  });
});

describe("add and query", () => {
  it("returns an added memory from a query, with meta and provenance", async () => {
    const app = open();
    const added = await post(app, "/add", {
      content: "Vendor Zyloq Engineering won three sub-S$90k awards at the Ministry of Health in one quarter",
      type: "factual",
      layer: "working",
      tags: ["R4"],
      source: "critic",
      confidence: 0.8,
      agentId: "critic",
      runId: "run_1",
      entities: ["zyloq"],
      meta: { agency: "Ministry of Health", uen: "201912345A", flag_id: "R4", tender_no: "MOH000ETT25000001" },
    });
    expect(added.status).toBe(200);
    expect(added.json.id).toMatch(/^mem-/);

    const q = await post(app, "/query", { query: "Zyloq Engineering sub-S$90k awards", topN: 5, filters: { agency: "Ministry of Health" }, agentId: "critic", runId: "run_2" });
    expect(q.status).toBe(200);
    expect(ids(q)).toContain(added.json.id);
    const m = q.json.memories.find((x: any) => x.id === added.json.id);
    expect(m.meta).toMatchObject({ agency: "Ministry of Health", uen: "201912345A", flag_id: "R4", tender_no: "MOH000ETT25000001" });
    expect(m.provenance.label).toBe("critic");
    expect(typeof m.score).toBe("number");
    expect(q.json.trace.strategy).toBeTruthy();
    expect(q.json.trace.retrievalReason).toBeTruthy();
  });

  it("rejects bad input with 400 and unknown feedback ids with 404", async () => {
    const app = open();
    expect((await post(app, "/add", { content: "no source" })).status).toBe(400);
    expect((await post(app, "/add", { content: "x", source: "s", type: "nope" })).status).toBe(400);
    expect((await post(app, "/query", {})).status).toBe(400);
    expect((await post(app, "/feedback", { memoryId: "mem-999", signal: "helpful" })).status).toBe(404);
    expect((await post(app, "/feedback", { memoryId: "mem-1", signal: "great" })).status).toBe(400);
    expect((await post(app, "/auditor-decision", { runId: "r" })).status).toBe(400);
  });
});

describe("feedback", () => {
  it("applies the exact reference deltas and returns the new confidence", async () => {
    const app = open();
    const { json } = await post(app, "/add", { content: "check the deploy window", source: "t", confidence: 0.7 });
    const helpful = await post(app, "/feedback", { memoryId: json.id, signal: "helpful", agentId: "critic", runId: "run_1" });
    expect(helpful.json.ok).toBe(true);
    expect(helpful.json.confidence).toBeCloseTo(0.75, 10);
    expect((await post(app, "/feedback", { memoryId: json.id, signal: "wrong" })).json.confidence).toBeCloseTo(0.55, 10);
  });
});

describe("auditor decisions", () => {
  it("recalls an exact (uen, flag_id, agency) dismiss as a long_term auditor memory", async () => {
    const app = open();
    const d = await dismiss(app);
    expect(d.status).toBe(200);

    // The query text deliberately shares no words with the stored reason: the exact filters are the match.
    const q = await post(app, "/query", {
      query: "supplier incorporated shortly before award",
      filters: { agency: "Ministry of Health", uen: "201912345A", flag_id: "R1" },
      agentId: "critic",
      runId: "run_2",
    });
    expect(ids(q)).toEqual([d.json.memoryId]);
    const m = q.json.memories[0];
    expect(m.meta).toMatchObject({ decision: "dismiss", uen: "201912345A", flag_id: "R1", agency: "Ministry of Health", scope: "agency", finding_id: "F-1" });
    expect(m.provenance.origin).toBe("auditor");
    expect(m.layer).toBe("long_term");
    expect(m.content).toMatch(/spin-off/);
  });

  it("does not match a different uen or flag_id", async () => {
    const app = open();
    await dismiss(app);
    for (const filters of [
      { agency: "Ministry of Health", uen: "200000000Z", flag_id: "R1" },
      { agency: "Ministry of Health", uen: "201912345A", flag_id: "R2" },
    ]) {
      expect(ids(await post(app, "/query", { query: "supplier incorporated shortly before award", filters }))).toEqual([]);
    }
  });

  it("keeps an agency-scoped memory out of other agencies, but lets a global one cross", async () => {
    const app = open();
    const local = await dismiss(app);
    const global = await dismiss(app, { agency: "Ministry of Health", uen: "201912345B", scope: "global", pattern_tag: "framework-spinoff" });

    const other = await post(app, "/query", {
      query: "supplier incorporated shortly before award",
      filters: { agency: "Ministry of Education", flag_id: "R1" },
    });
    expect(ids(other)).toEqual([global.json.memoryId]);
    expect(ids(other)).not.toContain(local.json.memoryId);

    const same = await post(app, "/query", { query: "supplier incorporated shortly before award", filters: { agency: "Ministry of Health", flag_id: "R1" } });
    expect(ids(same).sort()).toEqual([local.json.memoryId, global.json.memoryId].sort());
  });

  it("recalls a same-agency pattern_tag and ranks the latest ruling on a finding first", async () => {
    const app = open();
    const first = await dismiss(app, { pattern_tag: "framework-spinoff" });
    const second = await dismiss(app, { decision: "confirm", reason: "Reviewed again: not a spin-off after all.", pattern_tag: "framework-spinoff" });
    const q = await post(app, "/query", {
      query: "framework spinoff",
      filters: { agency: "Ministry of Health", uen: "201912345A", flag_id: "R1" },
    });
    expect(ids(q)).toEqual([second.json.memoryId, first.json.memoryId]);
    expect(q.json.memories[1].supersededBy).toBe(second.json.memoryId);

    const byPattern = await post(app, "/query", { query: "framework spinoff", filters: { agency: "Ministry of Health", pattern_tag: "framework-spinoff" } });
    expect(ids(byPattern)).toContain(second.json.memoryId);
    expect(ids(await post(app, "/query", { query: "framework spinoff", filters: { agency: "Ministry of Education", pattern_tag: "framework-spinoff" } }))).toEqual([]);
  });
});

describe("persistence", () => {
  it("keeps memories, confidence and supersession across a restart", async () => {
    const first = open();
    const d = await dismiss(first);
    const added = await post(first, "/add", { content: "restart canary memory", source: "t", confidence: 0.7, meta: { agency: "Ministry of Health" } });
    await post(first, "/feedback", { memoryId: added.json.id, signal: "helpful" });

    const second = open(); // a new process reading the same state dir
    const q = await post(second, "/query", {
      query: "supplier incorporated shortly before award",
      filters: { agency: "Ministry of Health", uen: "201912345A", flag_id: "R1" },
    });
    expect(ids(q)).toEqual([d.json.memoryId]);
    expect(q.json.memories[0].meta.decision).toBe("dismiss");

    const canary = await post(second, "/query", { query: "restart canary memory", filters: { agency: "Ministry of Health" } });
    expect(canary.json.memories.find((m: any) => m.id === added.json.id).confidence).toBeCloseTo(0.75, 10);

    // ids keep counting from where they left off instead of colliding.
    const next = await post(second, "/add", { content: "after restart", source: "t" });
    expect(next.json.id).not.toBe(added.json.id);
    expect(next.json.id).not.toBe(d.json.memoryId);
  });
});

describe("ledger", () => {
  it("is filterable by runId, JSONL, and mirrored to the logs file", async () => {
    const app = open();
    const d = await dismiss(app, { runId: "run_dismiss" });
    await post(app, "/query", { query: "x", filters: { uen: "201912345A", flag_id: "R1", agency: "Ministry of Health" }, runId: "run_read", agentId: "critic" });

    const res = await app.request("/ledger?runId=run_dismiss");
    expect(res.headers.get("content-type")).toContain("ndjson");
    const lines = (await res.text()).trim().split("\n").map((l) => JSON.parse(l));
    expect(lines.length).toBeGreaterThan(0);
    expect(lines.every((l) => l.runId === "run_dismiss")).toBe(true);
    expect(lines.map((l) => l.action)).toContain("create");
    expect(lines.find((l) => l.action === "create").memoryId).toBe(d.json.memoryId);

    const read = (await (await app.request("/ledger?runId=run_read")).text()).trim().split("\n").map((l) => JSON.parse(l));
    expect(read.map((l) => l.action)).toEqual(["read"]);
    expect(read[0]).toMatchObject({ memoryId: d.json.memoryId, agentId: "critic" });

    expect(await (await app.request("/ledger?runId=nobody")).text()).toBe("");

    const mirrored = fs.readFileSync(ledgerLog, "utf-8").trim().split("\n").map((l) => JSON.parse(l));
    const all = (await (await app.request("/ledger")).text()).trim().split("\n");
    expect(mirrored).toHaveLength(all.length);
    expect(mirrored[0].ts).toMatch(/^\d{4}-\d\d-\d\dT/);
  });
});
