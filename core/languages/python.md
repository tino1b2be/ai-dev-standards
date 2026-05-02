---
inclusion: always
---

# Python language standards

Language-level conventions for Python code in the target stacks. Scope
here is the **language**: version, typing, style, imports, dependencies,
error handling, logging, standard-library preferences, async patterns,
testing, and docstrings. Runtime-shape concerns — Lambda packaging,
cold-start behavior, handler wiring, `boto3` client lifetime — live in
`core/application/aws-serverless.md`, not here.

## Version

- **Python 3.12+ is the baseline.** New projects target 3.12 or newer.
  Code that depends on 3.11-or-older behavior is a finding.
- **Pin the interpreter explicitly.** `pyproject.toml` declares
  `requires-python = ">=3.12"`. CI runs the same interpreter version
  that production runs.
- **No `from __future__ import` shims** for features already present
  in 3.12. If the codebase still carries them, remove during touch.

## Type hints

- **Type hints are required on every public interface.** Module-level
  functions, class methods, and class attributes that cross a module
  boundary all carry annotations. Private helpers inside a single file
  may omit them when they add no signal.
- **Run a strict type checker in CI.** `mypy --strict` or `pyright` in
  strict mode. Type errors block the build. `# type: ignore` requires
  a reason comment and is itself a finding when used to paper over a
  real bug.
- **Prefer modern builtin generics** (`list[int]`, `dict[str, Foo]`,
  `X | None`) over `typing.List`, `typing.Dict`, and
  `typing.Optional`. `from __future__ import annotations` is not
  needed on 3.12+.
- **`Any` is a last resort.** When a value is genuinely untyped
  (external JSON at a boundary), use `object` or a `TypedDict`/Pydantic
  model and narrow explicitly. A function that returns `Any` leaks the
  hole to every caller.
- **Protocols over inheritance for structural typing.** Define
  `typing.Protocol` interfaces for collaborators rather than abstract
  base classes when the relationship is "quacks like".

## Code style

- **PEP 8, enforced by a formatter.** Use `ruff format` (preferred) or
  `black`. The formatter is the style guide; do not argue about
  whitespace in review.
- **`ruff` is the linter.** Run `ruff check` in CI with a shared config
  in `pyproject.toml`. Autofix what `ruff` can autofix; fix the rest
  by hand. Disabling a rule requires a reason comment.
- **Line length: 100.** Wider than stock PEP 8's 79 but narrower than
  letting lines sprawl. The formatter enforces it.
- **Naming.** `snake_case` for functions, variables, and module names;
  `PascalCase` for classes; `UPPER_SNAKE_CASE` for module-level
  constants. A single leading underscore marks module-private; do not
  use double leading underscores except for real name-mangling needs.
- **No wildcard imports** (`from foo import *`). A wildcard import is
  a finding.

## Import organization

- **Three groups, separated by one blank line**, in order: standard
  library, third-party, local. `ruff` (or `isort`) enforces this.
- **Absolute imports for code in the project package.** Relative
  imports (`from .sibling import x`) are acceptable within a package
  but not across package boundaries.
- **Import at the top of the module.** Import inside a function only
  when there is a specific reason (avoiding a cycle, deferring an
  optional heavy dependency) and document the reason in a comment.

## Dependency management

- **Lockfiles are required.** Use `uv` (preferred for new projects),
  `poetry`, or `pip-tools`. The lockfile (`uv.lock`, `poetry.lock`, or
  a pinned `requirements.txt` produced by `pip-compile`) is committed.
  A repo without a lockfile is a finding.
- **Pin direct and transitive dependencies** to exact versions in the
  lockfile. Version ranges belong in `pyproject.toml`; the lockfile
  resolves them to exact versions.
- **Separate runtime and dev dependencies.** Test tools, linters, and
  type checkers are dev dependencies and never ship in a deployment
  artifact.
- **Review before adding.** A new dependency needs a maintained
  upstream, a compatible license, and a clear reason the standard
  library or an existing dependency does not cover the need.
- **Upgrade on a schedule.** Stale lockfiles rot. Run
  `uv lock --upgrade` or equivalent at least monthly and treat the
  diff as a reviewable change.

## Error handling

- **Raise exceptions, do not return sentinels.** A function that
  returns `None` or `-1` on failure forces every caller to branch on
  magic values. Raise and let the caller handle it.
- **Narrow `except` clauses.** `except Exception:` and bare `except:`
  are findings except in a top-level crash-handler that logs and
  re-raises. Catch the specific exception the code actually expects.
- **Custom exception classes for domain errors.** Define a module-level
  base (`class OrdersError(Exception): ...`) and specific subclasses
  (`OrderNotFoundError`, `OrderAlreadyPaidError`). Callers catch the
  base when they want "any domain error" and the subclass when they
  need to branch.
- **Never swallow exceptions.** `except SomeError: pass` without a
  comment explaining why the error is safe to ignore is a finding.
- **Preserve tracebacks.** When re-raising with context, use
  `raise NewError(...) from exc`, not `raise NewError(...)`. The
  chained cause is part of the error.
- **Validate at the boundary.** Parse incoming data (HTTP bodies,
  event payloads, config files) into typed models (`dataclass`,
  `TypedDict`, or Pydantic) at the edge. Inside the service, trust
  the types.

## Logging

- **Use the `logging` module.** `print` in production code is a
  finding. `print` is acceptable only in `__main__` of a CLI script
  where stdout is the intended output channel.
- **One logger per module**, obtained as
  `logger = logging.getLogger(__name__)`. Do not use the root logger
  directly.
- **Structured JSON logs.** Configure a JSON formatter
  (`python-json-logger` or a small custom formatter) so each log line
  is a single JSON object with `level`, `message`, `logger`, and any
  business fields.
- **No secrets or PII in logs.** Request bodies, auth headers, and
  user identifiers are scrubbed before logging. Logs are a compliance
  surface.
- **`logger.exception` inside `except`**, not `logger.error` with a
  manual `traceback.format_exc()`. `exception` captures the active
  traceback automatically.

## Standard-library preferences

- **`pathlib.Path` over `os.path`.** File paths are `Path` objects
  end-to-end. `os.path.join(a, b)` is a finding when `Path(a) / b`
  works.
- **`dataclasses` (or Pydantic at boundaries) over ad-hoc dicts.** A
  function that takes `dict[str, Any]` and reads six specific keys
  should take a `@dataclass` instead. Typed structures survive
  refactors; dicts do not.
- **`enum.Enum` (or `enum.StrEnum`) over magic strings.** Status
  values, kinds, and modes are enums. A function parameter typed
  `Literal["open", "closed"]` is acceptable for a tiny closed set;
  anything larger is an enum.
- **`datetime` with explicit `tzinfo`.** Naive datetimes are a
  finding. Use `datetime.now(tz=datetime.UTC)` on 3.12+.
- **`functools.cache` / `functools.lru_cache`** for memoization;
  do not hand-roll dict caches.

## Async and await

- **Async when the workload is I/O-bound and concurrent.** Calling many
  HTTP endpoints in parallel or fanning out to many downstream services
  are legitimate async use cases. CPU-bound code is not.
- **Do not mix sync and async in the same call path.** Calling
  `asyncio.run()` inside a sync function that is itself called from
  an event loop is a finding. Pick one model per entry point.
- **Never block the event loop.** No `time.sleep`, no synchronous
  network libraries (`requests`) inside a coroutine. Use `asyncio.sleep`
  and async clients (`httpx.AsyncClient` or equivalent).
- **Cancel cleanly.** A coroutine that acquires resources uses
  `async with` or a `try/finally` so cancellation does not leak
  connections.

## Testing

- **`pytest` is the test runner.** `unittest` is acceptable for
  existing code but not for new tests.
- **Test files mirror source layout** under `tests/`, with filenames
  `test_<module>.py` and test functions named `test_<behavior>`.
- **Fixtures over setup/teardown boilerplate.** Use `pytest` fixtures
  (function-, class-, module-, or session-scoped) for shared setup.
  A fixture that silently swallows errors during teardown is a
  finding.
- **Parametrize repetition.** `@pytest.mark.parametrize` over copy-
  pasted test bodies.
- **No network or filesystem access in unit tests** beyond `tmp_path`.
  Integration tests that need a real service live in a separate
  directory and run on a separate CI job.
- **Deterministic tests.** No wall-clock dependencies, no random seeds
  without a fixed value, no order-dependent tests.

## Docstrings

- **Public functions, classes, and modules carry docstrings.** A
  module-private helper with an obvious name and signature may skip
  one.
- **Google or NumPy style, chosen per repo and consistent.** Pick one
  in `pyproject.toml`'s `ruff` or `pydocstyle` config and do not mix.
- **Summary line, then body.** First line is a short imperative
  summary ("Return the order total."); optional body describes
  arguments, returns, and raises.
- **Types live in annotations, not docstrings.** Do not duplicate
  type information in the docstring; the annotation is the source of
  truth.
