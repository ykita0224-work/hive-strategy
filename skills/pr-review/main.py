"""
PR review skill entry point.

Required env vars:
  ANTHROPIC_API_KEY  — Anthropic API key
  GITHUB_TOKEN       — GitHub token with pull_requests:write scope
  PR_NUMBER          — Pull request number (integer)
  REPO               — Repository in owner/name format (e.g. ykita0224-work/hive-strategy)
"""

import os
import sys
import anthropic
from github import get_pr_files, get_pr_commit_sha, post_review
from reviewer import review_diff


def main() -> None:
    github_token = os.environ["GITHUB_TOKEN"]
    anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]
    pr_number = int(os.environ["PR_NUMBER"])
    repo = os.environ["REPO"]

    print(f"[pr-review] Reviewing PR #{pr_number} on {repo}")

    client = anthropic.Anthropic(api_key=anthropic_api_key)

    files = get_pr_files(repo, pr_number, github_token)
    print(f"[pr-review] {len(files)} changed file(s)")

    commit_sha = get_pr_commit_sha(repo, pr_number, github_token)

    summary, comments = review_diff(files, client)
    print(f"[pr-review] {len(comments)} comment(s) generated")

    post_review(repo, pr_number, commit_sha, comments, github_token, summary, files)
    print("[pr-review] Done")


if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"[pr-review] Missing required env var: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[pr-review] Error: {e}", file=sys.stderr)
        sys.exit(1)
