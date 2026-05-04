---
name: take-notes
description: Writes a markdown note of a recent conversation topic. Structures the note as topical H2 sections derived from the concept (textbook-chapter style), with content session-bounded and a "Not yet covered" gap list. Use when the user says "take notes [on <concept>] [to <path>]".
---

Activate only on the explicit phrasing `take notes [on <concept>] [to <path>]`. Bare `take notes` is allowed; infer the concept from the most recent coherent topic. If recent conversation contains multiple unrelated topics, ask which to capture before writing.

## Path

Path is required. If the trigger omits `to <path>`, respond `Where should I save the note?` and wait. Do not fall back to the current working directory.

Filename slug is lower-kebab-case from the concept name: `idempotency.md`, `optimistic-concurrency.md`. No date prefix.

If `<slug>.md` already exists in the target directory, append a numeric suffix: `idempotency-2.md`, `idempotency-3.md`. Never overwrite, never append to existing.

## Content

Pull from recent conversation history. Do not ask the user to dictate or to confirm a draft — they just had the session, they want the artifact.

Content is session-bounded: write only what was actually discussed. Canonical content the user did not see goes in the gap list at the end, not in prose.

## Note shape

- `# <Concept Name>` — title-case H1.
- Intro paragraph, 1–3 sentences, textbook-chapter-opening style: what the concept is and why it matters.
- Topical H2 sections — content-driven (`## HTTP semantics`, `## The bind operator`). Never metadata titles (`## Summary`, `## Key points`). Pick count based on the session; no cap, no minimum.
- H3 sub-sections allowed when an H2 has distinct sub-points worth separating.
- `## Not yet covered` placed last — bullet list, no prose, of canonical sub-topics that did not come up. Omit the section entirely if the session was comprehensive.

## Confirmation

After writing, output exactly one line: `Wrote to <path>`. Do not reprint the file content.

## Worked example

User: `take notes on idempotency to ./notes/`

Resulting `./notes/idempotency.md`:

```md
# Idempotency

Idempotency is the property that applying an operation more than once produces the same result as applying it once. It matters anywhere retries happen: distributed systems, message queues, payment APIs.

## What it means

An operation is idempotent when its second, third, and Nth applications are indistinguishable in effect from the first. This is a property of the operation as observed by the system, not of its implementation.

## HTTP semantics

GET, PUT, and DELETE are specified as idempotent in HTTP; POST is not. Retrying a GET after a network blip is safe; retrying a POST may create a second resource.

## Idempotency keys

A common pattern: the client attaches a unique `Idempotency-Key` header, and the server records the (key, result) pair. Retries with the same key return the recorded result without re-executing.

### Key generation

UUIDs work. The key must be unique per *logical* request, not per physical retry — generate once on the client, reuse across retries.

## Not yet covered

- At-least-once vs exactly-once delivery semantics
- Distributed locks as an alternative to idempotency keys
- Idempotency in event-sourced systems
```

Skill output: `Wrote to ./notes/idempotency.md`

### Missing-path case

User: `take notes on idempotency`

Skill: `Where should I save the note?`
