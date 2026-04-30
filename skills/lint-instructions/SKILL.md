---
name: lint-instructions
description: Lints documentation and agent instruction files for four "instruction smells" — Duplication, Legacy Negation, Verbosity, and Ambiguous Subjectivity — and reports each finding with smell type, location, issue, and suggested refactor, then asks the user for permission before applying any fixes. Use when the user asks to lint, audit, review, or clean up CLAUDE.md, AGENTS.md, README.md, prompt files, SKILL.md files, or other documentation/instruction files for cross-file duplication, outdated negative phrasing, verbose tutorials in operational text, or vague subjective language.
---

# lint-instructions

## Quick start

1. Identify the target the user named: a file, glob, or directory of instruction/documentation files. If nothing was named, ask once — do not pick a default.
2. Read every targeted file in full (not partial reads). For directories, enumerate first.
3. Scan each file for the four smells defined below. For Duplication, compare across all targeted files.
4. Emit findings in the **Output format** block — one block per finding, no other prose between blocks.
5. After the findings, print a one-line count summary by smell type, then ask: `Apply these refactors? Reply with finding numbers, "all", or "none".`
6. Only after explicit user approval, edit the files. Apply only the approved findings.

## The four smells

### 1. Duplication (single source of truth)
The same rule, concept, or decision is stated in two or more files (or two distinct sections of one file).
- **Detect**: substantively overlapping prose, not just shared terminology. Paraphrases count.
- **Refactor**: pick one authoritative location; replace the others with a one-line reference (e.g. `See [path/to/file.md](path/to/file.md) §Section`).

### 2. Legacy Negation
A directive defined by what *not* to do, anchored to a prior workflow ("Do not create plan.md anymore", "We no longer use X").
- **Detect**: negations that reference a past state ("anymore", "no longer", "previously", "used to"); rules that only forbid without stating the current behavior.
- **Refactor**: state the current desired behavior affirmatively. Delete the historical contrast.

### 3. Verbosity
Tutorials, deep implementation detail, or background explanation that belongs in code comments or a technical appendix — not in operational instructions.
- **Detect**: paragraphs that explain *how something works internally* rather than *what the reader should do*; multi-paragraph examples where one line suffices.
- **Refactor**: reduce to the actionable directive. Move deep detail to a code comment at the implementation site, or to a `REFERENCE.md` / appendix file.

### 4. Ambiguous Subjectivity
Vague, unmeasurable adjectives that produce unpredictable behavior ("good", "robust", "clean", "nicely", "appropriate", "as needed", "well-formed").
- **Detect**: directives whose compliance cannot be checked by reading the output.
- **Refactor**: replace with a measurable constraint. Examples:
  - "write a good commit message" → "use Conventional Commits: `<type>(<scope>): <subject>`, subject ≤72 chars".
  - "make the script robust" → "wrap external I/O in try/except and log the exception with context".
  - "summarize nicely" → "summarize in ≤3 bullet points, each ≤20 words".

## Output format

For every finding, emit exactly this block (numbered sequentially across all files):

```
Finding #<n>
Smell Type: <Duplication | Legacy Negation | Verbosity | Ambiguous Subjectivity>
Location: <relative/path/to/file.md> §<section header or line range>
The Issue: <one or two sentences explaining what is wrong>
Suggested Refactor: <the exact rewritten text, or the specific action including all file paths/sections involved>
```

For Duplication, list every involved location in the `Location` field and name the chosen authoritative location in `Suggested Refactor`.

If a file has no smells, do not emit a block for it. After the last finding, print one summary line of the form `Found: <D> Duplication, <L> Legacy Negation, <V> Verbosity, <A> Ambiguous Subjectivity` and then the approval prompt.

## Approval and fixing

- Do not edit any file before approval. The findings list is read-only output.
- Accepted approval forms: `all`, `none`, or a comma-separated list of finding numbers. The user may also dictate per-finding edits that override the suggested refactor.
- When applying, re-read each file immediately before editing in case it changed, and edit only the lines covered by approved findings.
- After applying, report which findings were applied and which were skipped, with file paths.

## Scope guards

- Skip binary files, lockfiles, and any path matching `*.local.*` or `.env*`.
- Do not lint this skill's own `SKILL.md` unless the user explicitly targets it.
- If the target is a directory, restrict to common instruction file types by default: `*.md`, `AGENTS`, `CLAUDE.md`, `SKILL.md`, prompt files. Ask before extending to other file types.
