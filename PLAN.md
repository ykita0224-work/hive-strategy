# Hive Strategy

> **Primary goal:** Ship the DevOps infrastructure (GitHub MCP + Claude, CI PR-review skill, Slack integration).
> **Secondary goal:** The web app itself (business analysis UI with real-time agent visualization).

---

## What We're Building

**Hive Strategy** is a web app where AI agents collaborate in parallel on business analysis and planning tasks. Users can watch agents think and communicate in real time — each agent visible as it reasons, calls tools, and reaches conclusions. Agents are modular: users can install or upload new "skills" at runtime to extend what the hive can do.

Under the hood, the project is a showcase of modern DevOps: GitHub MCP wired to Claude Code, an automated PR review CI pipeline, and Slack notifications — all self-referentially used to build the product itself.

---

## Phase 0 — Repo & Tooling Bootstrap

**Goal:** Empty repo → working local dev environment with CI skeleton.

### 0.1 Repo Setup
- [ ] `git init` and push to GitHub (repo name: `hive-strategy`)
- [ ] Monorepo structure:
  ```
  hive-strategy/
  ├── apps/
  │   ├── web/               # Next.js frontend (own pnpm + package.json)
  │   └── api/               # FastAPI Python backend (own uv + pyproject.toml)
  ├── packages/
  │   └── agents/            # Shared agent runtime (Python)
  ├── .github/
  │   └── workflows/         # CI pipelines
  ├── .claude/
  │   └── settings.json      # Claude Code MCP config
  ├── mcp/                   # MCP server definitions
  ├── skills/                # Agent skill modules (Python)
  └── PLAN.md
  ```
- [ ] `pnpm` workspace
- [ ] ESLint + Prettier + pre-commit hooks

### 0.2 Branching Strategy
- `main` — protected, no direct push
- `develop` — integration branch
- Feature branches: `feat/<name>`, fix branches: `fix/<name>`
- PRs always target `develop`; `develop` → `main` on release

---

## Phase 1 — GitHub MCP + Claude Integration (PRIMARY)

**Goal:** Claude Code can read/write GitHub PRs, issues, and files via MCP.

### 1.1 MCP Server Setup
- [ ] Add `@modelcontextprotocol/server-github` to the project
- [ ] Configure `.claude/settings.json`:
  ```json
  {
    "mcpServers": {
      "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
        }
      }
    }
  }
  ```
- [ ] Verify Claude can: list PRs, read PR diffs, post comments, read repo files
- [ ] Store token in `.env.local`, document in `.env.example`

### 1.2 GitHub Actions Foundation
- [ ] `ci.yml` — runs on every PR: lint, type-check, unit tests
- [ ] `pr-review.yml` — triggers Claude-powered review (Phase 2)
- [ ] `deploy-preview.yml` — deploys preview URL on PR open
- [ ] Secrets configured in GitHub repo settings: `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `SLACK_WEBHOOK_URL`

---

## Phase 2 — CI PR Auto-Review Skill (PRIMARY)

**Goal:** Every PR gets an automated Claude code review posted as inline GitHub comments.

### 2.1 The Review Skill
- [ ] Create `skills/pr-review/` skill module:
  - `index.ts` — entry point, accepts PR number + repo
  - `reviewer.ts` — calls Claude with the diff and codebase context
  - `github.ts` — posts inline comments via GitHub API
- [ ] Review dimensions:
  - Correctness bugs
  - Security issues (OWASP top 10)
  - Performance concerns
  - Test coverage gaps
  - Architecture consistency

### 2.2 CI Integration
- [ ] `pr-review.yml` workflow:
  ```yaml
  on:
    pull_request:
      types: [opened, synchronize]
  jobs:
    ai-review:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - run: pnpm install
        - run: pnpm skill:pr-review
          env:
            ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            PR_NUMBER: ${{ github.event.pull_request.number }}
  ```
- [ ] Rate limit handling (large PRs → chunk the diff)
- [ ] Skip label: `skip-ai-review` on PR to bypass

### 2.3 Claude Code Skill (`.claude/`)
- [ ] Register as a slash command: `/review` → runs the PR review skill locally
- [ ] Can be run manually before pushing: `claude /review`

---

## Phase 3 — Slack Integration (PRIMARY)

**Goal:** Agent activity, PR review results, and deploy events post to Slack.

### 3.1 Slack App Setup
- [ ] Create Slack App via api.slack.com
- [ ] Channels:
  - `#hive-prs` — PR opened/merged/reviewed events
  - `#hive-deploys` — deploy status
  - `#hive-agents` — agent run summaries (Phase 4+)
- [ ] Incoming Webhook configured, URL stored in GitHub secrets + `.env.local`

### 3.2 Notification Skill
- [ ] `skills/notify/` — thin wrapper around Slack Webhook API
- [ ] Message templates: PR review summary, deploy success/fail, agent task complete
- [ ] Called from CI workflows after each job
- [ ] Called from agent runtime when a task finishes

### 3.3 Slash Commands (optional stretch)
- [ ] `/hive status` in Slack → returns current agent queue status
- [ ] `/hive review <PR#>` → triggers a manual PR review from Slack

---

## Phase 4 — Agent Runtime (SECONDARY)

**Goal:** Multi-agent system that runs business analysis tasks, with skills loadable at runtime.

### 4.1 Agent Architecture
```
AgentOrchestrator
├── AgentRunner          # Executes a single agent (Claude API call loop)
├── SkillRegistry        # Loads/unloads skill modules
├── EventBus             # Broadcasts agent events (SSE to frontend)
└── TaskQueue            # Manages parallel agent execution
```

### 4.2 Skill System
- Each skill is a directory in `skills/`:
  ```
  skills/
  ├── pr-review/          # Phase 2
  ├── notify/             # Phase 3
  ├── market-research/    # Business analysis skills
  ├── financial-analysis/
  └── swot/
  ```
- Skills export: `name`, `description`, `systemPrompt`, `tools[]`
- Users can upload new skill folders via the web UI → hot-reloaded into registry

### 4.3 Agent Personas (for business analysis)
- `CFO` — financial risk, cost modeling
- `CMO` — market positioning, GTM
- `Strategist` — SWOT, competitive landscape
- `Devil's Advocate` — challenges assumptions
- Orchestrator decides which personas to spawn per task

### 4.4 Streaming & Parallelism
- Claude API with `stream: true` on each agent
- Server-Sent Events (SSE) endpoint: `GET /api/agents/stream`
- Each agent emits events: `thinking`, `tool_call`, `message`, `done`
- Multiple agents run concurrently via `Promise.all` / worker pool

---

## Phase 5 — Web UI (SECONDARY)

**Goal:** Visual dashboard showing agents working in real time.

### 5.1 Tech Stack
- Next.js 15 (App Router)
- Tailwind CSS + shadcn/ui
- Zustand for agent state
- `EventSource` API for SSE consumption

### 5.2 Key Views
- **Task input** — enter a business question or upload a doc
- **Agent canvas** — cards per agent, streaming their current thought + tool calls
- **Timeline** — chronological log of all agent messages, color-coded by persona
- **Skill manager** — list installed skills, upload new ones, toggle active/inactive
- **Output panel** — final synthesized report with citations

### 5.3 Real-Time Agent Visualization
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  CFO Agent      │  │  CMO Agent      │  │  Strategist     │
│  ● thinking...  │  │  ✓ done         │  │  ⟳ searching    │
│                 │  │                 │  │                 │
│  "Analyzing     │  │  "Market size   │  │  [tool: web     │
│  burn rate..."  │  │  est. $2.3B"    │  │   search...]    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Tech Stack Summary

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Next.js 15 + Tailwind | SSE support, App Router streaming |
| Backend | FastAPI (Python 3) | Richer AI/ML ecosystem, async SSE support |
| AI | Claude Sonnet 4.6 | Best tool-use, streaming |
| Agent SDK | Anthropic SDK + custom runtime | Full control over streaming events |
| MCP | `@modelcontextprotocol/server-github` | Phase 1 |
| DB | PostgreSQL + Prisma | Task history, agent logs |
| Queue | BullMQ (Redis) | Parallel agent jobs |
| CI | GitHub Actions | PR review, deploy pipeline |
| Notifications | Slack Incoming Webhooks | Phase 3 |
| Hosting | Vercel (web) + Fly.io or Railway (api) | Easy preview deploys |

---

## Execution Order

```
Phase 0  →  Phase 1  →  Phase 2  →  Phase 3  →  Phase 4  →  Phase 5
(repo)      (MCP)        (CI PR     (Slack)      (agents)    (UI)
                          review)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRIMARY GOAL COMPLETE AFTER PHASE 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Success Criteria

### DevOps (Primary)
- [ ] Opening a PR triggers Claude to post inline code review comments automatically
- [ ] Slack `#hive-prs` gets notified on PR open, review complete, and merge
- [ ] Claude Code (local) can use `/review` to run the same review manually via MCP
- [ ] All secrets managed via GitHub Secrets, never hardcoded

### Web App (Secondary)
- [ ] Multiple agents run in parallel on a business question
- [ ] Users can watch agent reasoning stream in real time in the UI
- [ ] Users can upload a new skill folder and agents use it immediately
- [ ] Final analysis report is exportable

---

## Open Questions

1. **Backend language**: Node.js or Python (FastAPI)? Python has a richer AI ecosystem; Node keeps the stack uniform.
2. **Skill format**: Directory with config file, or npm packages the user installs?
3. **Auth**: Start with no auth (local dev only) or add Clerk/Auth.js from day one?
4. **Agent memory**: Stateless per-task or persistent memory across sessions?
