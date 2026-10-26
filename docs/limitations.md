# Limitations and responsible AI

Part of the [ProcureLens README](../README.md).

- **R4 is partial.** GeBIZ here has no quotation (ETQ) records, so splitting under the quotation band is invisible. R7 is not implemented.
- **The Resolver is only as good as its test.** The 100/100 score is on a selected, agent-reviewed, in-sample label set with no human
  review; fuzzy and LLM-tie-break accuracy are not established (the labelled set has none of those methods). Only 2 live tie-breaks have happened.
  Names with no local legal suffix that are absent from our ACRA subset become "out of scope", not R8. The ACRA data is a name-matched
  subset, so a renamed company whose old and new names share no first word can be missed.
- **Noisy flags.** R3 produces many benign matches (shared buildings and business centres), R2 uses current status only, and R5 and R6 are uncalibrated.
  The Critic and Risk agents reduce but do not remove this. SQL-stage precision is 28.6% on a 30-finding human-reviewed sample (9.5% before the round-1 fixes).
- **Offline mode covers only the five recorded inputs**, and a missing recording degrades to rule-based text.
- **Nightshift 499 and 502 errors happen.** The agent retries, then falls back to rule-based text. The committed
  `output_examples/example_3` memo shows it: its Reporter narrative failed with HTTP 499, so the memo says "narrative unavailable"
  and lists findings straight from the SQL evidence.
- **R5 needs the local model**, prepared once with `prepare_r5.py --download-model`, because Nightshift has no embeddings endpoint.
- **Live runs are slow**: about 1 to 5 minutes for the examples.
- **Not production-ready.** It is a hackathon prototype: no authentication on the API, an in-process run registry (finished runs are re-read from `logs/` after a restart), a local single-node setup.
- **Human review is required.** Every output is a lead for an auditor to check, not a conclusion.

## Responsible AI

- **Wording is enforced in code, not just in prompts.** [data/rules/wording.yaml](../data/rules/wording.yaml) bans terms such as
  fraud, corrupt, illegal, criminal, guilty, scam, bribe, collusion and kickback. The Risk agent checks every finding; the Reporter
  rewrites any hit with a neutral replacement; the prompts require "anomaly for review" and "may indicate".
- **Escalation to a human.** Findings are escalated rather than accepted when: confidence is below 0.7; the flag is a should-have
  rather than a must-have (R5 is capped at 0.6 and always escalated); a shared address is quiet or has a missing unit; or the Critic
  cannot verify a summary after its retries. The memo lists escalated items, and the web UI has a review queue with Confirm and Dismiss.
- **Every claim has evidence.** Each finding cites a Zetaris query id, the SQL and the rows, plus AGO context. The Critic must reproduce it first.
- **Disclaimer on every memo:** *"Automated screening output. Each item is an anomaly for review that may indicate a procurement-integrity
  concern, and requires auditor judgement. It is not a finding of wrongdoing."*
- **Limitations travel with the result.** Each memo lists the limitation of every flag that ran, plus replay and fallback notes.
- **Privacy.** Minimised public sample, no real personal data in the planted cases, a pseudonymised public view, and no personal data in logs by design.
