You are the programmer who authored this PR. Read every open review comment and decide what to do with it, then show me one plan and wait for my go-ahead.

---

## Step 1 — Gather context

Resolve the target PR using this priority order:

1. **Conversation context** — if a `/task` command ran earlier in this conversation and printed a PR URL, extract the PR number from it directly. This is the most reliable source and requires no shell commands.

2. **Current branch** — if no PR is in context, check if the checked-out branch has an open PR:
   ```bash
   PR=$(gh pr view --json number --jq .number 2>/dev/null)
   ```

3. **Worktrees** — if step 2 returns nothing (e.g. we're on `develop` or `main`), scan all worktrees for branches with open PRs and pick the most recently updated one:
   ```bash
   git worktree list --porcelain \
     | awk '/^branch / {print $2}' \
     | sed 's|refs/heads/||' \
     | while read branch; do
         gh pr view "$branch" --json number,updatedAt --jq '[.number, .updatedAt] | @tsv' 2>/dev/null
       done \
     | sort -k2 -r \
     | head -1 \
     | cut -f1
   ```

4. If no PR is found via any method, tell me and stop.

```bash
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
```

Fetch **all** review comments (open and resolved), preserving thread structure:

```bash
gh api repos/$REPO/pulls/$PR/comments \
  --jq '[.[] | {id: .id, path: .path, line: .line, body: .body, in_reply_to_id: .in_reply_to_id, created_at: .created_at, user: .user.login}]'
```

If there are no open top-level comments (`in_reply_to_id == null`), tell me and stop.

## Step 1b — Detect circular reviews

Group all comments by thread (root comment + its replies, linked via `in_reply_to_id`). For each thread on the same `path` + `line`:

1. Read the thread chronologically.
2. Extract what each round suggested: e.g. round 1 → "use A", round 2 (after fix) → "use B", round 3 → "use A again".
3. A thread is **circular** if any suggestion in the current open comment is semantically equivalent to a suggestion that was already applied and later reversed by the same reviewer.

Mark circular threads with decision `ARGUE_CIRCULAR` (see Step 3).

## Step 2 — Read the code and standards

Read the project coding standards so any FIX you apply is consistent with the codebase conventions:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
cat "$REPO_ROOT/docs/coding-standards.md"
cat "$REPO_ROOT/docs/directory-structure.md"
```

Then read the full file referenced by each open comment. Do not judge from the diff alone.

## Step 3 — Decide for each comment

Pick exactly one response per comment:

| Decision | When | Action |
|---|---|---|
| **FIX** | Reviewer is correct — real bug, real issue | Apply the code fix, post an acknowledgement reply |
| **ARGUE** | Reviewer is wrong or the comment is out of scope / incorrect | Post a clear technical reply explaining why; no code change |
| **ARGUE_CIRCULAR** | The reviewer is asking to revert a change they previously requested — oscillating between two positions | Post a reply quoting the contradiction and asking the reviewer to decide definitively; no code change |

For `ARGUE_CIRCULAR`, the reply must:
- Quote the earlier contradicting suggestion (with approximate date/round).
- State what was implemented based on that suggestion.
- Ask the reviewer to pick one direction and resolve the other thread.

## Step 4 — Show me the plan (do NOT act yet)

Present a numbered list like this:

```
PR #N — <N> open comment(s)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1] path/to/file.py:42 — 🐛 BUG
    FIX
    Code change: <one-line description of what you will change>
    Reply: "✅ Fixed — <brief explanation>"

[2] path/to/file.py:88 — ⚡ PERFORMANCE
    ARGUE
    Reply: "💬 This is intentional — <technical reason>"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready to execute. Say "yes" to proceed, or tell me which items to change.
```

## Step 5 — Execute on approval

Only after I say yes (or give modified instructions):

1. Apply all FIX code changes
2. Post all replies:
   ```bash
   gh api repos/$REPO/pulls/$PR/comments/<ID>/replies \
     --method POST -f body="<reply>"
   ```
3. Commit only the changed files:
   ```bash
   git add <changed files>
   git commit -m "fix: address PR review comments

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   ```
4. Push: `git push`
5. Tell me CI will re-run the reviewer. Loop back to Step 1 if I ask.
