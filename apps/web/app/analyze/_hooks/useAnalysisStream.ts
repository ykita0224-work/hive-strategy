"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { AGENTS } from "@/features/analyze/agents";
import type { Status } from "@/features/analyze/constants";

const initialStatuses = () =>
  Object.fromEntries(AGENTS.map((a) => [a.id, "waiting" as Status]));

const initialTexts = () =>
  Object.fromEntries(AGENTS.map((a) => [a.id, ""]));

export function useAnalysisStream(idea: string) {
  const [statuses, setStatuses] = useState<Record<string, Status>>(initialStatuses);
  const [texts, setTexts] = useState<Record<string, string>>(initialTexts);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const runningRef = useRef(false);

  useEffect(() => () => { esRef.current?.close(); }, []);

  const run = useCallback(() => {
    if (runningRef.current) return;
    runningRef.current = true;

    esRef.current?.close();
    setRunning(true);
    setError(null);
    setStatuses(initialStatuses());
    setTexts(initialTexts());

    const es = new EventSource(
      `/api/analyze/stream?idea=${encodeURIComponent(idea)}`
    );
    esRef.current = es;

    es.onmessage = (e) => {
      let data: { type: string; agentIds?: string[]; id?: string; text?: string };
      try {
        data = JSON.parse(e.data as string);
      } catch {
        return;
      }

      if (data.type === "start") {
        setStatuses(
          Object.fromEntries((data.agentIds ?? []).map((id) => [id, "thinking" as Status]))
        );
      } else if (data.type === "agent" && data.id) {
        setStatuses((prev) => ({ ...prev, [data.id!]: "done" }));
        setTexts((prev) => ({ ...prev, [data.id!]: data.text ?? "" }));
      } else if (data.type === "done") {
        runningRef.current = false;
        setRunning(false);
        es.close();
      }
    };

    es.onerror = () => {
      runningRef.current = false;
      setRunning(false);
      setError("Analysis failed — please try again.");
      es.close();
    };
  }, [idea]);

  const allDone = AGENTS.every((a) => statuses[a.id] === "done");

  return { statuses, texts, running, allDone, error, run };
}
