# Web UI (port 3100)

Next.js 15 + Tailwind v4, with shadcn-style components (Radix primitives, `class-variance-authority`) in `components/ui/`.

```bash
cd web
cp .env.example .env.local   # optional; defaults match CONTRACTS section 4
npm install
npm run dev                  # http://127.0.0.1:3100 (Zetaris owns 3000)
npm run build
```

- **Run API:** the browser calls `POST /run` and the SSE stream `GET /runs/{id}/events` on `NEXT_PUBLIC_API_URL`
  (default `http://127.0.0.1:8000`; the API's CORS allows port 3100). Each SSE `data:` line is a trace event (CONTRACTS section 8);
  `event: end` means the run finished, then the UI fetches `GET /runs/{id}` for the memo. The server replays the whole trace on every
  reconnect, so the client skips lines it already has.
- **Auditor decisions:** Confirm and Dismiss post to `app/api/auditor-decision/route.ts`, which forwards to H-MEM
  `POST /auditor-decision` at `HMEM_URL` (server-side, default `http://127.0.0.1:7070`). A finding without a UEN cannot be
  remembered (H-MEM recalls by uen, flag and agency), so its buttons are disabled.
- **Mock replay:** "Replay mock run" plays `mocks/run_demo.json` (fictional suppliers only; includes a Critic rejection, a retry,
  an escalation and a finding suppressed by memory). Decisions on a mock run are shown but not sent to H-MEM.
- **AGO excerpts:** `lib/ago-index.json` is a snapshot of `data/ago/` so the evidence drawer can show the quoted text and a page link.
  Regenerate it if `data/ago/` changes.
