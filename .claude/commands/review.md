Run the AI code review skill against the current branch's pull request and post inline comments to GitHub.

Steps:
1. Find the PR number for the current branch by running: `gh pr view --json number --jq .number`
   - If the command fails or returns nothing, tell the user no open PR was found for this branch and stop.
2. Load env vars from `.env.local` in the repo root if it exists.
3. Run the skill: `REPO=ykita0224-work/hive-strategy PR_NUMBER=<number> python skills/pr-review/main.py`
4. Report the result — how many inline comments were posted, and show the summary Claude produced.
   - If there were errors, explain what went wrong.

Notes:
- ANTHROPIC_API_KEY and GITHUB_TOKEN must be set (from .env.local or shell environment).
- The skill only comments on lines that appear in the diff — it will not hallucinate line positions.
- Add the label `skip-ai-review` to the PR to bypass this in CI.
