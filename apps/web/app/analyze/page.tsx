"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";

type Status = "waiting" | "thinking" | "done";

interface Agent {
  id: string;
  icon: string;
  name: string;
  role: string;
  mock: string;
}

const AGENTS: Agent[] = [
  {
    id: "cfo",
    icon: "💰",
    name: "CFO",
    role: "Financial",
    mock: "Financial projections show potential $50M market cap by year 3. Target burn rate of $200K/month for the first 18 months, with a death valley crossing at month 14. Recommend a Series A raise of $3M at a $15M pre-money valuation after hitting 1,000 paying customers. Unit economics need to reach CAC payback under 12 months.",
  },
  {
    id: "cmo",
    icon: "📣",
    name: "CMO",
    role: "Marketing",
    mock: "Go-to-market strategy should focus on product-led growth targeting SMBs first. Organic content + community can drive early traction. Target CAC below $150 with an LTV:CAC ratio of 4:1. Channel mix: 40% organic, 35% paid search, 25% partnerships. Launch on ProductHunt + targeted LinkedIn outreach to 500 ICP accounts.",
  },
  {
    id: "market",
    icon: "📊",
    name: "Market Analyst",
    role: "Research",
    mock: "TAM estimated at $12B globally with a SAM of $800M for the English-speaking B2B segment. Key competitors are fragmented, leaving a clear opening for a well-executed vertical play. Market growing at 24% CAGR. Top 3 competitors have NPS below 30 — customer satisfaction gap is the main wedge.",
  },
  {
    id: "vc",
    icon: "🏦",
    name: "VC Investor",
    role: "Investment",
    mock: "Strong founder-market fit potential. Seed milestones: working MVP, 10 design partners, $10K MRR. Series A trigger: $100K MRR with net revenue retention above 110%. Exit scenarios include strategic acquisition at 5–8x revenue or IPO at $300M+ ARR. Comparable exits in this space averaged 7.2x revenue.",
  },
  {
    id: "devil",
    icon: "⚠️",
    name: "Devil's Advocate",
    role: "Risk",
    mock: "Critical risks: regulatory headwinds in the EU could delay expansion 12–18 months. CAC may spike as incumbents respond aggressively. Technology moat is thin — a well-funded competitor could replicate core features in 6 months. Default scenario: if growth stalls below plan at month 18, runway collapses without bridge round.",
  },
  {
    id: "pm",
    icon: "🚀",
    name: "Product Manager",
    role: "Roadmap",
    mock: "MVP scope: core value prop in 3 user flows, shipped in 8 weeks. Phase 1 KPIs: 10-minute time-to-value, 60% D7 retention. Prioritize Slack and Google Workspace integrations for distribution leverage. V1.1 adds team collaboration features based on design partner feedback. Technical debt budget: max 20% of each sprint.",
  },
];

const STATUS_STYLES: Record<Status, string> = {
  waiting: "bg-zinc-800 text-zinc-400",
  thinking: "bg-amber-900/40 text-amber-400",
  done: "bg-green-900/40 text-green-400",
};

const STATUS_LABEL: Record<Status, string> = {
  waiting: "Waiting",
  thinking: "Thinking…",
  done: "Done",
};

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const idea = searchParams.get("idea") ?? "";

  const [statuses, setStatuses] = useState<Record<string, Status>>(
    Object.fromEntries(AGENTS.map((a) => [a.id, "waiting" as Status]))
  );
  const [texts, setTexts] = useState<Record<string, string>>(
    Object.fromEntries(AGENTS.map((a) => [a.id, ""]))
  );
  const [running, setRunning] = useState(false);

  const allDone = AGENTS.every((a) => statuses[a.id] === "done");

  const runAnalysis = () => {
    if (running) return;
    setRunning(true);
    setStatuses(Object.fromEntries(AGENTS.map((a) => [a.id, "thinking"])));
    setTexts(Object.fromEntries(AGENTS.map((a) => [a.id, ""])));

    AGENTS.forEach((agent, i) => {
      setTimeout(() => {
        setStatuses((prev) => ({ ...prev, [agent.id]: "done" }));
        setTexts((prev) => ({ ...prev, [agent.id]: agent.mock }));
        if (i === AGENTS.length - 1) setRunning(false);
      }, 1500 * (i + 1));
    });
  };

  useEffect(() => {
    if (!idea) router.replace("/");
  }, [idea, router]);

  if (!idea) return null;

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
