# Coding Standards

## 1. Server vs Client Components

Every file in `app/` is a **Server Component by default**. Only add `"use client"` when the component needs:
- Browser APIs (`EventSource`, `localStorage`, `window`)
- React state (`useState`, `useReducer`)
- React effects (`useEffect`)
- Event listeners (`onClick`, `onChange`)

**Push `"use client"` as deep as possible.** Keep pages and layouts as Server Components; only the interactive leaf nodes should be client components.

```
// Good — page is a Server Component, only the interactive grid is a client component
app/analyze/page.tsx          // no "use client"
app/analyze/_components/AgentGrid.tsx   // "use client"

// Bad — entire page is client-rendered for no reason
app/analyze/page.tsx          // "use client" at the top
```

## 2. Hooks

- Hook files are named `useSomething.ts` (camelCase, `use` prefix).
- Hooks that are only used by one route live in `app/[route]/_hooks/`.
- Hooks shared across multiple routes live in `hooks/[domain]/`.
- A hook file must include `"use client"` at the top because hooks can only run in client components.
- Never put data fetching in a hook when a Server Component can do it directly — hooks are for client-side state and browser APIs.

## 3. SSE (Server-Sent Events)

Use SSE for streaming responses that push multiple updates over time (e.g., streaming AI agent results).

**Route handler** (`app/api/[feature]/stream/route.ts`):
```ts
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const send = (data: object) =>
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));

      // push events...
      send({ type: "done" });
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
```

**Client hook** (`app/[route]/_hooks/useSomethingStream.ts`):
```ts
"use client";
// Open EventSource, parse messages, manage state, close on done/error/unmount.
// Always close the EventSource in a useEffect cleanup.
useEffect(() => () => { esRef.current?.close(); }, []);
```

**Event message schema** — always include a `type` discriminant:
```ts
{ type: "start", ... }
{ type: "agent", id: string, text: string }
{ type: "done" }
{ type: "error", message: string }
```

## 4. SSR (Server-Side Rendering)

- `page.tsx` files are Server Components — fetch data and render HTML on the server.
- Use `redirect()` from `next/navigation` for server-side redirects (no client-side flash).
- `searchParams` and `params` are **Promises** in Next.js 15 — always `await` them.

```ts
// Good
export default async function Page({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams;
  if (!q) redirect("/");
  // ...
}
```

- Avoid `useSearchParams()` in Server Components — read from the `searchParams` prop instead.

## 5. Feature modules (`features/`)

Each feature under `features/` is self-contained. A feature folder owns:

| File | Contains |
|---|---|
| `agents.ts` | Domain entities and static data |
| `constants.ts` | Types, enums, style/label maps |
| `actions.ts` | Server Actions (form mutations, CRUD) |
| `types.ts` | TypeScript interfaces for the feature |

Import from features using the `@/` alias:
```ts
import { AGENTS } from "@/features/analyze/agents";
import type { Status } from "@/features/analyze/constants";
```

## 6. Path aliases

`@/` resolves to the `apps/web/` root (configured in `tsconfig.json`).

```ts
// Good
import { AGENTS } from "@/features/analyze/agents";
import { Button } from "@/components/ui/Button";

// Avoid deep relative paths across feature boundaries
import { AGENTS } from "../../../features/analyze/agents"; // bad
```

Relative imports are fine within the same feature or route folder:
```ts
import { useAnalysisStream } from "../_hooks/useAnalysisStream"; // fine — same route
```

## 7. ESLint

Config lives in `apps/web/eslint.config.mjs` (ESLint v9 flat config). Extends `next/core-web-vitals` via `FlatCompat`.

Do not add `.eslintrc.json` or `.eslintrc.js` — ESLint v9 ignores them.

## 8. General

- No `"use client"` in `features/` or `lib/` — these are shared modules used by both server and client code.
- No business logic directly in `page.tsx` — keep pages thin. Data fetching goes in `lib/`, mutations in `actions.ts`, state in hooks.
- Route-private folders use the `_` prefix (`_components/`, `_hooks/`) so Next.js does not treat them as routes.
- Route groups use parentheses (`(marketing)/`, `(dashboard)/`) to organise routes without affecting the URL.
