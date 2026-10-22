# Procurement Integrity Investigator

OhMyFally, Open Agent Hackathon 2026, Track 02 (The Agent That Can Explain Why).

A multi-agent LangGraph system that tells an agency auditor which procurement awards need review, and why.
Data goes through **Zetaris**, reasoning through **Nemotron via Meterless Nightshift**, auditor feedback into **Meterless H-MEM**.

> Stub: full setup, usage, limitations and sponsor explanation land on D3. See `docs/agents/CONTRACTS.md` for the interfaces.

## Quick start (D1 state)

```bash
cp .env.example .env            # fill in the Zetaris and Nightshift values
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d            # needs Zetaris running first (external network zetaris_default)
python scripts/smoke_test.py    # 3 checks: Zetaris REST, Nightshift deep, Nightshift fast
python scripts/zsql.py "SELECT 1"
```

Findings are framed as "anomaly for review", never as fraud.
