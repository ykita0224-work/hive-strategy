import { redirect } from "next/navigation";
import Link from "next/link";
import { AgentGrid } from "./_components/AgentGrid";

interface Props {
  searchParams: Promise<{ idea?: string }>;
}

export default async function AnalyzePage({ searchParams }: Props) {
  const { idea: rawIdea } = await searchParams;
  const idea = (rawIdea ?? "").slice(0, 2000);

  if (!idea) redirect("/");

  return (
    <main className="min-h-screen bg-[#0a0a0a] px-4 py-12">
      <div className="max-w-5xl mx-auto flex flex-col gap-8">
        <div className="flex flex-col gap-4">
          <Link
            href="/"
            className="self-start text-zinc-500 hover:text-zinc-300 text-sm transition-colors"
          >
            ← Back
          </Link>
          <div>
            <p className="text-xs uppercase tracking-widest text-zinc-500 mb-1">Analyzing</p>
            <h1 className="text-2xl font-semibold text-white leading-snug max-w-3xl">{idea}</h1>
          </div>
        </div>
        <AgentGrid idea={idea} />
      </div>
    </main>
  );
}
