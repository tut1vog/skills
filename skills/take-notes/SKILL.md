---
name: take-notes
description: Writes a markdown note from conversation context and/or external sources (local files, URLs, PDFs). Merges all inputs, flags any conflicts for user clarification, and honours conversational "must keep" instructions. Use when the user says "take notes [on <concept>] [from <source>...] [to <path>]".
---

Activate on the slash command `/take-notes [on <concept>] [from <source1> from <source2> ...] [to <path>]`. Bare `/take-notes` is allowed; infer concept from the most recent coherent topic and use conversation context only, silently. If recent conversation contains multiple unrelated topics, ask which to capture before writing.

## Path

Path is required. If the trigger omits `to <path>`, respond `Where should I save the note?` and wait. Do not fall back to the current working directory.

Filename slug is lower-kebab-case from the concept name: `idempotency.md`, `optimistic-concurrency.md`. No date prefix.

If `<slug>.md` already exists in the target directory, append a numeric suffix: `idempotency-2.md`, `idempotency-3.md`. Never overwrite, never append to existing.

## Sources

Each `from <source>` argument is either a local file path or a URL.

**Supported file types**: plain text, markdown, PDF. For PDF files, delegate to the `pdf` skill to extract text content.

**URL fetching**: use the WebFetch tool. If a URL is inaccessible (404, timeout, paywall, etc.), abort and report: `Could not fetch <url>: <reason>`. Do not proceed.

**Multiple sources**: load all `from` arguments before writing begins. If any source fails to load, abort all and report which failed — ask the user to fix before re-running. Do not write partial notes.

## Merging

When sources are provided, merge them with conversation context:

1. Read and extract all source content.
2. Scan conversation for "must keep" instructions (see below).
3. Merge source content with conversation content — conversation takes priority where the two conflict.
4. Before writing, identify all conflicts: source-vs-source and source-vs-conversation contradictions. Flag every conflict to the user and ask for clarification. Do not write the note until all conflicts are resolved.

When no `from` sources are given, use conversation context only, silently.

## "Must keep" instructions

Before invoking, the user may state conversationally what the note must include. Scan recent conversation for imperative phrases directed at the note-taking intent:

- "make sure to include", "don't leave out", "keep the part about", "I want the notes to cover X"

Treat these as binding instructions — the flagged content must appear in the note regardless of how much of the session covered it.

## Content

Content is session-bounded: write only what was actually discussed or present in the sources. Canonical content the user did not see goes in the gap list at the end, not in prose. Do not ask the user to dictate or confirm a draft.

## Note shape

- `# <Concept Name>` — title-case H1.
- Intro paragraph, 1–3 sentences, textbook-chapter-opening style: what the concept is and why it matters.
- Topical H2 sections — content-driven (`## HTTP semantics`, `## The bind operator`). Never metadata titles (`## Summary`, `## Key points`). Pick count based on the session; no cap, no minimum.
- H3 sub-sections allowed when an H2 has distinct sub-points worth separating.
- `## Not yet covered` placed last — bullet list, no prose, of canonical sub-topics that did not come up. Omit the section entirely if the session was comprehensive.

## Confirmation

After writing, output exactly one line: `Wrote to <path>`. Do not reprint the file content.

## Examples

**Conversation only**
`/take-notes` → infers concept from context, asks for path.

**Single URL source**
`/take-notes on promises from https://example.com/promises-guide to ./notes/`

**Multiple sources**
`/take-notes from ./lecture.md from ./slides.pdf to ./notes/`

**With must-keep instruction**
User (before invoking): "make sure to include the part about error propagation"
`/take-notes on async-patterns from ./article.md to ./notes/`
→ skill ensures error propagation appears in the note.

**Missing path**
`/take-notes on idempotency` → `Where should I save the note?`

**Source fetch failure**
`/take-notes from https://paywalled-site.com to ./notes/`
→ `Could not fetch https://paywalled-site.com: 403 Forbidden`
