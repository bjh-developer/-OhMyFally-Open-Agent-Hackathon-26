# ProcureLens design system (MASTER)

**Source of truth for all `web/` UI work.** Page-specific overrides go in `design-system/pages/<page>.md` and win over this file for that page only.

## 0. Brand and principles

**Brand**
- **Name:** ProcureLens
- **Tagline:** "See which awards need a second look"
- **Logo:** the Lucide `ScanSearch` icon (24px, primary colour) followed by the wordmark "ProcureLens" (Inter 600, 20px, foreground colour). No other mark.
- **Audience:** internal auditors at Singapore public agencies. They are **not technical**: no SQL, no AI vocabulary.
- **Tone:** calm, neutral, factual, never accusatory. We show "awards worth a second look", never fraud or wrongdoing.

**Design basis:** we follow the [Singapore Government Design System (SGDS) v3](https://designsystem.tech.gov.sg/) for typography, spacing, layout, components and content style.
- ProcureLens is a prototype, not a government service.
- **Never use SGDS identity elements:**
  - the Masthead ("A Singapore Government Agency Website"), the Merlion or crest;
  - the gov.sg footer;
  - govicons logos;
  - GovTech brand colours;
  - any "official" copy.

**Principles**
1. **Answer first.** Every screen opens with a plain-language headline.
2. **One glance, one decision.** Each finding shows what, who, how much, why, and what to do.
3. **Technical detail is opt-in.** Put it behind "How we checked this" (per finding) or the **Technical view** tab. Never put it on the main path.
4. **Calm colour.** Amber marks "needs a look". Red is only for system errors. Colour is never the only signal; always add an icon and text.
5. **Consistency over novelty.** Same token, same component and same wording for the same meaning everywhere.

## 1. Colour: "Quiet ledger"

All colours are defined as tokens in `web/app/globals.css` (shadcn CSS variables). **Never put raw hex in components.**

| Token (shadcn var) | Hex | Use |
|---|---|---|
| `--background` | `#FAFAF7` | Page canvas |
| `--card`, `--popover` | `#FFFFFF` | Cards, sheets, dialogs |
| `--foreground`, `--card-foreground` | `#1B2A2F` | Body text (14.2:1 on bg) |
| `--primary` | `#1F5F5B` | Brand, the single primary action per view (white text 7.4:1) |
| `--primary-foreground` | `#FFFFFF` | |
| `--secondary` / `--accent` | `#3B6EA5` | Links, secondary emphasis, info, focus ring (5.1:1 on bg) |
| `--secondary-foreground` | `#FFFFFF` | |
| `--muted` | `#EEF0EA` | Alternate surfaces, table header, chips |
| `--muted-foreground` | `#5A6A6F` | Supporting text (5.4:1 on bg; 4.9:1 on muted) |
| `--border` | `#DDE1D8` | **Decorative** dividers and card borders only |
| `--input` | `#6F7E82` | Form control borders (≥3:1, WCAG 1.4.11) |
| `--ring` | `#3B6EA5` | Focus ring |
| `--warning` | `#B7791F` | **Non-text only**: icons, left borders, dots, chart fill |
| `--warning-subtle` | `#FBEBC8` | Warning tint background |
| `--warning-foreground` | `#6F4300` | Warning text on tint or white (7.2:1) |
| `--success` | `#2F7D4F` | Confirmed/cleared icons and text (4.8:1) |
| `--success-subtle` | `#E3F1E8` | Success tint (check text contrast at build time) |
| `--destructive` | `#B42318` | **System errors only**, never flags |
| `--chart-1`…`--chart-5` | `#1F5F5B`, `#3B6EA5`, `#C98A1B`, `#7A9E9A`, `#8A8F98` | Charts, always with labels |

**Amber rule.** `#B7791F` fails as text (3.5:1). Use it for icons and borders only. Warning text is always `#6F4300`.

**Theme:** light only. Do not ship dark mode.

## 2. Typography (SGDS)

**Font:** Inter via `next/font/google`, weights **300 / 400 / 600 / 700 only**, `display: swap`. Inside the Technical view only, mono text uses IBM Plex Mono 400.

| Role | Size / line height (base → ≥1024 → ≥1440) | Weight | Tracking | Tailwind |
|---|---|---|---|---|
| Page title (H1, heading-md) | 24/28 → 26/32 → 28/32 | 600 | -0.4px | `text-2xl lg:text-[26px] 2xl:text-[28px] font-semibold tracking-[-0.4px]` |
| Section title (H2, heading-sm) | 20/24 → 22/28 → 24/28 | 600 | -0.4px | |
| Card title (H3) | 18/28 | 600 | 0 | |
| Body | 16/24 | 400 | 0 | `text-base` (**default; minimum for reading text**) |
| Body small | 14/20 | 400 | 0 | Secondary facts only |
| Label (buttons, fields, tabs) | 16/24 | 600 | 0 | |
| Label small (badges, chips, metadata) | 14/20 | 600 | 0 | |
| Caption | 12/16 | 400 | 0 | Footnotes only, never essential info |

- **Numbers:** use `tabular-nums` for money and counts, right-aligned in tables.
- **Money:** `Intl.NumberFormat('en-SG', {style:'currency', currency:'SGD', maximumFractionDigits:0})`, giving "S$400,000". Show the `S$` prefix everywhere.
- **Dates:** "22 Oct 2025", via `en-SG` with `day: 'numeric', month: 'short', year: 'numeric'`.
- **No text below 12px.** Remove every `text-[11px]`.

## 3. Space, layout, shape, motion (SGDS)

- **Spacing:** 4px base (the Tailwind scale). Card padding is 24px (`p-6`). Gaps inside a card are 20px (`gap-5`). Sections are separated by 32px (`gap-8`) or 48px.
- **Breakpoints:** xs 320, sm 512, md 768, lg 1024, xl 1280, 2xl 1440. Mirror them in `@theme`.
- **Containers:** max width 1168px at xl and 1312px at 2xl. Side margins are 20px (xs), 24px (sm) and 28px (md).
- **Radius:** tags and badges 4px. Cards, inputs, buttons, dialogs and sheets 8px (`--radius: 0.5rem`). Tables 0. Large callouts 12px.
- **Borders:** 1px default; 2px on input hover and focus; a 4px underline for the active tab.
- **Elevation:** cards are **flat and bordered, with no shadow**. Popovers and menus use `0 0 2px rgba(14,14,14,.16), 0 4px 8px rgba(14,14,14,.08)`. Dialogs and sheets use `… 0 8px 16px rgba(14,14,14,.08)`. A sticky header uses edge-bottom `0 2px 4px rgba(14,14,14,.08)`.
- **Z-index:** base 0, raised 100, floating 400, tooltip 800, modal 1600.
- **Motion:**
  - Durations: 100ms, 200ms (default UI), 300ms (sheets and sidebar).
  - Easing: `cubic-bezier(.25,0,.25,1)`.
  - Animate only `transform` and `opacity`.
  - Use motion only for feedback, orientation or state change.
  - Under `prefers-reduced-motion`: no spin, no shimmer, no count-up; show values instantly.
- **Touch targets:** at least 44×44px for every interactive element. Buttons default to 48px tall (SGDS md).

## 4. Iconography

**Lucide only.** Sizes: 16px (inline with small text), 20px (default with body text), 24px (headers, empty states). Use `strokeWidth={1.75}`, consistently.
- Every icon sits next to text, or carries an `aria-label` when it is an icon-only button.
- Decorative icons get `aria-hidden`.

| Concept | Lucide icon |
|---|---|
| Brand | `ScanSearch` |
| R1 Registered shortly before the award | `CalendarClock` |
| R2 Supplier no longer active | `CircleOff` |
| R3 Shares an address with another supplier | `MapPin` |
| R4 Several awards just under the approval limit | `Split` |
| R5 Business type doesn't match the purchase | `Shapes` |
| R6 One supplier wins most awards | `ChartPie` |
| R8 Not found in the company registry | `SearchX` |
| R9 Winner wasn't the top-scored bid | `ClipboardX` |
| Needs your decision | `CircleAlert` (warning colour) |
| Flagged for review | `Flag` |
| Cleared earlier (memory) | `History` |
| Set aside (not enough evidence) | `CircleMinus` |
| Confirmed | `CircleCheck` (success colour) |
| Dismissed | `CircleX` (muted-foreground, **not** red) |
| Technical details | `Code` |
| Evidence and report quotes | `BookOpen` |
| Loading | `LoaderCircle` (spin, not under reduced motion) |

The implementer must verify that every icon name exists in the installed `lucide-react` version, and swap in the nearest equivalent if one doesn't.

## 5. Words (SGDS content rules)

**Style**
- UK English, sentence case, plain language, short sentences, no unexplained acronyms.
- Buttons: 1–2 words, starting with a verb ("Start review", "Confirm", "Dismiss", "View details"). Never "OK" or "Submit".

**Translations from internal terms to the words users see**

| Internal | On screen |
|---|---|
| investigation / run / pipeline | review |
| finding | item |
| `accepted` | Flagged for review |
| `escalated` | Needs your decision |
| `suppressed` | Cleared earlier (from a past decision) |
| `rejected` | Set aside: not enough evidence |
| confidence 0–1 | **High** (≥0.75), **Medium** (0.5–0.75), **Low** (<0.5), with a tooltip "How strongly the records support this" |
| UEN / tender no. | Company registration no. / Tender reference (shown only in the details) |
| agents, planner, critic, LLM, Zetaris, H-MEM, Nemotron, receipt, query ID, SQL | Technical view only |
| "anomaly for review…" disclaimer (repeated) | **Once** per page, in the footer: "ProcureLens points out awards worth a second look. It doesn't decide if anything is wrong." |
| AGO excerpt | "Why this matters": at most 2 sentences, plus a "Read the report" link |

**Why-flagged sentence.** One per item, under 20 words, built from the finding's fields. Examples:
- "Awarded S$400,000 three weeks after the company was registered."
- "Two awards of S$58,000 and S$51,000 within 7 weeks: together over the S$90,000 tender limit."

## 6. Components (shadcn/ui, styled to SGDS)

Install the shadcn components: `button card badge tabs sheet dialog alert-dialog accordion collapsible skeleton progress tooltip chart select popover command radio-group label textarea sonner separator dropdown-menu toggle-group scroll-area`.

**React Bits:** `CountUp-TS-TW` only, for the stat numbers. It respects reduced motion. No backgrounds or flashy text effects.

**Buttons**
- **Primary** (filled, primary colour): **one per view**.
- **Secondary**: outline.
- **Tertiary**: ghost.
- **Destructive** style: errors only. Dismiss is outline, not red.
- Size md is `h-12 min-w-24 px-5 text-base font-semibold`, and sm is `h-11`. An icon button is 44×44px with an `aria-label`.

**Status badge**
- 24px tall, 4px radius, Label-small text.
- Always icon plus text.
- Tones: warning-subtle / warning-foreground ("Needs your decision"); muted ("Flagged for review"); success-subtle / success ("Confirmed"); muted ("Cleared earlier", "Set aside", "Dismissed").

**Item card**
- Bordered, white, `p-6`, flat. A 4px left border in warning colour marks "Needs your decision" items.
- Layout:
  - **Row 1:** reason icon and plain reason title (H3), with the status badge on the right.
  - **Row 2:** supplier name (body, 600) · S$ amount (tabular) · award date.
  - **Row 3:** why-flagged sentence (body).
  - **Row 4:** strength chip (High/Medium/Low), then actions on the right: "View details" (ghost), plus "Confirm" and "Dismiss" on "Needs your decision" items. Flagged items show "View details" and an overflow menu with "Record a decision".
- No disclaimer, UEN, tender number, metric names or memory IDs on the card.

**Stat tile:** a muted background, no border, `p-5`. A Label-small muted label sits above a 32px/600 tabular number (CountUp), with an optional 14px sub-line.

**Charts**
- Use shadcn `chart` (Recharts) with `accessibilityLayer`.
- Always show direct value labels and the legend.
- Give each chart a text summary (`aria-describedby`) for screen readers.
- Gridlines in the border colour.
- No more than 5 categories per chart.

**Sheet (item details):** 512px wide from the right (full width below md), with a footer holding the decision actions.

**Dialog (decision):** max width 640px. The primary button names the outcome. Focus returns to the trigger.

**Toast (sonner):** top right, 5 seconds, a one-line title.

**Empty state:** a 24px icon, an H3 title, one line of body text, one action. Never a skeleton.

**Errors:** an outlined destructive Alert (`role="alert"`) saying what happened and what to do, plus a "Try again" button. Never show raw error strings; those go to the Technical view.

## 7. Loading

- **Running a review (1–5 min):** show a **vertical stepper** with 6 friendly steps mapped from trace `agent_name`:
  1. "Checking your request" (gate)
  2. "Planning the checks" (planner)
  3. "Matching suppliers to the company registry" (resolver)
  4. "Running the checks" (analyst)
  5. "Double-checking the results" (critic, risk)
  6. "Writing your summary" (reporter)

  Each step shows its state: pending (`Circle`, muted), active (`LoaderCircle` with spin and a label), or done (`CircleCheck`). Show elapsed time and "Usually takes 1–5 minutes". Below the stepper, show **skeletons** shaped like the stat tiles and 3 item cards. Announce step changes with `aria-live="polite"`, at most once per step.
- **Buttons:** a spinner plus the label "Starting…", disabled while pending.
- **Short waits (<1s):** show nothing. Never use a skeleton in an empty state.

## 8. Accessibility checklist (WCAG 2.1 AA, SGDS)

- [ ] Text contrast ≥4.5:1 (large ≥3:1); control borders and focus indicators ≥3:1
- [ ] Visible 2px `#3B6EA5` focus ring with offset 2 on every interactive element
- [ ] Keyboard: everything reachable in visual order; Esc closes sheets and dialogs; arrow keys work in tabs and toggle groups
- [ ] Every input has a visible label; errors appear next to the field
- [ ] Touch targets ≥44px; tooltips are never the only route to information (provide a tap alternative)
- [ ] Icon plus text for every status; charts have text summaries
- [ ] `prefers-reduced-motion` respected
- [ ] No horizontal scroll at 320–390px; results come before controls on mobile
- [ ] Heading order is H1 → H2 → H3, with one H1 per page
