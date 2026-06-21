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

import os
import sys
import anthropic

from github import get_pr_files, get_pr_commit_sha, get_existing_review_comments, post_review
from reviewer import review_diff


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
        summary, comments = review_diff(files, client, existing_comments)
    except RuntimeError as e:
        print(f"[review] Warning: {e}", file=sys.stderr)
        post_review(
            repo, pr_number, commit_sha, [], github_token,
            f"⚠️ Review could not be completed: {e}", files,
        )
        return
    print(f"[review] {len(comments)} issue(s) found")

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
