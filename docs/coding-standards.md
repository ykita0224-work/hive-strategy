# Coding Standards

## File placement

| File type | Where it goes | Example |
|---|---|---|
| Route entry point | `app/[route]/page.tsx` | `app/analyze/page.tsx` |
| Route layout | `app/[route]/layout.tsx` | `app/analyze/layout.tsx` |
| Client component used by one route | `app/[route]/_components/Name.tsx` | `app/analyze/_components/AgentGrid.tsx` |
| Client component shared across routes | `components/ui/Name.tsx` | `components/ui/Button.tsx` |
| Layout component (nav, sidebar, footer) | `components/layout/Name.tsx` | `components/layout/Navbar.tsx` |
| `use*` hook used by one route | `app/[route]/_hooks/useName.ts` | `app/analyze/_hooks/useAnalysisStream.ts` |
| `use*` hook shared across routes | `hooks/[domain]/useName.ts` | `hooks/common/useDebounce.ts` |
| SSE / REST / webhook endpoint | `app/api/[feature]/[action]/route.ts` | `app/api/analyze/stream/route.ts` |
| Domain data and static entities | `features/[feature]/agents.ts` | `features/analyze/agents.ts` |
| Types, enums, style maps | `features/[feature]/constants.ts` | `features/analyze/constants.ts` |
| TypeScript interfaces for a feature | `features/[feature]/types.ts` | `features/analyze/types.ts` |
| Server Actions (mutations) | `features/[feature]/actions.ts` | `features/analyze/actions.ts` |
| External service clients (DB, auth) | `lib/name.ts` | `lib/db.ts` |
| Shared utility functions | `lib/utils.ts` | `lib/utils.ts` |
| Global TypeScript types | `types/name.ts` | `types/api.ts` |

---

## `"use client"` directive

Add `"use client"` only when a file uses:
- React state or effects (`useState`, `useReducer`, `useEffect`)
- Browser APIs (`EventSource`, `localStorage`, `window`)
- Event handlers (`onClick`, `onChange`)

Never add `"use client"` to files in `features/`, `lib/`, or `types/` — these are shared by both server and client code.

Push `"use client"` as deep as possible. Pages and layouts stay as Server Components; only the interactive leaf component gets the directive.

---

## `"use client"` in hooks

Every hook file (`use*.ts`) must have `"use client"` at the top. Hooks run on the client only.

---

## SSR rules (Next.js 15)

- `page.tsx` is a Server Component by default — do not add `"use client"` unless the entire page is interactive with no server-rendered content.
- Read `searchParams` from the page props, not from `useSearchParams()`.
- `searchParams` and `params` are Promises in Next.js 15 — always `await` them.
- Use `redirect()` from `next/navigation` for server-side redirects.

---

## SSE rules

- SSE endpoints live at `app/api/[feature]/stream/route.ts`.
- Always export `export const dynamic = "force-dynamic"` in SSE route handlers.
- Every SSE message must have a `type` field: `"start"`, `"update"`, `"done"`, `"error"`.
- The consuming hook lives at `app/[route]/_hooks/use[Feature]Stream.ts`.
- Always close the `EventSource` in a `useEffect` cleanup — never leave it open on unmount.

---

## Import paths

Use the `@/` alias (resolves to `apps/web/`) for any import that crosses a folder boundary:

```ts
import { AGENTS } from "@/features/analyze/agents";
import { Button } from "@/components/ui/Button";
import type { Status } from "@/features/analyze/constants";
```

Use relative imports only within the same route or feature folder:

```ts
import { useAnalysisStream } from "../_hooks/useAnalysisStream";
import { AgentCard } from "./AgentCard";
```

---

## Private folders

Prefix with `_` to prevent Next.js from treating a folder as a route:

- `_components/` — components private to a route
- `_hooks/` — hooks private to a route

---

## Route groups

Wrap in parentheses to organise routes without affecting the URL:

- `(marketing)/` — public-facing pages
- `(dashboard)/` — authenticated pages

---

## ESLint

Config: `apps/web/eslint.config.mjs` (ESLint v9 flat config, `next/core-web-vitals`).

Do not create `.eslintrc.json` or `.eslintrc.js` — ESLint v9 ignores them.
