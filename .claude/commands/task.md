You are a coding agent working in a git worktree. Implement the task then open a PR.

## Parse $ARGUMENTS

- `task` = everything before any `--` flags
- `--branch <name>` = explicit branch name (optional)
- `--worktree <path>` = explicit worktree path (optional)
- `--base <branch>` = base branch for the PR (default: `develop`)
- `--help` = print usage and stop

If `--help` is present, print the following and do nothing else:

```
Usage: /task <description> [--branch <name>] [--worktree <path>] [--base <branch>]

  <description>       What to implement (required). Everything before any -- flag.

Options:
  --branch <name>     Use this git branch name instead of auto-generating one.
  --worktree <path>   Use this path for the worktree instead of auto-generating one.
  --base <branch>     Base branch for the PR (default: develop).
  --help              Show this help message.

Modes:
  Auto (Mode B)   No --branch or --worktree given. Branch and worktree path are
                  derived from the description slug.
  Manual (Mode A) --branch or --worktree supplied. Use the explicit values as-is.

Examples:
  /task add dark mode toggle
  /task "fix login redirect bug" --base main
  /task refactor auth module --branch refactor/auth --base develop
```

If `--branch` or `--worktree` is present → **Mode A** (manual). Otherwise → **Mode B** (auto).

---

## Step 1 — Resolve values

| Value | Mode B (auto) | Mode A (manual) |
|---|---|---|
| `BASE` | `develop` (or `--base` value) | same |
| `SLUG` | task slugified: lowercase, hyphens, max 40 chars | same |
| `BRANCH` | `feature/<SLUG>` | `--branch` value |
| `WORKTREE` | `<repo-root>/worktrees/<SLUG>` | `--worktree` value |

Repo root is `/Users/yoshi/Experiment/ade/hive-strategy`.

---

## Step 2 — Create branch and worktree

Run from repo root:

```bash
git fetch origin
git checkout -b <BRANCH> origin/<BASE>
git worktree add <WORKTREE> <BRANCH>
```

All subsequent work happens inside `<WORKTREE>`.

---

## Step 3 — Implement

Read existing code before editing. Do only what the task requires — no extra features, no cleanup beyond scope.

---

## Step 4 — Commit and push

```bash
git -C <WORKTREE> add -A
git -C <WORKTREE> commit -m "<concise description>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git -C <WORKTREE> push -u origin <BRANCH>
```

---

## Step 5 — Open PR

```bash
gh pr create \
  --title "<task summary>" \
  --base <BASE> \
  --body "$(cat <<'EOF'
## Summary
- <bullet: what changed>

## Test plan
- [ ] <step>

🤖 Generated with Claude Code
EOF
)"
```

Print the PR URL.

---

## Step 6 — Cleanup reminder

After the PR merges, the user should run:

```bash
git worktree remove <WORKTREE>
git branch -d <BRANCH>
```
