# UI/UX redesign plan: ProcureLens (web/)

**Status:** draft for Joon Hao's approval, 22 Oct 2026.
**Read first:** `design-system/MASTER.md` (tokens, type, words, components). It wins on any conflict with this plan.

## Why

The current UI (audited 22 Oct; screenshots are in the session scratchpad) is built for engineers:
- an agent timeline dominates the screen;
- there is no overview;
- the same ~40-word disclaimer repeats on every item;
- raw SQL is the first thing in the evidence drawer;
- jargon is everywhere (H-MEM, UEN, Critic, query IDs);
- 11–12px text, and touch targets of 22–32px;
- horizontal overflow on mobile;
- no loading feedback.

**Goal:** a non-technical auditor understands the result at a glance, knows exactly which items need their decision, and can still open the technical detail if they want it, as judges will.

## Scope and constraints

**Scope**
- **Only `web/`** changes.
- **No backend or API changes.** Use the existing endpoints and schemas:
  - `POST /run`
  - `GET /runs/{id}`
  - `GET /runs/{id}/events` (SSE)
  - H-MEM `POST /auditor-decision`, via the existing proxy route `web/app/api/auditor-decision/route.ts`
- If a field is missing (for example "awards checked"), omit that UI element. Don't invent data.

**Keep**
- the mock replay (fix its agency mismatch: the replay sets the form to the mock's agency);
- the CSRF protection in the decision route;
- deep linking by run id;
- the Markdown download (rewritten in plain language).

**Rules**
- Light theme only.
- Lucide icons only.
- No SGDS identity elements.
- No secrets in client code.

## Information architecture

**App shell**
- **Top bar:** ProcureLens logo, then two tabs, **Review** (default) and **Technical view**, and a "How it works" link that opens a sheet with 5 plain bullet points.
- **Body:** a container with max width 1168/1312px.
- **Footer:** one line holding the disclaimer, plus "Prototype for Open Agent Hackathon 2026. Not a government service."
- Use URL state: `/?run=<id>` and `/technical?run=<id>`.

### Screen 1: Review tab, before a run (empty state)
- **H1:** "Review procurement awards".
- **Request card:**
  - **Agency:** a combobox, prefilled with the three seeded agencies (HDB, People's Association, National Parks Board) and free text allowed.
  - **Period:** toggle-group presets ("FY2024/25", "Last 12 months", "Custom"); Custom reveals two date pickers.
  - **"Choose which checks to run":** a collapsed Collapsible holding plain-named checkboxes with icons (see MASTER §4). By default all checks run.
  - **"Start review":** the primary button.
  - **"Try a sample review":** a secondary link (the mock replay).
- Empty-state illustration area: the `ScanSearch` icon, "Pick an agency and a period to see which awards need a second look."

### Screen 2: Review tab, while running
The request card collapses into a one-line summary ("People's Association · 1 Apr 2021 to 31 Mar 2026 · Change"). Below it:
- **Progress card:** the 6-step vertical stepper (MASTER §7), the elapsed time, and "Usually takes 1–5 minutes". Step states are derived from the SSE `agent_name` and `status`.
- **Skeletons:** 4 stat tiles, 1 chart and 3 item cards.
- **Failure:** an outlined Alert reading "We couldn't finish this review. Try again, or open the Technical view for details." with a **Try again** button.

### Screen 3: Review tab, results (summary first, then list)
1. **Headline (H2, plain):** "12 awards worth a second look at People's Association. 3 need your decision." The sub-line gives the period and value.
2. **Stat tiles (4, CountUp):**
   - "Worth a second look" (count of accepted plus escalated)
   - "Need your decision" (escalated)
   - "Value involved" (S$ sum of `awarded_amt` over shown items)
   - "Cleared using your past decisions" (suppressed)

   Hide any tile whose data is absent.
3. **Charts (2, side by side ≥1024, stacked below):**
   - **"By reason"**: a horizontal bar chart of item count per flag, with plain names, icons in the legend, and value labels.
   - **"Where the money is"**: a horizontal bar chart of S$ per flag. The alternative is a status donut with the total in the centre. Pick the bar chart unless the data has fewer than 2 flags; then show a single tile instead of a chart.
   - Each has a one-sentence text summary under it, for example "Most items are shared addresses (7 of 12)."
4. **List, grouped by section (H2 with count):**
   - **Needs your decision** (escalated): always first, open.
   - **Flagged for review** (accepted): open. Sorted by strength (High first), then by amount.
   - **Cleared earlier** (suppressed): collapsed accordion; each row says which past decision cleared it.
   - **Set aside: not enough evidence** (rejected): collapsed accordion; one line each.
   - Filter toggle-group above the list: "All" · "Needs decision" · by reason. Plus a sort select (Strength, Amount, Date).
   - R3 shared-address groups render as one item: "3 suppliers share 10 Anson Road #12-01".
5. **Download summary** (secondary button): plain-language Markdown.

### Screen 4: Item details (Sheet, 512px; full screen below md)
- **Header:** the reason icon and title, plus the status badge.
- **"What we found":** the why-flagged sentence plus a short facts list:
  - Supplier
  - Amount
  - Award date
  - Agency
  - Registered on / Registry status (when present in `rows` or `detail`)
  - Tender reference
  - Company registration no.
- **"Why this matters":** the matching AGO excerpt, at most 2 sentences, plus "Read the report" (an external link with page number). If no excerpt matches this reason, hide the section. Don't show unrelated excerpts.
- **"How sure are we":** a High/Medium/Low chip plus `notes[]` rewritten as 1–3 plain bullets.
- **Accordion: "How we checked this"** (`Code` icon), collapsed by default:
  - data sources in plain names ("GeBIZ awards", "ACRA company registry");
  - the record rows as a formatted table (money formatted, friendly column labels);
  - then a nested "For specialists" block: SQL, query ID, source table names, memory IDs.
- **Footer actions:**
  - for "Needs your decision" items: **Confirm** (primary) and **Dismiss** (outline);
  - otherwise: "Record a decision" (outline) and "Close".
- After deciding, show the badge "Confirmed" or "Dismissed", with the reason and a timestamp.

### Screen 5: Decision dialog
**Title:** "Confirm this needs follow-up" or "Dismiss this item".

**Fields**
- **Reason:** a textarea, required for Dismiss, optional for Confirm. Helper: "Your note is saved with the decision."
- **"What explains it?":** optional, shown for Dismiss only. A radio list mapped to `pattern_tag`:
  - "Framework or panel contract" → `framework_contract`
  - "Shared office building" → `shared_office`
  - "Known, legitimate supplier" → `known_supplier`
  - "Something else" → (none)
- **"Apply to":** a radio group. "This agency only" (the default) maps to scope `agency`; "All agencies" maps to scope `global`. Helper: "Next time, ProcureLens will skip matching items."

**Buttons:** "Confirm" / "Dismiss" (outcome verbs) and "Cancel".

**Result:** a toast, "Decision saved. We'll remember it for next time."

**Mock run:** an inline note, "Sample review: decisions aren't saved."

### Screen 6: Technical view tab
For judges and specialists. A plain intro line: "Everything the system did for this review, step by step."
- **Run facts:**
  - run id;
  - time taken;
  - model calls and Nemotron receipts count;
  - Zetaris queries;
  - critiques and retries;
  - escalations.
- **Full agent timeline:** the existing timeline restyled. Agent names, actions, statuses, query IDs and receipts, with copy buttons that confirm "Copied". A filter toggles "Only critiques, retries and escalations".
- **Downloads:** raw trace (JSONL) and the memo (Markdown with technical lines).
- **"How the agents work together":** a small static diagram (Planner → Resolver → Analyst ↔ Critic → Risk → Reporter, with H-MEM and Zetaris), using Lucide icons and tokens.

### Mobile (<768)
- Results come before the request card, which collapses into a summary bar with "Change".
- Stat tiles go 2×2; charts stack; cards are full width.
- The sheet is full screen.
- No horizontal scroll at 320px.
- The Technical view timeline wraps (no nowrap rows; IDs truncate with copy).

## Implementation tasks (in order; commit after each, verify each)

1. **Tokens and fonts:**
   - rewrite `web/app/globals.css` with MASTER §1–3 (shadcn vars, `@theme` breakpoints, radius, shadows, motion, reduced-motion rules);
   - Inter via `next/font/google`, IBM Plex Mono for the technical view;
   - remove all `text-[11px]`.
   - **Verify:** `npm run build` passes.
2. **shadcn components:** install the MASTER §6 list (keep existing customisations where sensible), plus React Bits `CountUp`.
3. **Plain-language layer:** a `web/lib/copy.ts` holding all on-screen strings and the mappings:
   - flag → plain name and icon;
   - status → label and tone;
   - confidence → High/Medium/Low;
   - `formatMoney`, `formatDate`;
   - `whyFlagged(finding)` sentence builder from `detail`, `metric_*`, `awarded_amt` and `award_date`;
   - `friendlyColumn()`.

   Unit-test the builders (vitest, or a small script if no test runner exists).
4. **App shell:** top bar with the logo and tabs, footer, routing (`/` and `/technical`), `?run=` deep link.
5. **Review screen:** request card (combobox, period presets, collapsible checks), the running stepper and skeletons, the error alert.
6. **Results:** headline, stat tiles, 2 charts, the grouped list with filters and sort, R3 grouping, item card.
7. **Item details sheet and decision dialog**, per screens 4–5; keep the CSRF route untouched.
8. **Technical view tab:** the restyled timeline, run facts, downloads, the agent diagram.
9. **Mock replay:** fix the agency mismatch; check that it exercises every state (escalated, accepted, suppressed, rejected, critique, retry).
10. **Accessibility and responsive pass:** go through MASTER §8.
11. **Verification:**
    - Playwright screenshots at 390 and 1440 of: empty, running, results, sheet, dialog, technical view. Save them to `web/docs/screenshots/after/`.
    - Compare with the "before" set.
    - `npm run build` passes.
    - A live run against the real API works end to end, if the backend is up.

## Done when

- A non-technical reader can tell, within 5 seconds of results loading, how many items need them and why.
- No jargon appears on the Review tab.
- Every MASTER §8 checkbox is ticked.
- The build passes, the screenshots are committed, the work is merged into local `main`, and nothing is pushed.
