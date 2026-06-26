import Anthropic from "@anthropic-ai/sdk";
import { AGENTS } from "@/features/analyze/agents";

export const dynamic = "force-dynamic";

const SYSTEM_PROMPTS: Record<string, string> = {
  cfo: `You are a CFO and financial strategist. Analyze the given business idea from a financial perspective.
Cover: funding requirements, burn rate projections, unit economics, revenue model, key financial risks, and path to profitability.
Be concise and specific — 4–6 sentences. Use concrete numbers where reasonable.`,

  cmo: `You are a CMO and growth strategist. Analyze the given business idea from a marketing and go-to-market perspective.
Cover: target customer profile, acquisition channels, positioning, CAC/LTV expectations, and launch strategy.
Be concise and specific — 4–6 sentences.`,

  market: `You are a Market Analyst. Analyze the given business idea from a market research perspective.
Cover: TAM/SAM/SOM estimates, competitive landscape, market trends, customer pain points, and key differentiators.
Be concise and specific — 4–6 sentences.`,

  vc: `You are a VC Investor evaluating a potential investment. Analyze the given business idea from an investment perspective.
Cover: founder-market fit indicators, key milestones for seed/Series A, exit potential, comparable companies, and top 2–3 risks.
Be concise and specific — 4–6 sentences.`,

  devil: `You are a Devil's Advocate. Critically challenge the given business idea.
Identify the 3–4 most serious risks, blind spots, or assumptions that could cause this to fail. Be direct and specific.
Do not be encouraging — your job is to surface what could go wrong.`,

  pm: `You are a Product Manager. Analyze the given business idea from a product strategy perspective.
Cover: MVP scope, core user flows, success KPIs, key integrations, technical risks, and a realistic timeline.
Be concise and specific — 4–6 sentences.`,
};

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
      const send = (data: object) => {
        if (signal.aborted) return;
        try {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
        } catch {
          // controller already closed
        }
      };

      try {
        send({ type: "start", agentIds: AGENTS.map((a) => a.id) });

        const client = new Anthropic();

        await Promise.all(
          AGENTS.map(async (agent) => {
            const systemPrompt =
              SYSTEM_PROMPTS[agent.id] ??
              `You are a ${agent.name} (${agent.role}). Analyze the given business idea from your perspective in 4–6 sentences.`;

            let fullText = "";

            const stream = await client.messages.stream({
              model: "claude-sonnet-4-6",
              max_tokens: 512,
              system: systemPrompt,
              messages: [
                {
                  role: "user",
                  content: `Analyze this business idea:\n\n${idea}`,
                },
              ],
            });

            for await (const event of stream) {
              if (signal.aborted) break;
              if (
                event.type === "content_block_delta" &&
                event.delta.type === "text_delta"
              ) {
                const chunk = event.delta.text;
                fullText += chunk;
                send({ type: "chunk", id: agent.id, text: chunk });
              }
            }

            send({ type: "agent", id: agent.id, text: fullText });
          })
        );

        if (!signal.aborted) {
          send({ type: "done" });
        }
      } catch (err) {
        send({ type: "error", message: err instanceof Error ? err.message : "Unknown error" });
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
