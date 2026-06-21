"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [idea, setIdea] = useState("");
  const router = useRouter();

  const handleStart = () => {
    if (!idea.trim()) return;
    router.push(`/analyze?idea=${encodeURIComponent(idea.trim())}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleStart();
  };

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center px-4">
      <div className="w-full max-w-2xl flex flex-col items-center gap-8">
        <div className="text-center">
          <div className="text-4xl mb-4">🐝</div>
          <h1 className="text-5xl font-bold text-white tracking-tight mb-3">
            Hive Strategy
          </h1>
          <p className="text-lg text-zinc-400">
            Let a hive of AI agents stress-test your idea
          </p>
        </div>

        <div className="w-full flex flex-col gap-4">
          <textarea
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your product idea..."
            rows={5}
            className="w-full bg-zinc-900 text-white placeholder-zinc-600 border border-zinc-800 rounded-xl px-5 py-4 text-base resize-none focus:outline-none focus:border-zinc-600 transition-colors"
          />
          <button
            onClick={handleStart}
            disabled={!idea.trim()}
            className="w-full bg-white text-black font-semibold py-3 rounded-xl text-base hover:bg-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            Start Analysis →
          </button>
          <p className="text-center text-xs text-zinc-600">
            ⌘ + Enter to submit
          </p>
        </div>
      </div>
    </main>
  );
}
