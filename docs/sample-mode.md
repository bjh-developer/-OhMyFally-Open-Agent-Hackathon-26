# How SAMPLE_MODE works

Part of the [ProcureLens README](../README.md).

`SAMPLE_MODE` is read in [app/adapters/config.py](../app/adapters/config.py) and acted on in [app/replay.py](../app/replay.py) and the
two adapters. The default is **true** when the variable is unset.

| Situation | What happens |
|---|---|
| `SAMPLE_MODE=true`, **no** Zetaris key **and** no Nightshift token (unset, empty or an `.env.example` placeholder such as `your-...`) | **Offline.** No socket is opened. Every Zetaris query and model call is answered from `data/replay/<set>/`. H-MEM is skipped (trace line `memory_skipped`). |
| `SAMPLE_MODE=true` and **at least one** real credential | **Live first.** Services are called normally. A recording answers only after an *outage-type* failure: Zetaris connection error, timeout or HTTP 5xx after retries; Nightshift connection error, timeout, or HTTP 408, 425, 429, 499 or 5xx after retries. A 4xx, a bad-JSON reply or the call cap is never replayed. After the first outage a 30-second breaker serves recordings directly. |
| `SAMPLE_MODE=false` | Never replays. A failed service is a failed step. |

So a real `.env` with credentials does **not** put you offline even with `SAMPLE_MODE=true`. We checked this by pointing both
URLs at a closed port with dummy credentials: the run tried the live services first (about 17 seconds of retries), then finished
from the recordings and labelled them.

**What is replayed.** Five recorded sets under `data/replay/`, one per file in `input_examples/`, captured from real runs on 23-24 Oct:
`hdb-fy2425` (example 1), `pa-2024` (example 2), `nparks-2023-2025` (example 3), `pa-fy2125` (example 4) and `synthetic-2025` (`example_remaining`). Each holds
the Zetaris result for every SQL statement (keyed by a hash of the statement) and every Nightshift reply, with the original
receipt id and routed model.

**What is real in an offline run.** The Gate, Planner, Resolver, Analyst, Critic, Risk and Reporter code, the red-flag logic over the
returned rows, the Critic's checks, the wording gate and the memo rendering all execute. What is not live is the *source data and
model text*: they come from the recording.

**Labels, so a recording is never mistaken for a live answer.**

- Ids carry a `replay:` prefix (`replay:<hash>` for Zetaris, `replay:rcpt_req_...` for Nightshift), the model name ends in
  `(replayed)`, and trace events carry `"replayed": true` with `[replayed from recorded run]` in the summary.
- The memo gets a limitation line: *"Replayed from a recorded run: services were offline. N Zetaris result(s) and M Nightshift
  reply(ies) came from the recorded set '...', not from live services."* The same counts are in `stats.replayed`.
- A model call with no recorded reply fails like an outage, so that agent uses its **rule-based fallback** (deterministic scores,
  template narrative, no model claim check), and the memo says how many calls did.

**What is refused, not faked.** Offline, a request whose agency and period do not match a recorded set is rejected at the Gate
(CLI exit code 2; API `422 request_rejected`) with the list of what is recorded. The match is on **agency and period only**: if
you keep the agency and period but ask for different flags (for example `--flags R2` on the People's Association set), any query
that was not recorded is reported as a failed check in the trace and memo; nothing is invented. Offline runs do not call H-MEM,
so they never show memory suppression; the live examples in `output_examples/` do.

`output_examples/` holds saved outputs of **live** runs (Zetaris, Nightshift and H-MEM up). They are examples to read, and the
code never returns them.
