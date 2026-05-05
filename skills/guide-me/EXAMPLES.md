# guide-me — worked examples

One canonical example per supported explanation medium. Each example shows what the rendered output looks like for the *initial* turn after `guide me on <concept>`; the idempotency example also walks through `[branch]` and a free-form follow-up so the multi-turn shape is anchored once, and demonstrates the `Sources:` block (rendered on anchor-creation turns, gated off on conceptual free-form turns).

## Concept → medium

| Concept                  | Medium       | Turns shown                                  | Sources block                                          |
|--------------------------|--------------|----------------------------------------------|--------------------------------------------------------|
| idempotency              | prose        | initial, `[branch]`, free-form follow-up     | shown on initial + `[branch]`; gated off on free-form  |
| recursion                | code block   | initial only                                 | not shown (example predates feature; render per spec)  |
| TCP three-way handshake  | ASCII diagram| initial only                                 | not shown (example predates feature; render per spec)  |
| big-o comparison         | table        | initial only                                 | not shown (example predates feature; render per spec)  |

## guide me on idempotency (prose)

User: `guide me on idempotency`

(No existing `/tmp/guide-me-idempotency.md` → generate the root syllabus and write the map.)

```
Path: idempotency [0/8] (here)

An operation is idempotent when applying it more than once produces the same result as applying it once. In HTTP, GET and PUT are expected to be idempotent — retrying them after a network blip is safe — while POST is not. Idempotency matters anywhere retries happen: distributed systems, message queues, payment APIs. Designing for it usually means either making the operation naturally repeatable or attaching a unique key the receiver dedupes on.

Terms used:
  **GET / PUT / POST** — HTTP methods for reading, replacing, and creating resources.
  **Dedupes** — drops duplicates so the same action only takes effect once.

Syllabus for idempotency:
  [ ] **HTTP method semantics** — which verbs are required to be idempotent and why.
  [ ] **Idempotency keys** — client-supplied tokens used to dedupe retries server-side.
  [ ] **At-least-once vs exactly-once delivery** — practical answer to "exactly-once".
  [ ] **Retry policies** — how clients decide when and how often to retry.
  [ ] **Server-side dedupe stores** — caches/DB tables tracking handled requests.
  [ ] **Idempotency in databases** — UPSERT, MERGE, transactional retries.
  [ ] **Pure functions** — stronger property: same input → same output, no side effects.
  [ ] **Failure modes** — how non-idempotent retries break payments, queues, APIs.

Sources:
  - RFC 9110 §9.2.2 Idempotent Methods — https://datatracker.ietf.org/doc/html/rfc9110#section-9.2.2
  - Idempotence (Wikipedia) — https://en.wikipedia.org/wiki/Idempotence

[quiz] [branch <name>] [done]
or ask anything about idempotency
```

User: `branch Idempotency keys`

(No existing tree node by that name → create as child of root, generate child syllabus, mark visited, write map.)

```
Path: idempotency [1/8] → Idempotency keys [0/4] (here)

Idempotency keys are client-supplied tokens — typically a UUID or content hash — that a server uses to recognize and dedupe retried requests. The client sends the same key on the original and any retries; the server stores it alongside the first attempt's result and short-circuits subsequent attempts presenting the same key. This converts at-least-once retry semantics into an effectively exactly-once outcome from the server's perspective.

Terms used:
  **UUID** — universally unique identifier; standard format for collision-free random IDs.

Syllabus for Idempotency keys:
  [ ] **Key generation** — UUID, payload hash, client-controlled vs server-issued.
  [ ] **Storage backend** — Redis, DB tables, TTL trade-offs.
  [ ] **Scope and collision** — per-user, per-tenant, global; avoiding clashes.
  [ ] **Failure recovery** — what happens if the dedupe store is unavailable.

Sources:
  - Stripe API: Idempotent Requests — https://docs.stripe.com/api/idempotent_requests
  - Idempotency Keys (Brandur Leach) — https://brandur.org/idempotency-keys

[quiz] [branch <name>] [done]
or ask anything about Idempotency keys
```

User: `how do clients usually pick a key?`

(Free-form specific question → focused answer; same anchor; map untouched. `UUID` was already glossed on the previous turn for this anchor, so Terms used dedup keeps it out — block omitted. The question is conceptual — asking about typical client behavior, not a version-specific fact — so it doesn't qualify for the free-form search trigger; the Sources block is omitted as well.)

```
Path: idempotency [1/8] → Idempotency keys [0/4] (here)

Most clients generate a UUID v4 per request — random, cheap, collision-resistant — and reuse it on retries. Some hash the request payload instead, which has the side benefit that two semantically-identical requests get the same key, so accidental double-submission also dedupes. The choice usually comes down to whether the server should treat "different bytes, same intent" as the same operation.

Syllabus for Idempotency keys:
  [ ] **Key generation** — UUID, payload hash, client-controlled vs server-issued.
  [ ] **Storage backend** — Redis, DB tables, TTL trade-offs.
  [ ] **Scope and collision** — per-user, per-tenant, global; avoiding clashes.
  [ ] **Failure recovery** — what happens if the dedupe store is unavailable.

[quiz] [branch <name>] [done]
or ask anything about Idempotency keys
```

## guide me on recursion (code block)

User: `guide me on recursion`

The explanation is shorter than the prose example because the snippet *is* the explanation — adding sentences would dilute it.

```
Path: recursion [0/7] (here)

A function is recursive when it calls itself, with each call working on a smaller piece of the problem until it hits a base case that returns directly.

    def factorial(n):
        if n <= 1: return 1
        return n * factorial(n - 1)

Terms used:
  **Base case** — the input where the function returns directly without recursing.

Syllabus for recursion:
  [ ] **Base case design** — picking the stopping condition; off-by-one and infinite-recursion bugs.
  [ ] **Recursive case** — how the call shrinks toward the base case.
  [ ] **Stack frames and depth** — each call consumes stack; deep recursion overflows.
  [ ] **Tail call optimization** — when the compiler can reuse a frame; language support varies.
  [ ] **Memoization** — caching subproblem results to avoid exponential blowup.
  [ ] **Iterative equivalents** — turning recursion into a loop with an explicit stack.
  [ ] **Common patterns** — divide-and-conquer, tree traversal, backtracking.

[quiz] [branch <name>] [done]
or ask anything about recursion
```

## guide me on TCP three-way handshake (ASCII diagram)

User: `guide me on TCP three-way handshake`

Two sentences plus a 3-line diagram beats five sentences of prose describing the same packet exchange.

```
Path: TCP three-way handshake [0/6] (here)

The TCP handshake establishes a connection in three messages, with each side confirming receipt of the other's initial sequence number before any data flows. Without it, a sender would have no way to know the receiver is ready or to negotiate the starting sequence numbers used to detect lost or out-of-order packets.

    Client                          Server
       | -------- SYN ----------->    |
       | <------ SYN-ACK ---------    |
       | -------- ACK ----------->    |

Terms used:
  **SYN** — synchronize packet; opens a connection and announces a starting sequence number.
  **ACK** — acknowledgement packet; confirms receipt of a prior sequence number.
  **Sequence number** — per-byte counter that lets receivers detect loss and reorder packets.

Syllabus for TCP three-way handshake:
  [ ] **SYN packet** — what it carries and why it's the opener.
  [ ] **SYN-ACK packet** — combined acknowledgement and counter-synchronization.
  [ ] **ACK packet** — final confirmation; data may piggyback.
  [ ] **Initial sequence number selection** — randomization, ISN clock, security implications.
  [ ] **SYN flood attacks** — half-open connection exhaustion; SYN cookies as mitigation.
  [ ] **Connection teardown** — the FIN/ACK exchange that mirrors the handshake.

[quiz] [branch <name>] [done]
or ask anything about TCP three-way handshake
```

## guide me on big-o comparison (table)

User: `guide me on big-o comparison`

A single sentence plus a table; the table makes growth-rate differences obvious in a way prose can only gesture at.

```
Path: big-o comparison [0/6] (here)

Big-O describes how an algorithm's runtime grows as input size grows; comparing common classes shows what's tractable at scale and what isn't.

    | Class       | Name          | n=10 | n=10⁶          |
    |-------------|---------------|------|----------------|
    | O(1)        | constant      |    1 |              1 |
    | O(log n)    | logarithmic   |    3 |             20 |
    | O(n)        | linear        |   10 |      1,000,000 |
    | O(n log n)  | linearithmic  |   33 |     20,000,000 |
    | O(n²)       | quadratic     |  100 | 1,000,000,000² |

Syllabus for big-o comparison:
  [ ] **Common complexity classes** — O(1), O(log n), O(n), O(n log n), O(n²), O(2ⁿ).
  [ ] **Best, average, worst case** — same algorithm, different inputs.
  [ ] **Amortized analysis** — average cost per op across a sequence (e.g., dynamic arrays).
  [ ] **Big-Theta and Big-Omega** — tight and lower bounds vs. Big-O's upper bound.
  [ ] **Space vs time complexity** — same notation, different resource.
  [ ] **Constants and practical impact** — when a "slower" class wins for small n.

[quiz] [branch <name>] [done]
or ask anything about big-o comparison
```

## Off-topic deferral

User (mid-session): `what time is it?`

The skill defers — answer the question normally without path, syllabus, or menu. Same behavior on any clearly unrelated message.
