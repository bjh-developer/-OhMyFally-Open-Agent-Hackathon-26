"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useRun, MOCK_RUN_ID, MOCK_REQUEST } from "@/lib/use-run";
import type { DecisionRecord, Finding, RunRequest } from "@/lib/types";
import type { Item } from "@/lib/copy";

// Everything the Review and Technical tabs share, so switching tabs never loses the run.
export interface DecisionTarget {
  item: Item;
  kind: "confirm" | "dismiss";
}

type Ctx = ReturnType<typeof useRun> & {
  form: RunRequest;
  setForm: (r: RunRequest) => void;
  checks: string[]; // empty means "all checks"
  setChecks: (c: string[]) => void;
  decisions: Record<string, DecisionRecord>;
  recordDecision: (findings: Finding[], rec: DecisionRecord) => void;
  openItem: Item | null;
  setOpenItem: (i: Item | null) => void;
  target: DecisionTarget | null;
  setTarget: (t: DecisionTarget | null) => void;
  begin: (req: RunRequest) => void;
  beginMock: () => void;
  clear: () => void;
};

const RunCtx = createContext<Ctx | null>(null);
export const useRunCtx = () => {
  const c = useContext(RunCtx);
  if (!c) throw new Error("RunProvider missing");
  return c;
};

const DEFAULT_FORM: RunRequest = { agency: "", date_from: "2024-04-01", date_to: "2025-03-31" }; // FY2024/25

export function RunProvider({ children }: { children: React.ReactNode }) {
  const run = useRun();
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const urlRun = params.get("run");
  const [form, setForm] = useState<RunRequest>(DEFAULT_FORM);
  const [checks, setChecks] = useState<string[]>([]);
  const [decisions, setDecisions] = useState<Record<string, DecisionRecord>>({});
  const [openItem, setOpenItem] = useState<Item | null>(null);
  const [target, setTarget] = useState<DecisionTarget | null>(null);

  // Decisions belong to one run: clear them when the run changes.
  useEffect(() => {
    setDecisions({});
    setOpenItem(null);
    setTarget(null);
  }, [run.runId]);

  const setUrlRun = useCallback(
    (id: string | null) => {
      const q = id ? `?run=${encodeURIComponent(id)}` : "";
      router.replace(`${pathname}${q}`, { scroll: false });
    },
    [pathname, router]
  );

  // Our own URL updates must not be mistaken for a deep link to load.
  const lastSet = useRef<string | null>(null);

  // Deep link: open /?run=<id> (or /technical?run=<id>) in a fresh tab and the run loads.
  useEffect(() => {
    if (!urlRun || urlRun === lastSet.current || urlRun === run.runId) return;
    lastSet.current = urlRun;
    if (urlRun === MOCK_RUN_ID) {
      setForm({ ...MOCK_REQUEST });
      run.startMock(true);
    } else {
      run.resume(urlRun);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlRun]);

  // Put a started run's id in the URL once the API has given us one.
  useEffect(() => {
    if (run.runId && run.runId !== urlRun) {
      lastSet.current = run.runId;
      setUrlRun(run.runId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run.runId]);

  const begin = useCallback(
    (req: RunRequest) => {
      lastSet.current = null;
      void run.start({ ...req, ...(checks.length ? { flags: checks } : {}) });
    },
    [run, checks]
  );

  const beginMock = useCallback(() => {
    setForm({ ...MOCK_REQUEST }); // the form must show the sample's agency, not whatever was typed
    setChecks([]);
    run.startMock(false);
  }, [run]);

  const clear = useCallback(() => {
    lastSet.current = null;
    run.reset();
    setUrlRun(null);
  }, [run, setUrlRun]);

  const recordDecision = useCallback((findings: Finding[], rec: DecisionRecord) => {
    setDecisions((d) => ({ ...d, ...Object.fromEntries(findings.map((f) => [f.finding_id, rec])) }));
  }, []);

  const value = useMemo<Ctx>(
    () => ({ ...run, form, setForm, checks, setChecks, decisions, recordDecision, openItem, setOpenItem, target, setTarget, begin, beginMock, clear }),
    [run, form, checks, decisions, recordDecision, openItem, target, begin, beginMock, clear]
  );
  return <RunCtx.Provider value={value}>{children}</RunCtx.Provider>;
}
