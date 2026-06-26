"""
GET /analyze/stream?idea=<idea>

SSE stream that runs all 6 analyst agents in parallel against Claude claude-sonnet-4-6.

Event types emitted:
  {"type": "start",  "agentIds": [...]}
  {"type": "chunk",  "id": "<agentId>", "text": "<delta>"}        — streaming token
  {"type": "agent",  "id": "<agentId>", "text": "<full>"}         — agent finished
  {"type": "error",  "id": "<agentId>", "message": "<generic>"}   — agent failed
  {"type": "done",   "failedAgentIds": [...]}                      — all agents complete
"""

import asyncio
import json
import logging
import os

import anthropic
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from agents import AGENTS

logger = logging.getLogger(__name__)

router = APIRouter()

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 512
MAX_IDEA_LEN = 2000


async def _run_agent(
    client: anthropic.AsyncAnthropic,
    agent_id: str,
    system_prompt: str,
    idea: str,
    queue: asyncio.Queue,
) -> None:
    full_text = ""
    try:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Analyze this business idea:\n\n{idea}"}],
        ) as stream:
            async for event in stream:
                if (
                    event.type == "content_block_delta"
                    and event.delta.type == "text_delta"
                ):
                    chunk = event.delta.text
                    full_text += chunk
                    await queue.put({"type": "chunk", "id": agent_id, "text": chunk})

        await queue.put({"type": "agent", "id": agent_id, "text": full_text})
    except Exception as exc:
        logger.error("Agent %s failed: %s", agent_id, exc, exc_info=True)
        await queue.put({"type": "error", "id": agent_id, "message": "Agent failed. Please try again."})


@router.get("/stream")
async def analyze_stream(idea: str = Query(..., max_length=MAX_IDEA_LEN)):
    async def event_generator():
        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        queue: asyncio.Queue = asyncio.Queue()

        agent_ids = [a.id for a in AGENTS]
        yield {"data": json.dumps({"type": "start", "agentIds": agent_ids})}

        tasks = [
            asyncio.create_task(
                _run_agent(client, agent.id, agent.system_prompt, idea, queue)
            )
            for agent in AGENTS
        ]

        finished = 0
        total = len(tasks)
        failed_agent_ids: list[str] = []

        while finished < total:
            event = await queue.get()
            yield {"data": json.dumps(event)}
            if event["type"] == "agent":
                finished += 1
            elif event["type"] == "error":
                failed_agent_ids.append(event["id"])
                finished += 1

        await asyncio.gather(*tasks, return_exceptions=True)
        yield {"data": json.dumps({"type": "done", "failedAgentIds": failed_agent_ids})}

    return EventSourceResponse(event_generator())
