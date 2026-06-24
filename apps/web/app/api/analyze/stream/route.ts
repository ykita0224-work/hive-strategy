import { AGENTS } from "@/features/analyze/agents";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const idea = (searchParams.get("idea") ?? "").slice(0, 2000);

  if (!idea) {
    return new Response("Missing idea", { status: 400 });
  }

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      const send = (data: object) =>
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));

      send({ type: "start", agentIds: AGENTS.map((a) => a.id) });

      for (const agent of AGENTS) {
        await new Promise((r) => setTimeout(r, 1500));
        send({ type: "agent", id: agent.id, text: agent.mock });
      }

      send({ type: "done" });
      controller.close();
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
