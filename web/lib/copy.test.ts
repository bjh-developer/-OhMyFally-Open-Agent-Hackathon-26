import { describe, expect, it } from "vitest";
import mock from "@/mocks/run_demo.json";
import { buildItems, firstSentences, formatDate, formatMoney, friendlyColumn, headline, plainNotes, relevantAgoRefs, stepStates, strengthOf, summarise, whyFlagged } from "./copy";
import type { Finding, Memo } from "./types";

const memo = (mock as unknown as { memo: Memo }).memo;
const byFlag = (id: string) => memo.findings.find((f) => f.flag_id === id) as Finding;
const words = (s: string) => s.trim().split(/\s+/).length;

describe("formatting", () => {
  it("formats money with S$", () => expect(formatMoney(400000)).toBe("S$400,000"));
  it("formats dates without time-zone drift", () => expect(formatDate("2025-06-20")).toBe("20 Jun 2025"));
  it("maps confidence to strength", () => {
    expect([0.91, 0.75, 0.74, 0.5, 0.49].map(strengthOf)).toEqual(["High", "High", "Medium", "Medium", "Low"]);
  });
  it("labels columns", () => {
    expect(friendlyColumn("tender_no")).toBe("Tender reference");
    expect(friendlyColumn("sum_of_awards_90d")).toBe("Sum of awards 90d");
  });
});

describe("whyFlagged", () => {
  it("R1 uses months since registration", () => {
    expect(whyFlagged(byFlag("R1"))).toBe("Awarded S$400,000 about 3 weeks after the company was registered.");
  });
  it("R4 names both awards and the span", () => {
    const f = { ...byFlag("R4") };
    expect(whyFlagged(f)).toMatch(/^Two awards of S\$58,000 and S\$51,000 within 7 weeks: together over the S\$90,000 tender limit\.$/);
  });
  it("every sentence is under 20 words and has no jargon", () => {
    for (const f of memo.findings) {
      const s = whyFlagged(f);
      expect(words(s)).toBeLessThan(20);
      expect(s).not.toMatch(/UEN|SQL|H-MEM|anomaly/i);
    }
  });
});

describe("items and summary", () => {
  const items = buildItems(memo);
  const s = summarise(items);
  it("counts by status", () => {
    expect(s.worth).toBe(4);
    expect(s.needDecision).toBe(1);
    expect(s.cleared).toBe(1);
  });
  it("sums value over shown items", () => expect(s.value).toBe(400000 + 58000 + 120000 + 76500));
  it("writes a headline", () => expect(headline("Sample Agency", s)).toBe("4 items worth a second look at Sample Agency. 1 needs your decision."));
});

describe("plain wording helpers", () => {
  it("removes agent names from notes", () => {
    const out = plainNotes(["Escalated by RiskAgent: R5 findings always go to a human.", "Critic sent this back once: first count was 3 rows, re-run returned 2."]);
    expect(out.join(" ")).not.toMatch(/Critic|Agent/);
  });
  it("hides unrelated AGO excerpts", () => {
    expect(relevantAgoRefs("R1", ["ago-fy2425-edb-evaluation"])).toEqual([]);
    expect(relevantAgoRefs("R9", ["ago-fy2425-edb-evaluation"])).toEqual(["ago-fy2425-edb-evaluation"]);
  });
  it("keeps at most two sentences", () => {
    expect(firstSentences("63. One. Two. Three.")).toBe("One. Two.");
  });
});

describe("stepper", () => {
  it("never moves backwards on retry", () => {
    expect(stepStates(["GateAgent", "PlannerAgent", "AnalystAgent", "CriticAgent", "AnalystAgent"], false)).toEqual(["done", "done", "done", "done", "active", "pending"]);
  });
  it("marks all done when finished", () => expect(stepStates([], true).every((x) => x === "done")).toBe(true));
});
