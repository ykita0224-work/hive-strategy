"""
Fixer agent — Claude with file read/write tools to apply accepted review fixes.
Only runs on comments the programmer agent has accepted.
"""

import os
from pathlib import Path
import anthropic
from github import ReviewComment

SYSTEM_PROMPT = """You are an expert software engineer applying targeted code fixes.
You will receive files with their current content and specific issues to fix.

Rules:
- Fix ONLY what is described in the issue. Do not refactor unrelated code.
- Preserve all existing formatting, comments, and style.
- If a fix requires understanding broader context not provided, call mark_unfixable.
- Write the entire corrected file content when calling write_file."""

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the current content of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to repo root"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write corrected content to a file (entire file, not a patch)",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string", "description": "Complete corrected file content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "mark_unfixable",
        "description": "Mark an issue as requiring manual intervention",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["path", "reason"],
        },
    },
]


def fix_issues(
    comments: list[ReviewComment],
    client: anthropic.Anthropic,
    repo_root: str = ".",
) -> list[str]:
    """
    Run Claude agent to fix accepted review issues.
    Returns list of file paths that were changed.
    """
    if not comments:
        return []

    by_file: dict[str, list[str]] = {}
    for c in comments:
        by_file.setdefault(c.path, []).append(c.body)

    context_parts = []
    for path, issues in by_file.items():
        full_path = os.path.join(repo_root, path)
        try:
            content = Path(full_path).read_text()
        except FileNotFoundError:
            print(f"[fixer] Skipping {path} — file not found")
            continue
        issue_list = "\n".join(f"  - {i}" for i in issues)
        context_parts.append(
            f"**{path}**\n```\n{content}\n```\nIssues to fix:\n{issue_list}"
        )

    if not context_parts:
        return []

    changed: list[str] = []
    unfixable: list[str] = []
    messages = [
        {
            "role": "user",
            "content": "Fix these issues:\n\n" + "\n\n---\n\n".join(context_parts),
        }
    ]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_calls = [b for b in response.content if b.type == "tool_use"]
        if not tool_calls or response.stop_reason == "end_turn":
            break

        results = []
        for tool in tool_calls:
            if tool.name == "read_file":
                path = tool.input["path"]
                try:
                    content = Path(os.path.join(repo_root, path)).read_text()
                    out = content
                except FileNotFoundError:
                    out = f"Error: {path} not found"
                results.append({"type": "tool_result", "tool_use_id": tool.id, "content": out})

            elif tool.name == "write_file":
                path = tool.input["path"]
                Path(os.path.join(repo_root, path)).write_text(tool.input["content"])
                changed.append(path)
                print(f"[fixer] Fixed {path}")
                results.append({"type": "tool_result", "tool_use_id": tool.id, "content": f"Written: {path}"})

            elif tool.name == "mark_unfixable":
                unfixable.append(f"{tool.input['path']}: {tool.input['reason']}")
                results.append({"type": "tool_result", "tool_use_id": tool.id, "content": "Noted"})

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": results})

    if unfixable:
        print(f"[fixer] Unfixable (manual required): {'; '.join(unfixable)}")

    return changed
