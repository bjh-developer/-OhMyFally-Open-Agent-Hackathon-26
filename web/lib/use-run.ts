"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { eventsUrl, getRun, startRun } from "./api";
import type { Memo, RunRequest, TraceEvent } from "./types";
import mock from "@/mocks/run_demo.json";

export type RunState = "idle" | "running" | "done" | "rejected" | "failed";

const MOCK = mock as unknown as { run_id: string; events: TraceEvent[]; memo: Memo };

export function useRun() {
  const [runId, setRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [memo, setMemo] = useState<Memo | null>(null);
  const [state, setState] = useState<RunState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [isMock, setIsMock] = useState(false);
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
    setEvents([]);
    setMemo(null);
    setState("idle");
    setError(null);
    setIsMock(false);
  }, [stop]);

  const finish = useCallback(async (id: string, g: number) => {
    try {
      const view = await getRun(id);
      if (g !== gen.current) return;
      setMemo(view.memo);
      setError(view.error);
      setState(view.status === "running" ? "running" : view.status);
    } catch (e) {
      if (g !== gen.current) return;
      setError((e as Error).message);
      setState("failed");
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
      }
    },
    [connect, reset]
  );

  const startMock = useCallback(() => {
    reset();
    const g = gen.current;
    setIsMock(true);
    setState("running");
    setRunId(MOCK.run_id);
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
      }, 450 * (MOCK.events.length + 1))
    );
  }, [reset]);

  return { runId, events, memo, state, error, isMock, start, startMock, reset };
}
