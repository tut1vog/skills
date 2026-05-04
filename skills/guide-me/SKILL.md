---
name: guide-me
description: Explains a concept, anchors the conversation with a breadcrumb, and offers menu-driven follow-up (deeper/ask/quiz/branch). Use when the user says "guide me on <concept>".
---

Activate only on the explicit phrasing "guide me on <concept>". Once active, stay active for plausible follow-ups (menu replies, free-form questions about the current concept) and drop the framing for clearly unrelated messages. A fresh "guide me on <concept>" resets the breadcrumb.

## Every turn produces this shape

1. **Anchor line** — `Root: <X>` if depth 1, otherwise `<root> → ... → <current>` truncated to the last 4 hops.
2. **Explanation** — 3–5 sentences, brief but thorough. Technical precision for code and engineering topics; plain English otherwise.
3. **Branch lists** — two labeled sublists:

   ```
   Deeper into <current>:
     **Name** — one-sentence why it matters.

   Related to <current>:
     **Name** — one-sentence why it matters.
   ```

   2–3 items per list. If the concept is genuinely atomic, write `Deeper: this concept is roughly atomic — forward motion is sideways.` Don't force-fit filler.
4. **Menu line** — exactly: `[deeper] [ask <q>] [quiz] [branch <name>] [done]`

## Breadcrumb rules

- `[branch <name>]` is the only thing that advances the breadcrumb.
- `[deeper]` and `[ask]` keep the same anchor — depth = lateral hops from root, not sub-topics surfaced.
- The Deeper list should not repeat sub-aspects already covered in earlier `[deeper]` turns on the same anchor.

## Menu options

- `[deeper]` — drill into the current concept (mechanism, prerequisites, edge cases). Same template, same anchor.
- `[ask <q>]` — free-form follow-up. Answer in 2–4 sentences focused on the question, then re-show branch lists and menu.
- `[quiz]` — fire one quiz question. Adaptive: pick the format that fits the concept (free recall, multiple choice, application, counterexample), with a default bias toward **application** ("Is X a Y? Why?"). One question per call. On wrong/partial answer: identify the gap in one sentence and offer a hint, then re-show the menu. After two wrong attempts, give the answer and move on.
- `[branch <name>]` — advance to a related concept. Reset Deeper/Related for the new anchor.
- `[done]` — exit with a one-line summary: `Covered: <root> → <hop> → <hop>. Done.`

## Input tolerance

Parse permissively. `deeper`, `[deeper]`, `Deeper`, "go deeper" all map to `[deeper]`. A free-form message without a keyword is treated as `[ask]`. Bare `branch` (no name) → ask "which one?". Bare `quiz` → fire on the current concept.

## Worked example

User: `guide me on idempotency`

```
Root: idempotency

An operation is idempotent when applying it more than once produces the same result as applying it once. In HTTP, GET and PUT are expected to be idempotent — retrying them after a network blip is safe — while POST is not. Idempotency matters anywhere retries happen: distributed systems, message queues, payment APIs. Designing for it usually means either making the operation naturally repeatable or attaching a unique key the receiver dedupes on.

Deeper into idempotency:
  **Idempotency keys** — client-supplied tokens used to dedupe retries server-side.
  **At-least-once vs exactly-once delivery** — why idempotency is the practical answer to "exactly-once".

Related to idempotency:
  **Pure functions** — a stronger property that implies idempotency.
  **Optimistic concurrency** — a different answer to the "what if it runs twice" problem.

[deeper] [ask <q>] [quiz] [branch <name>] [done]
```

User: `quiz`

```
Root: idempotency

Application quiz: A `POST /charge` endpoint creates a payment record on each call. The team adds a unique `Idempotency-Key` header that the server checks before creating. Is `POST /charge` now idempotent? Why or why not?

[deeper] [ask <q>] [quiz] [branch <name>] [done]
```

User: `what time is it?`

The skill defers — answer the question normally without anchor or menu.
