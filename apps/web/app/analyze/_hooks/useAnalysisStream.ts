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
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => () => { esRef.current?.close(); }, []);

  const run = useCallback(() => {
    if (running) return;

    esRef.current?.close();
    setRunning(true);
    setStatuses(initialStatuses());
    setTexts(initialTexts());

    const es = new EventSource(
      `/api/analyze/stream?idea=${encodeURIComponent(idea)}`
    );
    esRef.current = es;

    es.onmessage = (e) => {
      const data = JSON.parse(e.data as string) as {
        type: string;
        agentIds?: string[];
        id?: string;
        text?: string;
      };

      if (data.type === "start") {
        setStatuses(
          Object.fromEntries((data.agentIds ?? []).map((id) => [id, "thinking" as Status]))
        );
      } else if (data.type === "agent" && data.id) {
        setStatuses((prev) => ({ ...prev, [data.id!]: "done" }));
        setTexts((prev) => ({ ...prev, [data.id!]: data.text ?? "" }));
      } else if (data.type === "done") {
        setRunning(false);
        es.close();
      }
    };

    es.onerror = () => {
      setRunning(false);
      es.close();
    };
  }, [running, idea]);

  const allDone = AGENTS.every((a) => statuses[a.id] === "done");

  return { statuses, texts, running, allDone, run };
}
