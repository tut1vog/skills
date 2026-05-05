---
name: guide-me
description: Explains a concept with inline jargon glosses, presents a comprehensive subtopic syllabus with visited-tracking, persists a tree map per root in /tmp, and accepts free-form follow-ups or menu commands (quiz/branch/done). Use when the user says "guide me on <concept>".
---

Activate only on the explicit phrasing "guide me on <concept>". Once active, stay active for plausible follow-ups (menu replies, free-form questions about the current concept) and drop the framing for clearly unrelated messages. A fresh "guide me on <concept>" resumes from the existing `/tmp/guide-me-<root-slug>.md` map if present (see Map file rules); type `restart` as the next user message to wipe and start over.

## Every turn produces this shape

1. **Path line** — `Path: <root> [n/m] → ... → <current> (here, n/m)`. Counts = direct-children visited / direct-children total. Truncate to the last 4 hops if deeper. At root: `Path: <root> [n/m] (here)`. Atomic anchor: `Path: ... <current> (atomic, here)`.
2. **Explanation** — 3–5 sentences, brief but thorough. Technical precision for code and engineering topics; plain English otherwise.
3. **Terms used** — short glossary of comprehension-blocker terms used in the explanation. See "Terms used rules" below. Omit the entire block when no terms qualify.
4. **Syllabus** — comprehensive list of subtopics covering the current anchor's full conceptual surface. See "Syllabus rules" below.
5. **Menu line + free-form invitation** — exactly two lines: `[quiz] [branch <name>] [done]` followed by `or ask anything about <current>` on its own line.

## Path and tree rules

- The tree is rooted at the concept named in the original "guide me on <concept>". The root never changes for a given map file.
- `[branch <name>]` is the only thing that grows the tree or moves the current anchor:
  - If `<name>` matches an existing tree node (DFS-first match from root), jump to that node.
  - If `<name>` doesn't match, create it as a child of the current anchor and generate its syllabus on entry.
  - Either way, mark the destination `[x]` visited.
- Free-form follow-ups (any non-keyword message) keep the same anchor and never modify the tree.
- "Visited" criterion: a node is visited the moment the user `[branch]`es to it and the agent renders its explanation. The root is visited from turn 1 by virtue of the initial "guide me on <concept>" entry.
- There is no `[back]`. To return to a parent or any earlier anchor, the user types `[branch <ancestor-name>]`; the `Path:` line shows ancestor names so the user has what to type.
- There is no `[map]`. To view the full tree, the user runs `! cat /tmp/guide-me-<root-slug>.md`.
- Path counts are direct children only — `[n/m]` for an anchor means n of m direct subtopics in its syllabus have been visited.

## Terms used rules

The `Terms used:` block lists short glosses for jargon inside the main explanation prose, so the user doesn't have to ask about each unfamiliar word one-by-one.

- **Selection criterion**: include a term only if a non-expert would need to look it up to follow the explanation. Skip plain English; skip terms whose meaning is clear from context (e.g. "distributed systems" used descriptively).
- **Scope**: scan only the main explanation prose. Do not scan the path line, the syllabus why-lines, or the menu.
- **Skip the root**: never gloss the current anchor concept itself — the explanation is its definition.
- **Format**: `**Term** — short clause, ≤12 words.` Match the bold-term shape of the syllabus.
- **Cap**: at most 3 terms per block. If more qualify, pick the ones most load-bearing for parsing the explanation; the user can ask about the rest.
- **Dedup**: gloss each term at most once per anchor. Track the glossed set across turns; reset it on `[branch <name>]` (entering a new anchor). Do not reset on free-form follow-ups.
- **Empty block**: when no terms qualify (after dedup), omit the entire `Terms used:` block — do not show a placeholder.
- **Modes**: apply on every turn that emits prose — initial, free-form follow-ups, `[quiz]`. In `[quiz]`, additionally never gloss the term being tested (in practice this is the anchor, already excluded above).
- **Overlap with Syllabus**: if a glossed term also appears in the syllabus, still include it in `Terms used:` — the two blocks have different jobs (definition vs. navigation motivation).

## Syllabus rules

The `Syllabus for <current>:` block is the comprehensive list of subtopics that, walked through, give the user thorough understanding of the current anchor. It replaces the old Deeper list.

- **Comprehensiveness**: cover the conceptual surface — prerequisites, mechanisms, and edges. Do not curate to a "most relevant next step" subset. The whole point is to fight depth-first tunneling.
- **Length**: typical 5–9 items; soft cap 12; hard cap 15. If a topic genuinely has more than 15 subtopics, restructure as a meta-anchor with 5–9 sub-areas that themselves recurse. If the concept is genuinely atomic (fewer than 4 real subtopics), write `Syllabus: this concept is roughly atomic — no further breakdown.` and the `Path:` line shows `(atomic, here)`.
- **Order**: logical / pedagogical — prerequisites first, then composites, then applications and edge cases. The user's workflow is to walk the list top-to-bottom; ordering should support that walk.
- **Per-item format**: `[ ] **Name** — one-sentence why it matters.` Bold the name. Use `[x]` for visited items.
- **Visited markers**: read from the map file. `[x]` if the user has previously `[branch]`ed into that subtopic; `[ ]` otherwise.
- **Generation**: an anchor's syllabus is generated the first time that anchor becomes current (root on initial activation; sub-anchors on first `[branch]` entry). Once generated, the syllabus is stored in the map file and re-read on subsequent turns — do not regenerate or reorder it.
- **The Related list is gone.** Lateral concepts not in the syllabus are surfaced only via the user's own `[branch <name>]` (which creates a new child) or by starting a fresh "guide me on <X>".

## Map file rules

The map file at `/tmp/guide-me-<root-slug>.md` is the canonical state for a guide session. The agent reads it at the start of every turn and writes it on every state change.

- **Path**: `/tmp/guide-me-<root-slug>.md`. The root slug is the original `<concept>` from "guide me on <concept>", lowercased, spaces replaced with hyphens, non-alphanumeric stripped.
- **Format**: single markdown file per root. A small header (`# Guide: <root>`, `Current anchor: <name>`, `Last updated: <ISO-8601>`) followed by a single nested bulleted tree of the entire root's exploration to date.
- **Tree node format**: `- [x] **Name** — one-sentence why it matters.` for visited; `- [ ] ...` for unvisited. The root is the top-level item, marked `(root)` after its name.
- **Reads**: at the start of every turn, read the file to recover current_anchor, the visited set, and existing syllabi. If no file exists, this is the first turn for this root — generate the root's syllabus and write the file.
- **Writes**: write the file on every state change — on `[branch]` (new visited marker, possibly new sub-syllabus); on syllabus generation; on `[done]`. Update `Current anchor:` and `Last updated:`.
- **Hand-edit-friendly**: the file is plain markdown so the user may edit it (e.g., flip a checkbox, add a node, rename) between turns. The agent honors what it reads.
- **Resume on fresh activation**: when "guide me on <X>" is issued and the file already exists, read it and emit a one-line notice: `Resumed: <root> [n/m covered, last anchor "<current>"]. Type 'restart' to wipe and start fresh.` Then proceed with a normal turn for the recovered current anchor. If the next user message is `restart`, delete the file and re-init.
- **Persistence**: the file is not deleted on `[done]` — that is the entire point of canonical state. Resume across sessions works automatically.

Map file format example (after `[branch Idempotency keys]` from a fresh idempotency session):

```markdown
# Guide: idempotency
Current anchor: Idempotency keys
Last updated: 2026-05-05T14:30:00Z

- [x] **idempotency** (root)
  - [ ] **HTTP method semantics** — which verbs are required to be idempotent and why.
  - [x] **Idempotency keys** — client-supplied tokens used to dedupe retries server-side.
    - [ ] **Key generation** — UUID, payload hash, client-controlled vs server-issued.
    - [ ] **Storage backend** — Redis, DB tables, TTL trade-offs.
    - [ ] **Scope and collision** — per-user, per-tenant, global; avoiding clashes.
    - [ ] **Failure recovery** — what happens if the dedupe store is unavailable.
  - [ ] **At-least-once vs exactly-once delivery** — practical answer to "exactly-once".
  - [ ] **Retry policies** — how clients decide when and how often to retry.
  - [ ] **Server-side dedupe stores** — caches/DB tables tracking handled requests.
  - [ ] **Idempotency in databases** — UPSERT, MERGE, transactional retries.
  - [ ] **Pure functions** — stronger property: same input → same output, no side effects.
  - [ ] **Failure modes** — how non-idempotent retries break payments, queues, APIs.
```

## Menu options

- `[quiz]` — fire one quiz question. Adaptive: pick the format that fits the concept (free recall, multiple choice, application, counterexample), with a default bias toward **application** ("Is X a Y? Why?"). One question per call. On wrong/partial answer: identify the gap in one sentence and offer a hint, then re-show the menu. After two wrong attempts, give the answer and move on. Same anchor; map untouched.
- `[branch <name>]` — navigate to the named node. If it matches an existing tree node, jump to it; otherwise create it as a child of the current anchor and generate its syllabus on entry. Mark visited. Updates the map file.
- `[done]` — exit with: `Covered: <root> [n/m]. Map saved at /tmp/guide-me-<root-slug>.md. Re-run 'guide me on <root>' to resume. Done.` The map is not deleted.

## Free-form follow-ups

Any user message that is not a recognized menu keyword (`branch`, `quiz`, `done`, `restart`) is treated as a free-form follow-up about the current anchor. The current anchor and the map file are never modified.

- **Generic depth request** (`tell me more`, `go deeper`, `more details`): respond in 3–5 sentences covering mechanism, prerequisites, or edge cases not surfaced in the initial explanation.
- **Specific question** (`how does TTL work?`, `why is GET idempotent?`): respond in 2–4 sentences focused on the question.

After the response, re-render Terms used (subject to dedup), the syllabus (unchanged), and the menu line + invitation.

## Input tolerance

Parse permissively. Bracketed and bare forms of `branch`, `quiz`, and `done` count as menu keywords. Bare `branch` (no name) → ask "which one?". Bare `quiz` → fire on the current concept. Anything else — including phrases like `deeper`, `go deeper`, `tell me more`, or arbitrary questions — is a free-form follow-up about the current anchor. Immediately after a `Resumed:` notice, the bare keyword `restart` (no brackets needed) wipes the map file and re-initializes.

## Worked example

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

[quiz] [branch <name>] [done]
or ask anything about idempotency
```

User: `branch Idempotency keys`

(No existing tree node by that name → create as child of root, generate child syllabus, mark visited, write map.)

```
Path: idempotency [1/8] → Idempotency keys [0/4] (here)

Idempotency keys are client-supplied tokens — typically a UUID or content hash — that a server uses to recognize and dedupe retried requests. The client sends the same key on the original and any retries; the server stores it alongside the first attempt's result and short-circuits subsequent attempts presenting the same key. This converts at-least-once retry semantics into an effectively exactly-once outcome from the server's perspective. The key's lifetime, scope, and storage backend are the main design knobs.

Terms used:
  **UUID** — universally unique identifier; standard format for collision-free random IDs.

Syllabus for Idempotency keys:
  [ ] **Key generation** — UUID, payload hash, client-controlled vs server-issued.
  [ ] **Storage backend** — Redis, DB tables, TTL trade-offs.
  [ ] **Scope and collision** — per-user, per-tenant, global; avoiding clashes.
  [ ] **Failure recovery** — what happens if the dedupe store is unavailable.

[quiz] [branch <name>] [done]
or ask anything about Idempotency keys
```

User: `how do clients usually pick a key?`

(Free-form specific question → focused 2–4 sentence answer; same anchor; map untouched. `UUID` was already glossed on the previous turn for this anchor, so Terms used dedup keeps it out — block omitted.)

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

User: `what time is it?`

The skill defers — answer the question normally without path or menu.
