Respond to open PR review comments as the programmer. Propose a response plan (ARGUE / ASK / ACCEPT+FIX) for each comment, show it to me for approval, then execute on my say-so.

Steps:

1. Find the current PR number:
   ```
   gh pr view --json number --jq .number
   ```
   Stop if no open PR exists on this branch.

2. Fetch all open reviewer comments (top-level, not yet replied to):
   ```
   gh api repos/ykita0224-work/hive-strategy/pulls/<PR>/comments \
     --jq '[.[] | select(.in_reply_to_id == null)]'
   ```

3. For each comment, read the full file at the referenced path. Do not rely on the diff alone.

4. For each comment decide:
   - **ARGUE** — code is correct, reviewer misunderstood → draft a technical rebuttal
   - **ASK** — reviewer intent unclear → draft a clarifying question
   - **ACCEPT + FIX** — issue is real → describe the fix you will make

5. Present the full plan clearly, numbered, with the decision and proposed reply for each comment. Do not execute anything yet.

6. Wait for me to say "yes", "skip N", "change N to ARGUE/ASK/ACCEPT", or "no".

7. On approval:
   - Post each reply via: `gh api repos/ykita0224-work/hive-strategy/pulls/comments/<ID>/replies --method POST --field body="<reply>"`
   - Apply code fixes for ACCEPT items
   - Commit: `git commit -m "fix: address review comments — <summary>\n\nCo-Authored-By: Claude"`
   - Push: `git push`
   - Tell me CI will re-review and we loop back to step 2
