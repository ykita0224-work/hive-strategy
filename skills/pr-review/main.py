"""
PR review skill — autonomous review + debate + fix loop.

Flow:
  1. Reviewer agent   → reads PR diff, posts inline comments
  2. Programmer agent → argues back or accepts each comment
  3. Fixer agent      → auto-fixes accepted issues, commits + pushes
  4. Push triggers a new CI run — loop continues until no fixable issues remain

Loop guard: stops after MAX_AI_FIX_ITERATIONS consecutive AI-fix commits.

Required env vars:
  ANTHROPIC_API_KEY  — Anthropic API key
  GITHUB_TOKEN       — GitHub token (pull_requests:write + contents:write)
  PR_NUMBER          — Pull request number
  REPO               — e.g. ykita0224-work/hive-strategy
"""

import os
import sys
import subprocess
import anthropic

from github import get_pr_files, get_pr_commit_sha, post_review
from reviewer import review_diff
from debater import debate
from fixer import fix_issues

MAX_AI_FIX_ITERATIONS = 5
AI_FIX_MARKER = "[ai-fix-"


def count_consecutive_ai_fixes() -> int:
    result = subprocess.run(
        ["git", "log", "--oneline", "-20"],
        capture_output=True, text=True,
    )
    count = 0
    for line in result.stdout.splitlines():
        if AI_FIX_MARKER in line:
            count += 1
        else:
            break  # stop at first non-AI commit
    return count


def commit_and_push(changed_files: list[str], pr_number: int, iteration: int) -> bool:
    subprocess.run(["git", "config", "user.email", "ci-bot@hive-strategy.dev"], check=True)
    subprocess.run(["git", "config", "user.name", "Hive Strategy CI"], check=True)

    for path in changed_files:
        subprocess.run(["git", "add", path], check=True)

    staged = subprocess.run(["git", "diff", "--staged", "--quiet"])
    if staged.returncode == 0:
        print("[main] Nothing to commit after fixes")
        return False

    msg = f"fix: {AI_FIX_MARKER}{iteration}] auto-fix review findings on PR #{pr_number}"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push"], check=True)
    print(f"[main] Pushed AI fix commit (iteration {iteration})")
    return True


def main() -> None:
    github_token = os.environ["GITHUB_TOKEN"]
    anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]
    pr_number = int(os.environ["PR_NUMBER"])
    repo = os.environ["REPO"]

    print(f"[main] Reviewing PR #{pr_number} on {repo}")

    # Guard against runaway loop
    consecutive_fixes = count_consecutive_ai_fixes()
    if consecutive_fixes >= MAX_AI_FIX_ITERATIONS:
        print(
            f"[main] Reached max AI fix iterations ({MAX_AI_FIX_ITERATIONS}). "
            "Stopping to avoid infinite loop — manual review required."
        )
        return

    client = anthropic.Anthropic(api_key=anthropic_api_key)

    # Step 1 — Review
    files = get_pr_files(repo, pr_number, github_token)
    print(f"[main] {len(files)} changed file(s)")

    commit_sha = get_pr_commit_sha(repo, pr_number, github_token)
    summary, comments = review_diff(files, client)
    print(f"[main] {len(comments)} comment(s) from reviewer")

    if not comments:
        print(f"[main] No issues found. Summary: {summary}")
        # Post a clean summary comment
        post_review(repo, pr_number, commit_sha, [], github_token, f"✅ {summary}", files)
        return

    review_id = post_review(repo, pr_number, commit_sha, comments, github_token, summary, files)

    # Step 2 — Debate: programmer argues back or accepts each comment
    accepted = debate(repo, pr_number, review_id, comments, github_token, client)

    if not accepted:
        print("[main] All comments argued — no auto-fixes to apply")
        return

    # Step 3 — Fix accepted issues
    changed = fix_issues(accepted, client)

    if not changed:
        print("[main] Fixer made no changes")
        return

    # Step 4 — Commit + push (triggers next CI run)
    commit_and_push(changed, pr_number, consecutive_fixes + 1)


if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"[main] Missing required env var: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[main] Error: {e}", file=sys.stderr)
        raise
