"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { eventsUrl, getRun, startRun } from "./api";
import type { Memo, RunRequest, TraceEvent } from "./types";
import mock from "@/mocks/run_demo.json";

export type RunState = "idle" | "running" | "done" | "rejected" | "failed";

const MOCK = mock as unknown as { run_id: string; events: TraceEvent[]; memo: Memo };
export const MOCK_RUN_ID = MOCK.run_id;
export const MOCK_REQUEST: RunRequest = { agency: MOCK.memo.agency, date_from: MOCK.memo.date_from, date_to: MOCK.memo.date_to };

export function useRun() {
  const [runId, setRunId] = useState<string | null>(null);
  const [request, setRequest] = useState<RunRequest | null>(null);
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [memo, setMemo] = useState<Memo | null>(null);
  const [state, setState] = useState<RunState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [isMock, setIsMock] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [endedAt, setEndedAt] = useState<number | null>(null);
  const es = useRef<EventSource | null>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const gen = useRef(0); // bumps on every start/reset so stale callbacks are ignored

  const stop = useCallback(() => {
    es.current?.close();
    es.current = null;
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }, []);

  useEffect(() => stop, [stop]);

  const reset = useCallback(() => {
    gen.current++;
    stop();
    setRunId(null);
    setRequest(null);
    setEvents([]);
    setMemo(null);
    setState("idle");
    setError(null);
    setIsMock(false);
    setStartedAt(null);
    setEndedAt(null);
  }, [stop]);

  const finish = useCallback(async (id: string, g: number) => {
    try {
      const view = await getRun(id);
      if (g !== gen.current) return;
      setMemo(view.memo);
      setError(view.error);
      setState(view.status === "running" ? "running" : view.status);
      if (view.status !== "running") setEndedAt(Date.now());
    } catch (e) {
      if (g !== gen.current) return;
      setError((e as Error).message);
      setState("failed");
      setEndedAt(Date.now());
    }
  }, []);

  // The server replays the whole trace on every (re)connect, so after a drop we skip what we already have.
  const connect = useCallback(
    (id: string, g: number, skip: number) => {
      const source = new EventSource(eventsUrl(id));
      es.current = source;
      let seen = 0;
      source.onmessage = (m) => {
        if (g !== gen.current) return;
        seen++;
        if (seen <= skip) return;
        try {
          const ev = JSON.parse(m.data) as TraceEvent;
          setEvents((prev) => [...prev, ev]);
        } catch {
          /* ignore malformed line */
        }
      };
      source.addEventListener("end", () => {
        source.close();
        if (g === gen.current) void finish(id, g);
      });
      source.onerror = () => {
        source.close();
        if (g !== gen.current) return;
        const have = skip + Math.max(0, seen - skip);
        const t = setTimeout(async () => {
          if (g !== gen.current) return;
          try {
            const view = await getRun(id);
            if (g !== gen.current) return;
            if (view.status === "running") connect(id, g, have);
            else void finish(id, g);
          } catch (e) {
            if (g !== gen.current) return;
            setError(`Lost connection to the API: ${(e as Error).message}`);
            setState("failed");
            setEndedAt(Date.now());
          }
        }, 1000);
        timers.current.push(t);
      };
    },
    [finish]
  );

  const start = useCallback(
    async (req: RunRequest) => {
      reset();
      const g = gen.current;
      setRequest(req);
      setStartedAt(Date.now());
      setState("running");
      try {
        const view = await startRun(req);
        if (g !== gen.current) return;
        setRunId(view.run_id);
        connect(view.run_id, g, 0);
      } catch (e) {
        if (g !== gen.current) return;
        setError((e as Error).message);
        setState("failed");
        setEndedAt(Date.now());
      }
    },
    [connect, reset]
  );

  // Deep link: /?run=<id>. The server replays the whole trace, and ends the stream at once for a finished run.
  const resume = useCallback(
    (id: string) => {
      reset();
      const g = gen.current;
      setStartedAt(Date.now());
      setState("running");
      setRunId(id);
      getRun(id)
        .then((view) => {
          if (g !== gen.current) return;
          const m = view.memo;
          if (m) setRequest({ agency: m.agency, date_from: m.date_from, date_to: m.date_to });
          connect(id, g, 0);
        })
        .catch((e: Error) => {
          if (g !== gen.current) return;
          setError(e.message);
          setState("failed");
          setEndedAt(Date.now());
        });
    },
    [connect, reset]
  );

  // Sample review. `instant` skips the replay (used by the ?run=run_mock_demo link).
  const startMock = useCallback(
    (instant = false) => {
      reset();
      const g = gen.current;
      setIsMock(true);
      setRunId(MOCK.run_id);
      setRequest(MOCK_REQUEST);
      setStartedAt(Date.now());
      if (instant) {
        setEvents(MOCK.events);
        setMemo(MOCK.memo);
        setState("done");
        setEndedAt(Date.now());
        return;
      }
      setState("running");
      MOCK.events.forEach((ev, i) => {
        timers.current.push(
          setTimeout(() => {
            if (g === gen.current) setEvents((prev) => [...prev, ev]);
          }, 450 * (i + 1))
        );
      });
      timers.current.push(
        setTimeout(() => {
          if (g !== gen.current) return;
          setMemo(MOCK.memo);
          setState("done");
          setEndedAt(Date.now());
        }, 450 * (MOCK.events.length + 1))
      );
    },
    [reset]
  );

  return { runId, request, events, memo, state, error, isMock, startedAt, endedAt, start, resume, startMock, reset };
}
