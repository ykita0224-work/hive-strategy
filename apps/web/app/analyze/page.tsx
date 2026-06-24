"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { AGENTS } from "./agent";
import { Status, STATUS_STYLES, STATUS_LABEL } from "./record";

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const idea = (searchParams.get("idea") ?? "").slice(0, 2000);

  const [statuses, setStatuses] = useState<Record<string, Status>>(
    Object.fromEntries(AGENTS.map((a) => [a.id, "waiting" as Status]))
  );
  const [texts, setTexts] = useState<Record<string, string>>(
    Object.fromEntries(AGENTS.map((a) => [a.id, ""]))
  );
  const [running, setRunning] = useState(false);
  const timerRefs = useRef<ReturnType<typeof setTimeout>[]>([]);

  const allDone = AGENTS.every((a) => statuses[a.id] === "done");

  const runAnalysis = () => {
    if (running) return;

    timerRefs.current.forEach(clearTimeout);
    timerRefs.current = [];

    if (AGENTS.length === 0) {
      setRunning(false);
      return;
    }

    setRunning(true);
    setStatuses(Object.fromEntries(AGENTS.map((a) => [a.id, "thinking"])));
    setTexts(Object.fromEntries(AGENTS.map((a) => [a.id, ""])));

    AGENTS.forEach((agent, i) => {
      const id = setTimeout(() => {
        setStatuses((prev) => ({ ...prev, [agent.id]: "done" }));
        setTexts((prev) => ({ ...prev, [agent.id]: agent.mock }));
        if (i === AGENTS.length - 1) setRunning(false);
      }, 1500 * (i + 1));
      timerRefs.current.push(id);
    });
  };

  useEffect(() => {
    return () => { timerRefs.current.forEach(clearTimeout); };
  }, []);

  useEffect(() => {
    if (!idea) router.replace("/");
  }, [idea, router]);

  if (!idea) return <p className="min-h-screen bg-[#0a0a0a] flex items-center justify-center text-zinc-500">Redirecting…</p>;

  return (
    <main className="min-h-screen bg-[#0a0a0a] px-4 py-12">
      <div className="max-w-5xl mx-auto flex flex-col gap-8">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <button
            onClick={() => router.push("/")}
            className="self-start text-zinc-500 hover:text-zinc-300 text-sm transition-colors"
          >
            ← Back
          </button>
          <div>
            <p className="text-xs uppercase tracking-widest text-zinc-500 mb-1">
              Analyzing
            </p>
            <h1 className="text-2xl font-semibold text-white leading-snug max-w-3xl">
              {idea}
            </h1>
          </div>
          <button
            onClick={runAnalysis}
            disabled={running}
            className="self-start bg-white text-black font-semibold px-6 py-2.5 rounded-xl text-sm hover:bg-zinc-100 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {running ? "Running…" : allDone ? "Re-run Analysis" : "Run Analysis"}
          </button>
        </div>

        {/* Agent grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {AGENTS.map((agent) => {
            const status = statuses[agent.id];
            const text = texts[agent.id];
            return (
              <div
                key={agent.id}
                className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex flex-col gap-3"
              >
                {/* Card header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{agent.icon}</span>
                    <div>
                      <p className="text-white font-semibold text-sm leading-tight">
                        {agent.name}
                      </p>
                      <p className="text-zinc-500 text-xs">{agent.role}</p>
                    </div>
                  </div>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[status]}`}
                  >
                    {STATUS_LABEL[status]}
                  </span>
                </div>

                {/* Card body */}
                <div className="min-h-[100px] text-sm text-zinc-400 leading-relaxed">
                  {status === "thinking" && (
                    <div className="flex gap-1 items-center pt-2">
                      <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce [animation-delay:0ms]" />
                      <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce [animation-delay:150ms]" />
                      <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce [animation-delay:300ms]" />
                    </div>
                  )}
                  {status === "done" && text}
                  {status === "waiting" && (
                    <p className="text-zinc-700 italic">
                      Waiting for analysis to start…
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense>
      <AnalyzeContent />
    </Suspense>
  );
}
