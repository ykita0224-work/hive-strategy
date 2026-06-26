# Directory Structure

## Top-level

```
hive-strategy/
├── apps/
│   └── web/               # Next.js frontend
├── docs/                  # Engineering standards (this folder)
└── skills/                # Claude Code skills
```

## `apps/web/` — Next.js app

```
apps/web/
├── app/                   # Next.js App Router — routes only
│   ├── api/               # Route Handlers (SSE, REST, webhooks)
│   │   └── [feature]/
│   │       └── [action]/
│   │           └── route.ts
│   ├── [route]/
│   │   ├── _components/   # Route-local client components (private — not a route)
│   │   ├── _hooks/        # Route-local use* hooks (private — not a route)
│   │   ├── layout.tsx     # Route layout (Server Component)
│   │   └── page.tsx       # Route page (Server Component by default)
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
│
├── features/              # Self-contained feature modules
│   └── [feature]/
│       ├── agents.ts      # Domain data / entities
│       ├── constants.ts   # Types, enums, style maps
│       ├── actions.ts     # Server Actions (mutations)
│       └── types.ts       # TypeScript types for the feature
│
├── components/            # Shared, reusable UI (used across multiple routes)
│   ├── ui/                # Primitives: Button, Input, Modal, Badge
│   ├── layout/            # Navbar, Sidebar, Footer
│   └── shared/            # LoadingSpinner, EmptyState, ErrorBoundary
│
├── hooks/                 # Global shared use* hooks (used across multiple routes)
│   ├── common/            # useDebounce, useLocalStorage, useMediaQuery
│   └── [domain]/          # useAuth, useSession, etc.
│
├── lib/                   # Utilities and external service clients
│   ├── db.ts              # Database client
│   ├── auth.ts            # Auth helpers
│   └── utils.ts           # General utilities
│
└── types/                 # Global TypeScript types shared across the app
```

## Rules: where does a file go?

| What | Where |
|---|---|
| Custom `use*` hook used by one route only | `app/[route]/_hooks/` |
| Custom `use*` hook shared across routes | `hooks/[domain]/` |
| Client component used by one route only | `app/[route]/_components/` |
| Client component shared across routes | `components/ui/` or `components/shared/` |
| Domain data, types, constants for a feature | `features/[feature]/` |
| External API call or DB query | `lib/` |
| Server mutation (form submit, CRUD) | `features/[feature]/actions.ts` |
| SSE / REST / webhook endpoint | `app/api/[feature]/[action]/route.ts` |

## Current feature: `analyze`

```
app/
├── api/analyze/stream/route.ts          # SSE stream — one result per agent
├── analyze/
│   ├── _components/AgentGrid.tsx        # "use client" — renders grid + run button
│   ├── _hooks/useAnalysisStream.ts      # EventSource hook
│   └── page.tsx                         # Server Component — SSR entry point

features/analyze/
├── agents.ts                            # Agent interface + AGENTS data
└── constants.ts                         # Status type + STATUS_STYLES/LABEL
```
