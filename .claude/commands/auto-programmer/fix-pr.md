You are the programmer who authored this PR. Read every open review comment and decide what to do with it, then show me one plan and wait for my go-ahead.

---

## Step 1 — Gather context

```bash
PR=$(gh pr view --json number --jq .number)
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
```

Stop immediately if there is no open PR on this branch.

Fetch open top-level comments (not yet replied to):

```bash
gh api repos/$REPO/pulls/$PR/comments \
  --jq '[.[] | select(.in_reply_to_id == null) | {id: .id, path: .path, line: .line, body: .body}]'
```

If there are no open comments, tell me and stop.

## Step 2 — Read the code

For each comment, read the full file it references. Do not judge from the diff alone.

## Step 3 — Decide for each comment

Pick exactly one response per comment:

| Decision | When | Action |
|---|---|---|
| **FIX** | Reviewer is correct — real bug, real issue | Apply the code fix, post an acknowledgement reply |
| **ARGUE** | Reviewer is wrong or the comment is out of scope / incorrect | Post a clear technical reply explaining why; no code change |

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
   gh api repos/$REPO/pulls/comments/<ID>/replies \
     --method POST --field body="<reply>"
   ```
3. Commit only the changed files:
   ```bash
   git add <changed files>
   git commit -m "fix: address PR review comments

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   ```
4. Push: `git push`
5. Tell me CI will re-run the reviewer. Loop back to Step 1 if I ask.
