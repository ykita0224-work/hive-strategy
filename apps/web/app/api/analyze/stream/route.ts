import { AGENTS } from "@/features/analyze/agents";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const idea = (searchParams.get("idea") ?? "").slice(0, 2000);

  if (!idea) {
    return new Response("Missing idea", { status: 400 });
  }

  const { signal } = request;
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      const send = (data: object) =>
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));

      try {
        send({ type: "start", agentIds: AGENTS.map((a) => a.id) });

        for (const agent of AGENTS) {
          if (signal.aborted) break;
          await new Promise<void>((resolve) => {
            const t = setTimeout(resolve, 1500);
            signal.addEventListener("abort", () => { clearTimeout(t); resolve(); }, { once: true });
          });
          if (signal.aborted) break;
          send({ type: "agent", id: agent.id, text: agent.mock });
        }

        if (!signal.aborted) {
          send({ type: "done" });
        }
      } catch {
        // client disconnected or enqueue error — fall through to close
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
