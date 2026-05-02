---
inclusion: always
---

# AWS serverless application standards

Application-level conventions for workloads built on Lambda, API Gateway,
and the event sources that drive them. These rules cover the **runtime
shape** of a serverless app — function design, packaging, cold starts,
event wiring, error handling, timeouts, observability, and
runtime-specific notes for the two supported runtimes. Account-level,
network, IAM, and service-selection policy live in `core/platforms/aws.md`
and are out of scope here.

## Function design

- **Single responsibility per function.** One function handles one event
  type or one route. A function that branches on `event.source` to do
  three unrelated things is a finding. Split it.
- **Thin handler, separate business logic.** The handler exported to
  Lambda parses the event, calls into a pure function in another module,
  and shapes the response. Business logic lives in modules that can be
  unit-tested without importing `aws-lambda-powertools` or an SDK client.
- **No framework handlers in Lambda.** Do not run Express, Flask, or
  FastAPI inside Lambda as a monolith behind a proxy integration. If the
  workload needs a framework that routes across many paths, it belongs on
  Fargate or EKS, not Lambda.
- **Idempotent by default.** Every function MUST tolerate being invoked
  more than once for the same logical event, because every supported
  event source can redeliver. Use an idempotency key stored in DynamoDB
  or a similar store when the work is not naturally idempotent.

## Packaging and deployment

- **Zip packages are the default.** Use container images only when the
  package exceeds Lambda's zip size limit, or when the runtime needs
  native binaries that the managed runtime does not provide.
- **One package per function.** Do not share a single zip across many
  functions with different entry points. Per-function packaging keeps
  cold-start payloads small and lets each function version independently.
- **Lambda layers are a last resort.** Prefer bundling dependencies into
  the function package. Layers are acceptable for a large shared native
  binary (for example, a custom `ffmpeg`) but not for ordinary
  application dependencies. Layers hide the dependency graph from the
  function's own lockfile and make reproducible builds harder.
- **Pin every dependency.** The function package is built from a lockfile
  (`package-lock.json`, `pnpm-lock.yaml`, `poetry.lock`, or
  `uv.lock`). Unpinned installs in a build step are a finding.
- **Strip dev dependencies and source maps** from the deployed package.
  Ship only what the runtime needs to execute.

## Cold-start mitigation

- **Minimize init-phase work.** Module-level code runs on every cold
  start. Keep it to imports and cheap constants. Do not open database
  connections, fetch secrets, or load large models at import time unless
  the function cannot function without them.
- **Lazy-import heavy dependencies.** A function that only uses `boto3`'s
  `s3` client on a subset of events should import and construct that
  client inside the branch that uses it, not at module top.
- **Reuse SDK clients across invocations.** Construct clients once at
  module scope (or behind a lazy accessor) and let the Lambda runtime
  reuse them across warm invocations in the same execution environment.
- **Right-size the package.** Smaller packages cold-start faster. Audit
  the zip contents periodically and remove vestigial files.
- **Provisioned concurrency is a scalpel, not a default.** Use it only
  for user-facing, latency-sensitive endpoints where cold-start p99 is
  demonstrably a problem. Every function with provisioned concurrency
  MUST have an explicit reason documented in the IaC definition.
- **SnapStart** is acceptable for supported runtimes where it measurably
  helps; it is not a substitute for keeping init-phase work small.

## Event source wiring

- **API Gateway (HTTP API preferred over REST API for new work).**
  Use proxy integration to Lambda, not Lambda's URL directly, unless
  there is a specific reason to skip API Gateway. Validate request
  shapes at the API Gateway layer where possible; never trust the event
  payload in the handler without re-validation.
- **SQS.** Use event source mappings with batch size and batch window
  tuned to the workload. Report partial-batch failures (see below) so
  only the failed records are retried.
- **SNS and EventBridge.** Prefer EventBridge for new event-bus work;
  SNS is acceptable for fan-out to SQS and for simple pub/sub where the
  routing features of EventBridge are not needed. Do not wire both SNS
  and EventBridge for the same event.
- **S3.** Prefer S3 → EventBridge → Lambda over direct S3 notifications
  to Lambda. EventBridge gives filtering, retries, and multiple targets
  without touching S3 configuration.
- **DynamoDB Streams and Kinesis.** Use event source mappings with
  per-shard concurrency tuned to the workload. Report partial-batch
  failures. Checkpointing is implicit in the mapping — do not try to
  manage it in application code.
- **No polling loops.** A Lambda that polls SQS or Kinesis on a timer is
  a finding. Use the managed event source mapping.

## Error handling per event source

- **API Gateway.** The handler returns a structured response; uncaught
  exceptions are mapped to `5xx` by a central error handler in the
  business-logic layer, not scattered across routes. Do not leak stack
  traces to clients.
- **SQS.** Every queue with a Lambda consumer MUST have a dead-letter
  queue configured on the **event source mapping** (not only on the
  source queue). Use partial-batch failure reporting: return
  `batchItemFailures` from the handler so only failed messages are
  retried.
- **SNS.** Configure a DLQ on the **Lambda subscription**. SNS
  deliveries are retried by the service; failures past the retry policy
  land in the subscription DLQ.
- **EventBridge.** Configure a DLQ on the target. Use retry policy
  settings (max attempts, max event age) intentionally; defaults are
  rarely what the workload wants.
- **S3 via EventBridge.** Follow the EventBridge rules above. Direct S3
  notifications do not support DLQs for Lambda targets — another reason
  to route through EventBridge.
- **DynamoDB Streams and Kinesis.** Report partial-batch failures via
  `batchItemFailures`. Configure an on-failure destination (SQS or SNS)
  on the event source mapping so records that exceed `MaximumRetryAttempts`
  or `MaximumRecordAgeInSeconds` are captured, not silently dropped.
- **Never swallow errors to make retries stop.** If a message cannot be
  processed, let it fail and land in the DLQ. A handler that catches
  everything and returns success hides real failures.

## Timeouts and memory sizing

- **Set timeouts intentionally.** The default of 3 seconds is wrong for
  most workloads. Pick a timeout based on the work the function actually
  does, plus headroom. A synchronous API handler behind API Gateway MUST
  have a timeout less than API Gateway's own 29-second integration
  timeout.
- **Set memory intentionally.** Memory controls CPU on Lambda. Start
  with a realistic value for the workload (often 512–1024 MB for I/O
  work, higher for CPU-bound work) and tune with AWS Lambda Power
  Tuning. Do not ship a function at 128 MB because that is the
  minimum.
- **Timeouts on downstream clients are shorter than the function
  timeout.** An SDK call that can outlast the function timeout will get
  killed mid-flight and leak connections. Configure client-side
  connect/read timeouts explicitly.

## Observability per function

- **Structured JSON logs.** Every log line is a single JSON object with
  at minimum `level`, `message`, `service-name`, `function-name`,
  `request-id`, and any business identifiers (for example,
  `order-id`). No `print`/`console.log` of free-form strings in
  production code.
- **No secrets or PII in logs.** Scrub request bodies and headers that
  may carry tokens, session cookies, or personal identifiers before
  logging. Logs are a compliance surface.
- **X-Ray tracing enabled** on every function unless there is a
  specific reason not to. Propagate the trace header across downstream
  SDK calls and across service boundaries (SNS, SQS, EventBridge, Step
  Functions all carry X-Ray context).
- **Custom metrics via Embedded Metric Format (EMF).** Emit business
  metrics (for example, `orders-processed`, `decode-failures`) from
  logs rather than synchronous `PutMetricData` calls, which add latency
  to the critical path.
- **Per-function log group retention** is set in IaC, not left at
  "Never expire". A reasonable default is 30 days in non-prod and a
  workload-defined retention in prod.

## Node.js 20+ runtime notes

Node.js 20+ is the supported JS/TS backend runtime for Lambda. These
notes cover runtime-shape concerns; language-level TypeScript guidance
lives in `core/languages/typescript.md`.

- **Runtime lifecycle.** The handler module is loaded once per execution
  environment. Top-level `await` runs during init and counts against
  init duration. Keep it to configuration, not work.
- **ES modules.** Prefer ESM (`"type": "module"` in `package.json`,
  `.mjs` or compiled `.js`) for new functions. The runtime supports it
  natively. CommonJS is acceptable for existing code and for packages
  that do not publish ESM entry points.
- **Init hooks.** Use `globalThis` or module-scope caches for
  cross-invocation reuse (SDK clients, config objects). Do not rely on
  `/tmp` for cross-invocation state; it is per-execution-environment
  and will disappear.
- **AWS SDK v3.** Use modular `@aws-sdk/client-*` packages, not the
  bundled `aws-sdk` v2. Bundle the specific clients the function needs;
  do not depend on the runtime-provided SDK.
- **Connection reuse.** Set `AWS_NODEJS_CONNECTION_REUSE_ENABLED=1` (or
  rely on the SDK v3 default) so HTTPS keep-alive is on. A function
  that opens a new TCP connection for every call is a finding.
- **Source maps.** If compiling from TypeScript, ship source maps and
  set `NODE_OPTIONS=--enable-source-maps` so stack traces are useful.

## Python 3.12+ runtime notes

Python 3.12+ is the supported Python runtime for Lambda. These notes
cover runtime-shape concerns; language-level Python guidance lives in
`core/languages/python.md`.

- **Handler signature.** `def handler(event, context):` (or async
  equivalent where used). The handler returns a JSON-serializable value
  for API Gateway integrations and `None` or a partial-batch-failure
  dict for stream/queue integrations.
- **Cold-start considerations.** Python import graphs can dominate cold
  start. Avoid top-level imports of heavy optional dependencies
  (`pandas`, `numpy`, `torch`, large AWS SDK submodules) unless every
  invocation needs them. Import inside the handler branch that uses
  them.
- **`boto3` client reuse.** Construct `boto3` clients at module scope
  so the Lambda runtime reuses them across warm invocations. A client
  created inside the handler on every call is a finding.
- **Packaging.** Build the deployment package from a lockfile
  (`poetry.lock`, `uv.lock`, or a pinned `requirements.txt`). Do not
  run `pip install` against unpinned specifiers in the build step.
  Strip `__pycache__`, tests, and `.dist-info` from the package when
  size matters.
- **Native wheels.** Build wheels for the Lambda execution architecture
  (`x86_64` or `arm64`) explicitly. A wheel built on a developer laptop
  for a different architecture will fail at import time in the runtime.
- **Structured logging.** Use the standard `logging` module configured
  to emit JSON (via `aws-lambda-powertools` or a small custom
  formatter). The root logger's default text format is not acceptable
  for production functions.
