# API standards

Conventions for HTTP APIs. These rules apply to any API the project exposes,
regardless of backing stack (Lambda + API Gateway, a containerized service,
a framework on a VM). They are tool-neutral and prescriptive — follow them
exactly. Security, repo layout, and CI/CD live in their own files; do not
restate them here.

## Resource naming and URL structure

- URLs name **resources**, not actions. Use **nouns**, not verbs.
  `GET /orders/{order_id}` is correct. `GET /getOrder?id=...` is not.
- Collections are **plural**: `/users`, `/orders`, `/invoices`. Never mix
  plural and singular forms for the same resource.
- Multi-word path segments use **kebab-case**: `/payment-methods`,
  `/api-keys`. No camelCase, snake_case, or spaces in paths.
- Nest paths only to express ownership, not to encode behavior. One level
  of nesting is the norm: `/orders/{order_id}/items`. Deeper nesting is a
  smell — expose the inner resource at its own top-level path instead.
- Resource identifiers in the path are opaque to clients. Do not leak
  internal database shapes (auto-increment IDs, internal UUID formats)
  as part of the contract unless the API deliberately exposes them.
- Actions that do not fit REST semantics (for example, "reprocess this
  invoice") are modeled as a sub-resource representing the action's
  result: `POST /invoices/{invoice_id}/reprocessings`. Verbs in paths
  are a last resort and MUST be justified.

## HTTP method semantics

Methods carry meaning. Use them as intended — clients, caches, and proxies
all rely on it.

- **`GET`** — read-only. Safe and idempotent. MUST NOT have side effects.
- **`POST`** — create a resource, or invoke a non-idempotent action.
  Returns `201 Created` with a `Location` header for creation.
- **`PUT`** — full replace of a resource at a known URL. Idempotent:
  repeating the same `PUT` MUST yield the same final state.
- **`PATCH`** — partial update. Body describes the change, not the full
  resource. Should be idempotent when the change is expressible as such.
- **`DELETE`** — remove a resource. Idempotent: deleting an already-deleted
  resource returns `204 No Content` or `404 Not Found`, not `500`.

## Request and response formats

- Request and response bodies are **JSON**. Content-type is
  `application/json; charset=utf-8` on both sides.
- Every endpoint has an **explicit schema** for its request body, response
  body, and error shape. Publish schemas as OpenAPI (or the project's
  equivalent) alongside the code.
- Field names are `snake_case` in the wire format. Pick `snake_case` or
  `camelCase` once, at the API level, and apply it consistently.
- Timestamps are **ISO 8601** in **UTC** with an explicit `Z` suffix
  (`2025-01-15T09:30:00Z`). No local times, no ambiguous offsets.
- Money is an object with an integer amount in the currency's minor unit
  and an ISO 4217 currency code: `{"amount": 1299, "currency": "USD"}`.
  Never use floats for monetary values.
- Enumerated values are lower-case strings with explicit allowed values in
  the schema. Do not use magic integers.
- Unknown fields in a request MUST be rejected with `400 Bad Request`.
  Unknown fields in a response MUST be ignored by clients; this is how
  the API evolves without breaking them.

## Versioning

- APIs are versioned in the **URI**: `/v1/...`, `/v2/...`. Version lives
  between the host and the first resource segment (`https://api.example.com/v1/orders`).
- Only the **major** version appears in the URL. Minor and patch evolution
  is backwards-compatible and does not change the URL.
- **Breaking changes bump the major version.** A breaking change is any
  change that can cause a conforming existing client to fail: removing
  or renaming a field, tightening a type, changing an error code, or
  changing the meaning of a field.
- Additive, non-breaking changes (new optional fields, new endpoints,
  new enum values that existing clients can ignore) ship in the current
  major version.
- When a new major version ships, the previous major version MUST keep
  working for a documented deprecation window. The deprecation is
  announced in the response (`Deprecation` and `Sunset` headers) and in
  the API changelog before the old version is removed.

## Error response shape

Every error response uses a single consistent envelope. Clients parse one
shape, not many.

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Order REPLACE_ME was not found.",
    "details": [
      { "field": "order_id", "issue": "unknown" }
    ],
    "request_id": "REPLACE_ME"
  }
}
```

Rules:

- `code` is a stable, machine-readable `snake_case` string. Clients branch
  on `code`, never on `message`.
- `message` is a human-readable explanation. Safe to log, safe to show to
  an operator. MUST NOT contain secrets or PII.
- `details` is an optional array of structured sub-errors (for example,
  per-field validation failures). Present when the error has structure.
- `request_id` echoes the correlation ID the server assigned to the
  request, so clients can quote it in support tickets.
- The HTTP **status code** MUST match the error class: `400` for client
  input errors, `401` for missing or invalid auth, `403` for forbidden,
  `404` for not found, `409` for conflicts, `422` for semantic validation,
  `429` for rate limiting, `5xx` for server-side failures. Do not return
  `200 OK` with an error body.

## Pagination

List endpoints MUST paginate. Clients MUST NOT depend on unbounded results.

- Prefer **cursor-based** pagination. Request: `?limit=<n>&cursor=<opaque>`.
  Response:

  ```json
  {
    "items": [ /* ... */ ],
    "next_cursor": "REPLACE_ME"
  }
  ```

- `limit` has a documented default and a documented maximum. A `limit`
  over the maximum is clamped or rejected with `400`, but never silently
  exceeded.
- `next_cursor` is an opaque string. Clients MUST treat it as opaque and
  pass it back unchanged. A `null` or missing `next_cursor` means the
  end of the collection.
- Offset/page pagination is allowed only for small, bounded collections
  where the underlying store cannot support a cursor. It MUST NOT be used
  for anything whose size grows unboundedly.

## Filtering, sorting, field selection

These are query parameters on list endpoints, never path segments.

- **Filtering.** `?status=open&assignee_id=REPLACE_ME`. Each filter is a
  separate query parameter named after the field. Multi-value filters
  use repeated parameters (`?status=open&status=pending`), not
  comma-delimited strings.
- **Sorting.** `?sort=created_at` for ascending, `?sort=-created_at` for
  descending. Multi-key sort uses comma separation
  (`?sort=-created_at,id`). Only fields the API documents as sortable
  are accepted.
- **Field selection.** `?fields=id,status,total` restricts the response
  to the named fields. Unknown fields are rejected with `400`.
- Unknown query parameters are rejected with `400 Bad Request`. Silently
  ignoring them hides client bugs.

## Idempotency keys

`POST` requests that create resources (or trigger non-idempotent side
effects such as charging a card) MUST support an idempotency key.

- Clients send a unique key per logical operation in the
  `Idempotency-Key` request header. The value is an opaque string the
  client chooses (typically a UUID).
- The server stores the key together with the response for a documented
  window (for example, 24 hours).
- A retry with the **same key and same request body** returns the
  **same response** as the original, with the same status code. The
  side effect happens **once**.
- A retry with the **same key and a different body** is rejected with
  `409 Conflict` and an error code of `idempotency_key_conflict`.
- `GET`, `PUT`, and `DELETE` are already idempotent by HTTP contract and
  do not require idempotency keys.

## Authentication

- Authentication is **token-based** and sent on **every request**. APIs
  are stateless; the server does not rely on session cookies or sticky
  connections.
- Tokens travel in the `Authorization` header as
  `Authorization: Bearer <token>`. Never in the query string, never in
  the path, never in the request body.
- Tokens are short-lived. Long-lived credentials (for example, static
  API keys) are issued only where a short-lived token flow is not
  available, and they are scoped to the minimum permissions needed.
- The token format (JWT, opaque, signed reference) is an API-level
  decision; clients treat it as opaque regardless.
- Missing or invalid credentials return `401 Unauthorized`. Valid
  credentials without permission return `403 Forbidden`. Never conflate
  the two.
- Deeper authorization rules (scopes, roles, resource-level checks) live
  in the security standards, not here.

## Rate limiting and quotas

APIs MUST defend themselves against excessive traffic. Clients MUST
handle being throttled.

- Every response to an authenticated endpoint SHOULD include rate-limit
  headers so clients can self-throttle:
  - `RateLimit-Limit` — requests allowed in the current window.
  - `RateLimit-Remaining` — requests remaining in the current window.
  - `RateLimit-Reset` — seconds until the window resets.
- When a client exceeds its limit, the server returns `429 Too Many Requests`
  with the standard error envelope and a `Retry-After` header giving the
  number of seconds the client SHOULD wait before retrying:

  ```
  HTTP/1.1 429 Too Many Requests
  Retry-After: 30
  Content-Type: application/json; charset=utf-8

  {
    "error": {
      "code": "rate_limited",
      "message": "Request rate exceeded. Retry after 30 seconds.",
      "request_id": "REPLACE_ME"
    }
  }
  ```

- Limits are applied per credential (per API key, per token subject) —
  not per IP alone. IP-based limits are a coarse fallback, not the
  primary mechanism.
- Documented quotas (per minute, per day) MUST be published alongside the
  API. A client hitting an undocumented limit is an API bug.
