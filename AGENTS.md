# Agent instructions (Cursor and other coding agents)

Read these before writing any code in this repo:

1. `docs/agents/CONTRACTS.md`: the shared interfaces, ports, env vars, schemas and hard rules. It always wins.
2. Your owner's file:
   - Rae: `docs/agents/rae.md` (H-MEM service, red-flag rules, wording, AGO excerpts, UI components, pitch)
   - Inchara: `docs/agents/inchara.md` (data pipeline, Entity Resolver, red-flag SQL, evaluation)
   - Joon Hao: `docs/agents/joon-hao.md` (orchestration, adapters, tracing, API, UI, integration, submission)

Hard rules, repeated so they're never missed:
- No product code before **22 Oct 2026, 08:00 SGT**.
- Never print or commit secrets; `.env` is gitignored.
- All data goes through Zetaris, and all LLM calls go through Meterless Nightshift.
- Findings say "anomaly for review", never "fraud".
