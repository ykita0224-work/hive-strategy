"use client";

import { AGENTS } from "@/features/analyze/agents";
import { STATUS_STYLES, STATUS_LABEL } from "@/features/analyze/constants";
import { useAnalysisStream } from "../_hooks/useAnalysisStream";

interface Props {
  idea: string;
}

export function AgentGrid({ idea }: Props) {
  const { statuses, texts, running, allDone, run } = useAnalysisStream(idea);

  return (
    <div className="flex flex-col gap-8">
      <button
        onClick={run}
        disabled={running}
        className="self-start bg-white text-black font-semibold px-6 py-2.5 rounded-xl text-sm hover:bg-zinc-100 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        {running ? "Running…" : allDone ? "Re-run Analysis" : "Run Analysis"}
      </button>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {AGENTS.map((agent) => {
          const status = statuses[agent.id];
          const text = texts[agent.id];
          return (
            <div
              key={agent.id}
              className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex flex-col gap-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{agent.icon}</span>
                  <div>
                    <p className="text-white font-semibold text-sm leading-tight">{agent.name}</p>
                    <p className="text-zinc-500 text-xs">{agent.role}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[status]}`}>
                  {STATUS_LABEL[status]}
                </span>
              </div>

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
                  <p className="text-zinc-700 italic">Waiting for analysis to start…</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
