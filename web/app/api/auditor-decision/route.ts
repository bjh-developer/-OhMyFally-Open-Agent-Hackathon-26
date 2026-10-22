import { NextResponse } from "next/server";

// Browser -> this route -> H-MEM POST /auditor-decision (CONTRACTS section 6).
// The proxy keeps H-MEM off the browser's CORS path and lets HMEM_URL stay server-side.
const HMEM_URL = (process.env.HMEM_URL ?? "http://127.0.0.1:7070").replace(/\/$/, "");

const REQUIRED = ["runId", "finding_id", "uen", "flag_id", "agency", "decision", "reason", "scope"] as const;

export async function POST(req: Request) {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "body must be JSON" }, { status: 400 });
  }
  for (const k of REQUIRED) {
    if (typeof body[k] !== "string" || !(body[k] as string).trim()) {
      return NextResponse.json({ error: `${k} is required` }, { status: 400 });
    }
  }
  if (!["confirm", "dismiss"].includes(body.decision as string)) {
    return NextResponse.json({ error: "decision must be confirm or dismiss" }, { status: 400 });
  }
  if (!["agency", "global"].includes(body.scope as string)) {
    return NextResponse.json({ error: "scope must be agency or global" }, { status: 400 });
  }
  const payload: Record<string, string> = {};
  for (const k of REQUIRED) payload[k] = (body[k] as string).trim();
  if (typeof body.pattern_tag === "string" && body.pattern_tag.trim()) payload.pattern_tag = body.pattern_tag.trim();

  try {
    const res = await fetch(`${HMEM_URL}/auditor-decision`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(10_000),
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) return NextResponse.json({ error: json.error ?? `H-MEM returned ${res.status}` }, { status: res.status });
    return NextResponse.json(json);
  } catch {
    return NextResponse.json({ error: "H-MEM service is unreachable" }, { status: 502 });
  }
}
