"""
PR review skill — CI mode (review only).

Runs on every PR push via GitHub Actions. Posts inline review comments.
Does NOT auto-fix or argue — that happens interactively in Cursor/Claude Code
with human approval before anything is pushed.

Full flow:
  CI:     review only  →  posts comments on GitHub PR
  Cursor: /debate      →  proposes arguments/fixes, waits for approval, then pushes

Required env vars:
  ANTHROPIC_API_KEY  — Anthropic API key
  GITHUB_TOKEN       — GitHub token with pull_requests:write scope
  PR_NUMBER          — Pull request number
  REPO               — e.g. ykita0224-work/hive-strategy
"""

import json
import os
import re
import sys
import anthropic
import httpx

from github import get_pr_files, get_pr_commit_sha, get_existing_review_comments, post_review
from reviewer import review_diff

INPUT_PRICE_PER_M = 3.00
OUTPUT_PRICE_PER_M = 15.00
JPY_PER_USD = 155
COST_MARKER = "<!-- pr-cost-data:"


def _gh_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_issue_comments(repo: str, pr_number: int, token: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    resp = httpx.get(url, headers=_gh_headers(token), timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def _upsert_cost_comment(
    repo: str,
    pr_number: int,
    token: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    comments = _get_issue_comments(repo, pr_number, token)
    existing = next((c for c in comments if COST_MARKER in c.get("body", "")), None)

    if existing:
        match = re.search(r"<!-- pr-cost-data: ({.*?}) -->", existing["body"])
        if match:
            prior = json.loads(match.group(1))
            input_tokens += prior.get("input_tokens", 0)
            output_tokens += prior.get("output_tokens", 0)
            runs = prior.get("runs", 0) + 1
        else:
            runs = 1
    else:
        runs = 1

    total_usd = (input_tokens / 1_000_000 * INPUT_PRICE_PER_M
                 + output_tokens / 1_000_000 * OUTPUT_PRICE_PER_M)
    total_jpy = total_usd * JPY_PER_USD

    data = {"input_tokens": input_tokens, "output_tokens": output_tokens,
            "runs": runs, "total_usd": round(total_usd, 6)}
    body = (
        f"{COST_MARKER} {json.dumps(data)} -->\n"
        f"💰 Review run #{runs} — "
        f"{input_tokens:,} in / {output_tokens:,} out tokens — "
        f"${total_usd:.4f} / ¥{total_jpy:.1f}"
    )

    headers = _gh_headers(token)
    if existing:
        url = f"https://api.github.com/repos/{repo}/issues/comments/{existing['id']}"
        httpx.patch(url, headers=headers, json={"body": body}, timeout=30.0).raise_for_status()
        print(f"[cost] Updated cost comment (run #{runs}): ${total_usd:.4f} / ¥{total_jpy:.1f}")
    else:
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        httpx.post(url, headers=headers, json={"body": body}, timeout=30.0).raise_for_status()
        print(f"[cost] Posted cost comment (run #{runs}): ${total_usd:.4f} / ¥{total_jpy:.1f}")


def main() -> None:
    github_token = os.environ["GITHUB_TOKEN"]
    anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]
    pr_number = int(os.environ["PR_NUMBER"])
    repo = os.environ["REPO"]

    print(f"[review] PR #{pr_number} on {repo}")

    client = anthropic.Anthropic(api_key=anthropic_api_key)

    files = get_pr_files(repo, pr_number, github_token)
    print(f"[review] {len(files)} changed file(s)")

    existing_comments = get_existing_review_comments(repo, pr_number, github_token)
    print(f"[review] {len(existing_comments)} existing comment(s) from prior reviews")

    commit_sha = get_pr_commit_sha(repo, pr_number, github_token)
    try:
        summary, comments, usage = review_diff(files, client, existing_comments)
    except RuntimeError as e:
        print(f"[review] Warning: {e}", file=sys.stderr)
        post_review(
            repo, pr_number, commit_sha, [], github_token,
            f"⚠️ Review could not be completed: {str(e)[:200]}", files,
        )
        return
    print(f"[review] {len(comments)} issue(s) found")

    if usage:
        try:
            _upsert_cost_comment(repo, pr_number, github_token,
                                 usage.input_tokens, usage.output_tokens)
        except Exception as e:
            print(f"[cost] Warning: could not post cost comment: {e}", file=sys.stderr)

    if not comments:
        post_review(repo, pr_number, commit_sha, [], github_token, f"✅ {summary}", files)
        print("[review] Clean — no issues found")
        return

    post_review(repo, pr_number, commit_sha, comments, github_token, summary, files)
    print("[review] Comments posted — open Cursor to debate and fix")


if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"[review] Missing required env var: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[review] Error: {e}", file=sys.stderr)
        raise
