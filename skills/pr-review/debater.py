"""
Debater agent — the programmer argues back against reviewer comments.

For each review comment the programmer either:
  ACCEPT — reviewer is right, proceed to auto-fix
  ARGUE  — code is intentional, posts an explanation as a reply thread

Accepted comments are returned for the fixer to action.
Argued comments get a reply posted to the PR so the thread is visible in Cursor/VSCode.
"""

from dataclasses import dataclass
import anthropic
import httpx
from github import ReviewComment

GITHUB_API = "https://api.github.com"

SYSTEM_PROMPT = """You are the engineer who authored this pull request.
A reviewer has flagged some issues. For each comment, decide:

ACCEPT  — the reviewer is correct and the issue should be fixed
ARGUE   — the code is intentionally written this way and the reviewer is wrong

Rules for ACCEPT:
- The reviewer identified a real bug, security flaw, or critical issue
- The fix is clear and safe

Rules for ARGUE:
- The code is correct and the reviewer misunderstood the intent
- The "issue" is a false positive or a style preference, not a real problem
- The pattern is intentional (e.g., a specific API contract, a known trade-off)

Be professional. When arguing, explain the technical reason clearly and concisely.
Do not argue just to avoid fixing things — only argue when genuinely correct."""

VERDICT_TOOL = {
    "name": "submit_verdicts",
    "description": "Submit accept/argue decision for each review comment",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "comment_id": {"type": "integer"},
                        "path": {"type": "string"},
                        "line": {"type": "integer"},
                        "decision": {"type": "string", "enum": ["ACCEPT", "ARGUE"]},
                        "reply": {
                            "type": "string",
                            "description": "Reply to post on the PR thread. For ACCEPT: brief ack. For ARGUE: technical explanation.",
                        },
                    },
                    "required": ["comment_id", "path", "line", "decision", "reply"],
                },
            }
        },
        "required": ["verdicts"],
    },
}


@dataclass
class Verdict:
    comment_id: int
    comment: ReviewComment
    decision: str  # ACCEPT or ARGUE
    reply: str


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_review_comments(
    repo: str, pr_number: int, review_id: int, token: str
) -> list[dict]:
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/reviews/{review_id}/comments"
    resp = httpx.get(url, headers=_headers(token), timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def post_reply(repo: str, comment_id: int, body: str, token: str) -> None:
    url = f"{GITHUB_API}/repos/{repo}/pulls/comments/{comment_id}/replies"
    resp = httpx.post(url, headers=_headers(token), json={"body": body}, timeout=30.0)
    resp.raise_for_status()


def debate(
    repo: str,
    pr_number: int,
    review_id: int,
    comments: list[ReviewComment],
    token: str,
    client: anthropic.Anthropic,
) -> list[ReviewComment]:
    """
    Run the programmer agent debate.
    Posts replies to all comments on the PR.
    Returns only the ACCEPT-ed comments for the fixer to action.
    """
    gh_comments = get_review_comments(repo, pr_number, review_id, token)
    id_map = {(c["path"], c["line"]): c["id"] for c in gh_comments if c.get("line")}

    debateable = [c for c in comments if c.line and (c.path, c.line) in id_map]
    if not debateable:
        print("[debater] No comments with resolvable thread IDs")
        return []

    comment_context = "\n".join(
        f"[comment_id={id_map[(c.path, c.line)]} path={c.path} line={c.line}]\n{c.body}"
        for c in debateable
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[VERDICT_TOOL],
        tool_choice={"type": "tool", "name": "submit_verdicts"},
        messages=[
            {
                "role": "user",
                "content": f"Review comments on your PR:\n\n{comment_context}\n\nFor each comment, decide ACCEPT or ARGUE and write a reply.",
            }
        ],
    )

    tool_use = next((b for b in message.content if b.type == "tool_use"), None)
    if not tool_use:
        raise RuntimeError(
            f"Model did not return a tool_use block (stop_reason={message.stop_reason!r})."
        )

    verdicts = tool_use.input["verdicts"]
    accepted: list[ReviewComment] = []

    for v in verdicts:
        comment_id = v.get("comment_id")
        if not comment_id:
            print(f"[debater] Warning: no comment_id for {v['path']}:{v.get('line')} — skipping reply")
        decision = v["decision"]
        reply_body = f"**[{'✅ Accepted' if decision == 'ACCEPT' else '💬 Argued'}]** {v['reply']}"

        # Post reply thread to PR (visible in Cursor/VSCode)
        if comment_id:
            try:
                post_reply(repo, comment_id, reply_body, token)
                print(f"[debater] {decision} on {v['path']}:{v['line']}")
            except Exception as e:
                print(f"[debater] Could not post reply to {comment_id}: {e}")

        if decision == "ACCEPT":
            matching = [c for c in debateable if c.path == v["path"] and c.line == v["line"]]
            accepted.extend(matching)

    print(f"[debater] {len(accepted)}/{len(debateable)} comment(s) accepted for auto-fix")
    return accepted
