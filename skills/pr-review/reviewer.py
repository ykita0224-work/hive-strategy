import anthropic
from github import PRFile, ReviewComment

SYSTEM_PROMPT = """You are a senior software engineer performing a thorough code review.
Analyze the provided git diff and identify real, actionable issues only.

Focus on:
- Correctness bugs (logic errors, off-by-one, null/None dereferences, wrong conditions)
- Security vulnerabilities (injection, auth bypass, hardcoded secrets, OWASP top 10)
- Performance issues (N+1 queries, blocking I/O in async code, unnecessary loops)
- Missing error handling at system boundaries (external APIs, file I/O, DB calls)

Rules:
- Only comment on lines marked with `+` in the diff (new or changed lines)
- Do NOT comment on style, formatting, or naming unless they cause a real bug
- Do NOT invent issues — only flag things you are confident about
- If there are no real issues, return an empty comments list"""

REVIEW_TOOL = {
    "name": "submit_review",
    "description": "Submit structured code review findings",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "1-3 sentence overall summary of the PR and its quality",
            },
            "comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path exactly as shown in the diff header",
                        },
                        "line": {
                            "type": "integer",
                            "description": "Line number in the NEW file (right side, after the change)",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["bug", "security", "performance", "error-handling"],
                        },
                        "body": {
                            "type": "string",
                            "description": "Specific, actionable comment explaining the issue and how to fix it",
                        },
                    },
                    "required": ["path", "line", "severity", "body"],
                },
            },
        },
        "required": ["summary", "comments"],
    },
}

MAX_DIFF_CHARS = 80_000


def _build_diff(files: list[PRFile]) -> str:
    parts = []
    total = 0
    for f in files:
        if f.patch:
            chunk = f"### {f.filename}\n```diff\n{f.patch}\n```"
            if total + len(chunk) > MAX_DIFF_CHARS:
                parts.append("_[Remaining files omitted — diff too large]_")
                break
            parts.append(chunk)
            total += len(chunk)
    return "\n\n".join(parts)


def review_diff(
    files: list[PRFile], client: anthropic.Anthropic
) -> tuple[str, list[ReviewComment]]:
    diff = _build_diff(files)

    if not diff.strip():
        return "No reviewable changes (binary files or empty diff).", []

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[REVIEW_TOOL],
        tool_choice={"type": "tool", "name": "submit_review"},
        messages=[
            {
                "role": "user",
                "content": f"Please review this pull request diff:\n\n{diff}",
            }
        ],
    )

    tool_use_blocks = [b for b in message.content if b.type == "tool_use"]
    if not tool_use_blocks:
        raise RuntimeError(
            f"Model did not return a tool_use block (stop_reason={message.stop_reason!r}). "
            "The diff may be too large even after truncation."
        )
    result = tool_use_blocks[0].input

    severity_emoji = {
        "bug": "🐛",
        "security": "🔒",
        "performance": "⚡",
        "error-handling": "⚠️",
    }

    comments = [
        ReviewComment(
            path=c["path"],
            line=c["line"],
            body=f"{severity_emoji.get(c['severity'], '•')} **{c['severity'].upper()}** — {c['body']}",
        )
        for c in result.get("comments", [])
    ]

    return result["summary"], comments
