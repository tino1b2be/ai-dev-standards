---
inclusion: always
---

# TypeScript language standards

Language-level conventions for TypeScript code in the target stacks. Scope
here is the **language**: compiler settings, typing discipline, module
system, style, naming, error handling, null/undefined handling, interface
vs. type, generics, dependencies, and testing. Runtime-shape concerns —
Node.js version targeting, Lambda packaging, event-loop behavior, module
resolution on disk, `npm` registry behavior — live in
`core/application/aws-serverless.md` or `core/platforms/*.md`, not here.

## Strict mode

- **`strict: true` in `tsconfig.json` is the baseline.** The `strict`
  flag is non-negotiable for new projects and a finding when absent in
  an existing one. It bundles the individual strict flags; do not
  cherry-pick a subset.
- **Additional safety flags are on.** Enable
  `noUncheckedIndexedAccess`, `noImplicitOverride`,
  `noFallthroughCasesInSwitch`, and `exactOptionalPropertyTypes`.
  These catch real bugs that base `strict` does not.
- **`skipLibCheck: true` is acceptable** for build performance as long
  as the project's own code type-checks cleanly. It is not a license
  to ship broken types.
- **Type errors block the build.** `tsc --noEmit` runs in CI and a
  non-zero exit fails the pipeline. Comments that suppress errors
  (`// @ts-ignore`, `// @ts-expect-error`) require a reason and are
  themselves reviewable.

## Type safety

- **`any` is banned by default.** `@typescript-eslint/no-explicit-any`
  is on as an error. When a value is genuinely unknown (external JSON,
  dynamic message payload), use `unknown` and narrow with a type guard
  or a schema parser before using it.
- **`unknown` at every boundary.** HTTP bodies, queue messages, config
  files, and third-party callback payloads enter the program as
  `unknown` and are validated into a typed shape (Zod, Valibot, a
  hand-written guard) at the edge. Inside the service, trust the
  types.
- **Discriminated unions for variant data.** A value that can be one
  of several shapes is a union with a literal discriminator
  (`type Result = { kind: "ok"; value: T } | { kind: "err"; error: E }`),
  not an object with optional fields that callers have to branch on.
- **No non-null assertions to paper over holes.** `value!` is a
  finding except at a boundary where the invariant is documented in a
  comment. Prefer a guard or an explicit `throw` with a clear message.
- **Avoid type assertions to coerce shapes.** `value as Foo` lies to
  the compiler; use `satisfies` for structural checks and a real
  validator for data coming from outside the program.

## Module system

- **ES modules, not CommonJS.** `package.json` sets
  `"type": "module"`; imports and exports use ESM syntax. Projects
  that must emit CJS for a specific consumer do so from a build step,
  not by authoring in CJS.
- **`.ts` for runtime code, `.tsx` for React components.** No `.js`
  source files in a TypeScript project except in explicitly-marked
  interop shims.
- **`import type` for type-only imports.** An import used purely for
  its types uses `import type { Foo } from "./foo";` so bundlers can
  drop it cleanly. `verbatimModuleSyntax: true` in `tsconfig.json`
  enforces this at the compiler.
- **Explicit file extensions in import specifiers** when the project
  targets native ESM (`import { x } from "./foo.js";`). The extension
  is `.js` in the specifier even though the source is `.ts`; this is
  the ESM rule, not a quirk of the project.
- **No wildcard re-exports at package boundaries.** `export * from
  "./internal"` leaks internals. Name every export on the boundary.

## Code style

- **Prettier is the formatter.** Formatting is not a discussion.
  Prettier runs in CI and a diff fails the build. Shared config lives
  in the repo (`.prettierrc` or in `package.json`).
- **ESLint with `@typescript-eslint` is the linter.** Use the
  recommended type-checked configs (`strict-type-checked` and
  `stylistic-type-checked`). Rule suppressions
  (`// eslint-disable-next-line ...`) carry a reason comment.
- **Line length: 100.** Matches the Python standard in this repo and
  leaves room for typed signatures without wrapping every line.
- **Semicolons and double quotes** (or whatever the Prettier config
  sets). Pick once per repo, commit the config, stop discussing it.

## Naming conventions

- **`PascalCase` for types, interfaces, classes, enums, and type
  parameters** (`UserId`, `OrderRepository`, `T`, `TItem`). Type
  parameters are short (`T`, `K`, `V`) when generic, descriptive
  (`TItem`, `TError`) when the role is not obvious.
- **`camelCase` for functions, methods, variables, and object
  properties** (`getUserById`, `orderTotal`).
- **`UPPER_SNAKE_CASE` for module-level constants** that are true
  compile-time constants (`const MAX_RETRIES = 3`). Mutable module
  state — if it exists at all — uses `camelCase`.
- **No Hungarian prefixes.** `IUser` for interfaces and `TOptions`
  for type aliases are findings. The compiler knows the kind; the
  reader does not need a prefix.
- **File names are `kebab-case.ts`** (`user-repository.ts`) except
  for React component files which may be `PascalCase.tsx` when the
  repo convention calls for it. Pick one style per repo.

## Error handling

- **Throw `Error` subclasses, never strings or objects.** `throw
  "not found"` and `throw { code: 404 }` are findings. The thrown
  value is typed `unknown` in a `catch`; starting from an `Error`
  gives it a stack and a message.
- **Define domain error classes.** A module that can fail in
  well-known ways defines a base (`class OrderError extends Error`)
  and subclasses (`OrderNotFoundError`, `OrderAlreadyPaidError`).
  Callers branch on `instanceof`, not on string-matching a message.
- **`catch (err)` is typed `unknown`.** Narrow before using: check
  `err instanceof Error` or validate the shape. Reading `err.message`
  without a guard is a finding.
- **`Result<T, E>` is the right tool for expected failures.** For
  operations whose failure is part of the domain (parsing input,
  looking up an optional record), return
  `{ kind: "ok"; value: T } | { kind: "err"; error: E }` instead of
  throwing. Reserve `throw` for invariant violations and unexpected
  failures.
- **Never swallow rejections.** Every `Promise` is `await`ed, chained,
  or explicitly handed to a supervisor (`void promise` is a finding
  without a comment). Unhandled rejections are bugs, not warnings.
- **Preserve the cause.** When wrapping an error, use
  `new WrappedError("context", { cause: err })` so the original stack
  is retained.

## Null and undefined

- **`strictNullChecks` is on** (implied by `strict: true`). A value
  that can be absent is typed `T | undefined` or `T | null`, not
  "usually `T`".
- **Pick one: `undefined` for absence, `null` for explicit absence.**
  The idiomatic TypeScript choice is `undefined`; use `null` only
  when an external contract (JSON API, database driver) demands it.
  Mixing both in the same codebase is a finding.
- **Optional chaining and nullish coalescing.** `user?.address?.city`
  and `value ?? defaultValue` over hand-written guards. Do not use
  `||` for default values when the falsy set includes legitimate
  values (`0`, `""`, `false`).
- **`noUncheckedIndexedAccess` is on.** `array[0]` is typed
  `T | undefined`. Handle the absence explicitly.

## Interface vs type alias

- **`type` for simple aliases, unions, intersections, and mapped
  types.** `type UserId = string;`, `type Status = "open" | "closed";`,
  `type Partial<T> = { [K in keyof T]?: T[K] };`.
- **`interface` for extensible object shapes** that callers or
  subclasses are expected to extend, and for public API surfaces
  that benefit from declaration merging.
- **Do not mix both for the same shape.** Pick one per exported
  symbol and stay with it. A shape that starts as `type` and later
  needs extension becomes an `interface`; update the callers and
  move on.
- **No empty interfaces.** `interface Foo extends Bar {}` is a
  finding; use `type Foo = Bar` or delete the alias.

## Generics

- **Use generics when the type relationship is real.** A function
  that takes `T` and returns `T` earns its generic. A function that
  takes `T` and returns `unknown` does not.
- **Constrain with `extends`.** `function f<T extends { id: string }>(x: T)`
  is more useful than `function f<T>(x: T)` when the body reads `x.id`.
- **Avoid over-abstraction.** Three call sites is usually not enough
  to justify a generic helper. Duplicate first; abstract when the
  third call site forces the issue.
- **Default type parameters when the common case is obvious.**
  `function query<T = unknown>(sql: string): Promise<T[]>` is kinder
  to callers than forcing every site to specify `T`.

## Dependency management

- **One package manager per repo.** Pick `pnpm` (preferred for new
  projects), `npm`, or `yarn` and commit only that manager's
  lockfile. A repo with two lockfiles is a finding.
- **Lockfile committed.** `pnpm-lock.yaml`, `package-lock.json`, or
  `yarn.lock` is tracked. A repo without a lockfile is a finding.
- **Pinned versions.** `package.json` uses exact versions (`"zod":
  "3.23.8"`) or tight ranges (`"~3.23.8"`). Broad ranges (`"^3"`,
  `"*"`, `"latest"`) are findings.
- **Separate `dependencies` and `devDependencies`.** Test tools,
  linters, type checkers, and build tools are `devDependencies` and
  never ship in a deployment artifact.
- **Review before adding.** A new dependency needs a maintained
  upstream, a compatible license, and a clear reason the standard
  library, an existing dependency, or a 20-line helper does not
  cover the need.
- **Upgrade on a schedule.** Run `pnpm update --latest` (or
  equivalent) at least monthly and treat the diff as a reviewable
  change.

## Testing

- **Vitest (preferred for new projects) or Jest.** Pick one per repo.
  Vitest's ESM-native behavior matches the module stance above; Jest
  is acceptable for existing code.
- **Test files live next to source as `<name>.test.ts`** or in a
  parallel `tests/` tree mirroring the source layout. Pick one per
  repo and stay with it.
- **Test names describe behavior.** `it("returns the order total")`
  and `it("throws OrderNotFoundError when the id is unknown")`, not
  `it("works")`.
- **No network or filesystem access in unit tests** beyond a
  per-test temp directory. Integration tests that need a real
  service live in a separate suite and run on a separate CI job.
- **Deterministic tests.** No wall-clock dependencies, no
  unseeded randomness, no order-dependent tests.
- **Type-level tests when the types are the product.** For library
  code whose correctness is in its types, add `expectTypeOf` (Vitest)
  or `tsd` assertions alongside runtime tests.
