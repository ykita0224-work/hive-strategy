"""
Fixer agent — Claude with file read/write tools to apply accepted review fixes.
Only runs on comments the programmer agent has accepted.
"""

from pathlib import Path
import anthropic
from github import ReviewComment

MAX_ITERS = 20


def _safe_path(repo_root: str, path: str) -> Path:
    root = Path(repo_root).resolve()
    full = (root / path).resolve()
    if not full.is_relative_to(root):
        raise ValueError(f"Path escape attempt: {path}")
    return full

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
        try:
            content = _safe_path(repo_root, path).read_text()
        except ValueError as e:
            print(f"[fixer] Skipping {path} — {e}")
            continue
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

    for _ in range(MAX_ITERS):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_calls = [b for b in response.content if b.type == "tool_use"]

        results = []
        for tool in tool_calls:
            if tool.name == "read_file":
                path = tool.input["path"]
                try:
                    out = _safe_path(repo_root, path).read_text()
                except ValueError:
                    out = f"Error: {path} is outside the repo root"
                except FileNotFoundError:
                    out = f"Error: {path} not found"
                results.append({"type": "tool_result", "tool_use_id": tool.id, "content": out})

            elif tool.name == "write_file":
                path = tool.input["path"]
                try:
                    _safe_path(repo_root, path).write_text(tool.input["content"])
                    changed.append(path)
                    print(f"[fixer] Fixed {path}")
                    out = f"Written: {path}"
                except ValueError:
                    out = f"Error: {path} is outside the repo root"
                results.append({"type": "tool_result", "tool_use_id": tool.id, "content": out})

            elif tool.name == "mark_unfixable":
                unfixable.append(f"{tool.input['path']}: {tool.input['reason']}")
                results.append({"type": "tool_result", "tool_use_id": tool.id, "content": "Noted"})

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": results})

        if response.stop_reason != "tool_use":
            break
    else:
        print("[fixer] Hit max iterations — stopping")

    if unfixable:
        print(f"[fixer] Unfixable (manual required): {'; '.join(unfixable)}")

    return changed
