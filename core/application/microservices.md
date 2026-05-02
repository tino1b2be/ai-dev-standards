---
inclusion: always
---

# Event-driven microservices standards

Application-level conventions for event-driven microservices on AWS:
service boundaries, inter-service communication, data ownership,
contracts, async-first patterns, sagas, error handling across
boundaries, discovery, observability, and testing. Scope here is the
**architecture between services**. Lambda packaging, cold-start shape,
and event-source wiring inside a single service live in
`core/application/aws-serverless.md`. Account, IAM, and platform setup
live in `core/platforms/aws.md`.

## Service boundaries

- **One business capability per service.** A service owns a coherent
  piece of the domain (`orders`, `payments`, `inventory`,
  `notifications`). Splitting `orders` into `orders-read` and
  `orders-write` is a finding unless the two have genuinely different
  scaling or security profiles.
- **Services own their data.** Every service has its own DynamoDB
  table, S3 bucket, or database. No other service reads or writes that
  store directly. A second service that needs the data consumes events
  or calls a published API.
- **No shared databases across services.** Two services pointing at
  the same DynamoDB table or RDS instance are the same service wearing
  two uniforms. Either merge them or split the data.
- **Size for change, not lines of code.** A service is the right size
  when a single team can deploy it independently and its failure does
  not cascade to unrelated capabilities.
- **Name services after the capability.** `service-name: orders`, not
  `service-name: order-lambda-stack-v2`. The name shows up in logs,
  metrics, alarms, and event schemas.

## Communication between services

- **EventBridge for domain events.** Publish `OrderPlaced`,
  `PaymentCaptured`, `InventoryReserved` to a shared event bus
  (`arn:aws:events:us-east-1:YOUR_ACCOUNT_ID:event-bus/REPLACE_ME`).
  Consumers subscribe via rules without the publisher knowing they
  exist.
- **SQS for work queues.** Use SQS when one service hands specific
  units of work to another and needs buffering, retry, and DLQ
  semantics. A queue has exactly one logical consumer service.
- **Step Functions for workflows.** Use Step Functions when multiple
  steps across services MUST run in a defined order with explicit
  success, failure, compensation, and timeout behavior. Do not encode
  a multi-step workflow as a chain of Lambda-invokes-Lambda calls.
- **No synchronous service-to-service calls by default.** A Lambda
  from service `A` calling an API Gateway endpoint on service `B`
  couples their availability. If `A` must wait on `B`, justify it in
  the design and accept the coupling explicitly.
- **No service mesh, no shared in-process libraries with business
  logic.** A shared package that encodes `orders` rules is a back-door
  shared database. Share SDK-style utilities (logging, tracing) and
  nothing else.

## Data ownership

- **Each service owns exactly one system of record** for its data.
  Other services hold derived views (read models) built from events.
- **Read models are local.** If `analytics` needs `orders` data, it
  subscribes to `OrderPlaced` events and maintains its own projection,
  not a cross-account query against the `orders` table.
- **No cross-service foreign keys.** A service references another
  service's entities by stable, published IDs only
  (`order-id: REPLACE_ME`), not by internal primary keys that may
  change.
- **Schemas evolve independently.** A column added to the `orders`
  table does not require a migration in any other service. If it does,
  the boundary is wrong.
- **Backups and retention are per-service.** Each service defines its
  own RPO, RTO, and retention.

## Contract stability

- **Every published event has a schema**, stored in EventBridge Schema
  Registry or an equivalent versioned location. Consumers generate
  types from the schema; nobody hand-codes event shapes.
- **Event names are versioned**, not the payload. Prefer
  `OrderPlaced.v1`, `OrderPlaced.v2` over a `version` field that
  consumers must branch on. New consumers subscribe to `v2`; `v1` is
  published until consumers migrate.
- **Backwards-compatible changes only** within a version: add optional
  fields, never remove or retype required ones. A breaking change is a
  new version.
- **Published APIs follow the same rule.** REST/HTTP contracts follow
  `core/steering/api-standards.md` and are versioned. Internal-only
  HTTP endpoints do not exist — if another service calls it, it is
  published.
- **Consumer-driven contract tests.** Each consumer publishes a
  contract (Pact or equivalent) describing the event or response shape
  it depends on. Producer CI verifies every consumer contract before
  release. A producer change that breaks a consumer contract blocks
  the build.
- **Deprecate loudly.** Retiring an event version starts with a
  deprecation notice in the schema, a metric on remaining consumers,
  and a published cutoff date.

## Async-first patterns

- **Commands, events, state.** A client sends a command
  (`PlaceOrder`); the owning service validates and accepts it
  synchronously, writes state, and publishes an event
  (`OrderPlaced`). Downstream effects happen from the event, not from
  the command path.
- **Accept-and-acknowledge, don't block.** A command endpoint returns
  `202 Accepted` with a resource identifier the client can poll or
  subscribe to. It does not synchronously wait for downstream services
  to finish.
- **Eventual consistency is the default.** Design UX and internal
  flows so a short window between "command accepted" and "state
  visible everywhere" is normal, not an incident.
- **Idempotency keys on commands.** Every command carries a
  client-supplied idempotency key. The accepting service stores the
  key and returns the same result on retry.
- **No distributed transactions.** No two-phase commit, no XA across
  services. Consistency across services is achieved with sagas, not
  locks.

## Saga patterns

Distributed workflows with multiple steps across services use one of
two patterns. Pick one per workflow; do not mix.

- **Orchestration via Step Functions.** A state machine drives the
  workflow: invoke service `A`, wait for result, invoke `B`, on
  failure invoke `A`'s compensation. Use this when the workflow is
  complex, needs explicit timeouts, or has clear recovery steps.
  Orchestration makes the flow visible and auditable in one place.
- **Choreography via events.** Each service reacts to events from
  others and publishes its own. `payments` sees `OrderPlaced`, charges
  the card, publishes `PaymentCaptured`. `inventory` sees
  `PaymentCaptured`, reserves stock, publishes `InventoryReserved`.
  Use this when coupling MUST be low and the flow is naturally linear.
- **Compensating actions are explicit.** Every forward step has a
  documented compensation: `ChargeCard` → `RefundCard`,
  `ReserveStock` → `ReleaseStock`.
- **Saga state is owned by one service.** The orchestrator (Step
  Functions execution) or a dedicated saga-tracker owns the workflow's
  state. No service infers saga progress by querying others.

## Error handling across boundaries

- **Retries with exponential backoff and jitter** on every async hop.
  Rely on the managed service (SQS redrive, EventBridge retry policy,
  Step Functions `Retry`) rather than custom retry logic.
- **Dead-letter queues on every async target.** SQS consumers, SNS
  subscriptions, EventBridge targets, Step Functions tasks — every
  one has a DLQ with an alarm on depth > 0.
- **At-least-once delivery, plan for duplicates.** Every event
  consumer is idempotent. Store processed event IDs in DynamoDB with
  a TTL matching the source's retention window, or derive idempotency
  from the business state (`order.status == 'paid'` already).
- **Poison messages go to a DLQ, not a retry loop.** A consumer that
  crashes on a malformed event MUST fail fast so the message lands in
  the DLQ after the configured retries. Swallowing the error to "keep
  moving" hides bugs.
- **Timeouts are shorter than the caller's timeout.** A synchronous
  call from `A` to `B` has a client-side timeout strictly less than
  `A`'s own timeout, so `A` never gets killed mid-call leaking
  connections.
- **Circuit breakers on synchronous calls.** If `A` must call `B`
  synchronously, `A` trips a breaker after a threshold of failures
  and returns a degraded response rather than amplifying the outage.

## Service discovery

- **EventBridge event buses are the discovery mechanism for events.**
  A shared bus per environment
  (`arn:aws:events:us-east-1:YOUR_ACCOUNT_ID:event-bus/REPLACE_ME`);
  consumers subscribe by rule pattern. Publishers do not know who
  listens.
- **SNS topics for simple fan-out** where EventBridge's routing is
  not needed. Publishers know the topic ARN; subscribers attach.
- **Synchronous endpoints are discovered via a registry**, not
  hardcoded hostnames. Use AWS Cloud Map, Parameter Store entries
  (`/services/REPLACE_ME/endpoint`), or a published OpenAPI index.
  Hardcoded URLs in deployed code are a finding.
- **Environment-per-account, not environment-in-name.** The `orders`
  service is the same logical service in dev and prod; its discovery
  name does not change. Use the account boundary for separation.

## Observability across services

- **Correlation IDs propagate through every event and call.** A
  request entering at the edge gets a `correlation-id` (a ULID or
  UUID); every subsequent event, SQS message, Step Functions execution
  input, and downstream HTTP call carries it in headers and payload.
- **Standard envelope attributes.** Put `correlation-id`,
  `causation-id` (the immediate parent event's ID), and `trace-id` in
  every event envelope. Do not invent per-service header names.
- **Distributed tracing with X-Ray or OpenTelemetry.** A trace spans
  the whole workflow — API Gateway through Lambda through EventBridge
  through the next Lambda. A trace that stops at a service boundary
  is a finding; propagate the trace context explicitly across async
  hops.
- **Structured JSON logs per service, aggregated centrally.** Every
  log line includes `service-name`, `correlation-id`, and
  `request-id`.
- **Cross-service SLOs, not just per-service metrics.** Define
  success for the end-to-end workflow ("95% of `PlaceOrder` commands
  result in `OrderFulfilled` within 10 minutes"), not only for each
  service's p99.
- **Alarms on async depth and age.** DLQ depth > 0, SQS oldest
  message age over threshold, EventBridge rule failed-invocation
  count > 0 — these are the cross-service early-warning signals.

## Testing strategy

- **Unit tests inside each service.** Pure business logic is
  unit-tested without any AWS dependency. A service whose unit tests
  need LocalStack or live AWS to pass has too much logic in its
  adapters.
- **Contract tests at every boundary.** Each consumer publishes a
  contract for every event or API it depends on. Producer CI runs
  every published consumer contract. A producer release is blocked by
  a broken contract, not by a failing integration detected days later.
- **Integration tests against real AWS in ephemeral environments.**
  Spin up a per-PR or per-branch environment in a sandbox account
  (`account-id: YOUR_ACCOUNT_ID`) with the service and its real
  dependencies (EventBridge bus, SQS queues, DynamoDB tables),
  exercise the workflow end-to-end, tear down after. LocalStack is
  acceptable for developer-loop speed, not for the pre-merge gate.
- **Test the saga, not just the steps.** End-to-end tests of
  orchestrated or choreographed flows verify compensation paths too:
  force `payments` to fail and assert the order ends up cancelled
  with the right events and state.
- **Chaos and failure injection** on critical workflows: drop a
  consumer, delay a step, inject a DLQ entry. If the workflow cannot
  survive one downstream service being slow or temporarily absent,
  the design is wrong — fix it before production.
- **Do not mock AWS to make tests pass.** A mocked SQS that never
  redelivers, never duplicates, and never fails is testing a universe
  you do not deploy into. Use real services or well-known fakes
  (LocalStack for dev, real AWS for CI).
