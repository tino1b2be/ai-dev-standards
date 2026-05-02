---
inclusion: always
---

# Frontend web application standards

Application-level conventions for TypeScript frontend web projects:
framework choice, component architecture, state, routing, API clients,
forms, styling, assets, accessibility, performance, and testing. Scope
here is the browser runtime and the code that ships to it. Language-level
TypeScript guidance lives in `core/languages/typescript.md`;
deployment/hosting (S3, CloudFront, Amplify) lives in
`core/platforms/aws.md` or the serverless platform files.

## Framework choice

- **Pick one framework per project and commit.** Mixing React with Vue,
  or shipping two parallel routing stacks, is a finding.
- **Defaults.** Use **Next.js** for apps that need SSR, ISR, or
  server-driven routing. Use **Vite + React** for single-page apps that
  render entirely in the browser. Reach for other frameworks only when
  the defaults demonstrably do not fit.
- **TypeScript strict mode, no exceptions.** `strict: true` in
  `tsconfig.json`. Opting out to silence errors is a finding.
- **One build tool.** Vite, Next's bundler, or a single equivalent. Do
  not run Webpack and Vite side-by-side on the same app.
- **Supported browsers are explicit.** Declare the browserslist target
  in `package.json` or `.browserslistrc`. Do not ship targeting "latest"
  browsers without saying so.

## Component architecture

- **Small, focused components.** One component does one thing. Files
  over ~200 lines are a smell; split before adding more.
- **Composition over inheritance.** Components do not extend each
  other. Compose behavior with hooks, render props, or child components.
- **Colocate logic with the component that uses it.** Extract a hook
  when the same logic repeats in two places, not preemptively.
- **Props are typed explicitly.** No `any`, no implicit `props: object`.
  Use discriminated unions for variant props instead of optional flags
  that are silently mutually exclusive.
- **No business logic in JSX.** Extract pure functions into a module
  that can be unit-tested without rendering.

## State management

- **Local state first.** `useState` and `useReducer` cover most needs.
  Do not reach for a global store until two unrelated components
  genuinely share the same state.
- **Server state is not client state.** Data fetched from an API is
  managed by a server-state library (TanStack Query, SWR, RTK Query)
  that handles caching, revalidation, and request deduplication. Do not
  hand-roll `useEffect` + `useState` fetching for anything non-trivial.
- **Global client state only when needed.** Pick one: **React Context**
  for small, read-heavy config (theme, current user); **Zustand** for
  lightweight app state; **Redux Toolkit** for complex state with strict
  action logs. Do not combine two global stores in the same app.
- **No prop drilling past ~3 levels.** Lift state to context or a
  store; do not keep threading props.
- **Derived state is computed, not stored.** If `B` is always a function
  of `A`, do not store `B`. Stale derived state is a common bug source.

## Routing and code-splitting

- **Route-based code splitting is the default.** Each top-level route
  is a separate chunk. In Next.js this is automatic; in Vite + React
  use `React.lazy` with `Suspense` per route.
- **Lazy-load heavy routes and components.** Admin panels, rich-text
  editors, charting libraries, and map components are loaded on demand,
  not in the initial bundle.
- **Preload what the user is about to need.** Prefetch the next route
  on hover or visible link; do not wait for the click.
- **One routing library per app.** Next's router, React Router, or
  TanStack Router — pick one.
- **Route params and query strings are typed.** Do not parse
  `window.location.search` ad hoc inside components.

## API client patterns

- **One typed API client per backend.** Generated from an OpenAPI
  schema where possible, or hand-written with shared request/response
  types. Do not sprinkle raw `fetch` calls across components.
- **Centralized error handling.** The client maps HTTP errors to a
  discriminated union (`{ ok: true, data } | { ok: false, error }`) or
  throws typed errors caught by a single boundary. User-visible error
  messages are mapped in one place.
- **Request cancellation.** Every request supports cancellation via
  `AbortSignal`. Components cancel in-flight requests on unmount and on
  dependency change; server-state libraries do this by default.
- **Auth tokens are attached by the client**, not by each caller. One
  interceptor adds `Authorization`; one handles 401 refresh-or-redirect.
- **Retries are intentional.** Idempotent GETs may retry with backoff;
  POSTs do not retry automatically without a server-side idempotency
  key.
- **Base URL is configured per environment**, not hardcoded. Use
  placeholders (`https://api.example.com`, `REPLACE_ME`) in committed
  config.

## Form handling

- **Controlled components for anything non-trivial.** A form library
  (React Hook Form, Formik, TanStack Form) manages state, validation,
  and submission. Do not roll your own for forms over ~3 fields.
- **Client validation mirrors the server schema.** Share the schema
  (Zod, Yup, or generated from OpenAPI) between client validation and
  the types the API client uses. A field valid on the client that the
  server rejects is a finding.
- **Disable submit while pending.** Every submit button disables during
  an in-flight request. Double submissions must be impossible from the
  UI.
- **Server errors map to field errors.** A 422 with field-level errors
  renders next to the offending input, not as a toast.
- **Never trust client validation alone.** Client validation is UX; the
  server revalidates everything.

## Styling

- **Pick one styling approach per project.** CSS Modules, a CSS-in-JS
  library (Emotion, styled-components), or a utility-first framework
  (Tailwind). Do not mix two in the same app.
- **Design tokens live in one place.** Colors, spacing, typography, and
  breakpoints are defined once (CSS variables, a theme object, or a
  Tailwind config) and referenced everywhere. No hex codes scattered
  across components.
- **No inline styles for anything reusable.** Inline styles are
  acceptable for one-off dynamic values; anything themable belongs in
  the styling system.
- **Dark mode and high-contrast** are considered from the start, not
  retrofitted. Use tokens that can flip, not hardcoded colors.
- **CSS resets are explicit.** Ship one reset (for example,
  `modern-normalize` or Tailwind's preflight). Do not stack two.

## Asset handling

- **Static assets are imported, not referenced by string path**, so the
  bundler can fingerprint them for long-term caching.
- **Images are optimized at build time.** Use the framework's image
  component (Next `Image`, equivalent Vite plugins) for responsive
  sizes, lazy loading, and modern formats (AVIF, WebP with fallbacks).
- **SVGs are inlined as components** when they need styling or ARIA;
  referenced as `<img>` when they are purely decorative.
- **Fonts are self-hosted or loaded from a single provider.** Declare
  `font-display: swap` so text is never invisible waiting for a font.
  Subset fonts to the characters actually used.
- **No unoptimized media in the repo.** Large images, videos, and PDFs
  live in object storage (`https://assets.example.com/REPLACE_ME`), not
  in `git`.

## Accessibility

Accessibility is a baseline, not a feature. Target **WCAG 2.1 AA**.

- **Semantic HTML first.** Use `<button>`, `<a>`, `<nav>`, `<main>`,
  `<header>`, `<label>`. A `<div onClick>` that should have been a
  `<button>` is a finding.
- **Keyboard navigation works.** Every interactive element is reachable
  via Tab, activatable via Enter/Space, and has a visible focus
  indicator. Custom focus styles may replace the default — they may not
  remove it.
- **ARIA where needed, not where duplicative.** `role="button"` on a
  `<button>` is noise. Reach for ARIA for patterns HTML does not
  express (combobox, tablist, live regions).
- **Every form control has a label** associated via `for`/`id` or
  wrapping. Placeholders are not labels.
- **Images have `alt` text.** Decorative images use `alt=""` explicitly;
  omitting the attribute is a finding.
- **Color contrast meets AA.** 4.5:1 for normal text, 3:1 for large
  text and UI components. Verify with an automated tool in CI.
- **Automated a11y checks run in CI** (axe-core via Playwright,
  `jest-axe`, or `vitest-axe`). Full WCAG conformance still requires
  manual testing with assistive technologies and expert review.
- **Motion is respected.** Honor `prefers-reduced-motion`; do not
  auto-play animations that cannot be paused.

## Performance budget

- **Core Web Vitals targets** (mobile, 75th percentile): LCP < 2.5s,
  INP < 200ms, CLS < 0.1. A release that regresses any of these past
  the threshold is blocked until fixed.
- **Initial JS bundle budget.** Target < 170 KB gzipped for the
  landing route's JS; fail the build when a route's initial JS exceeds
  the agreed cap.
- **No unused large dependencies.** Audit with `source-map-explorer`
  or equivalent before shipping. Replace heavyweight libs (moment,
  lodash-full) with lighter alternatives (date-fns, per-function lodash
  imports) or native APIs.
- **Third-party scripts are justified and lazy.** Analytics, chat
  widgets, and A/B tools load after interactive, not before. Each added
  third-party script has a documented owner.
- **Images are sized.** Every `<img>` has `width` and `height` (or
  `aspect-ratio`) to prevent CLS. Above-the-fold images are
  `fetchpriority="high"`; below-the-fold are `loading="lazy"`.
- **Caching headers are set** on static assets for long-term immutable
  caching (fingerprinted filenames) and on HTML for short revalidation
  windows.

## Testing

- **Unit tests with Vitest or Jest.** Pure functions, hooks, and
  reducers have unit tests. Vitest for Vite projects; Jest for Next.js
  where already configured. Pick one per project.
- **Component tests with React Testing Library.** Test behavior from
  the user's perspective — queries by role and label, not by class
  name or test ID unless nothing else works. A test that breaks on a
  CSS refactor is testing the wrong thing.
- **E2E tests with Playwright.** Cover critical user journeys (sign-in,
  checkout, primary create/read flows) against a real build. Playwright
  runs in CI on every PR.
- **Accessibility assertions are part of the suite.** Run axe-core in
  at least one component test per page-level component and in every
  Playwright E2E.
- **No snapshot tests for large component trees.** Snapshots go stale
  and get blindly updated. Acceptable only for small, stable output (a
  formatted date string, a serialized error).
- **Mock the network at the boundary.** Use MSW (Mock Service Worker)
  so tests exercise the real API client and real components against
  controlled responses. Do not mock individual `fetch` calls inside
  components.
