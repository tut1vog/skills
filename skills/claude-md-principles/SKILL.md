---
name: claude-md-principles
description: Principles for writing high-quality CLAUDE.md files — covering structure, instruction budget, length, anti-patterns, and progressive disclosure. Use when writing a new CLAUDE.md, improving an existing one, or answering questions about what belongs in CLAUDE.md.
---

> **Context skill.** This skill provides context only. Read and internalize it; do not prompt the user for a next action. Acknowledge with exactly: "Context loaded."

## Mental model

CLAUDE.md is loaded into every session automatically. The model has no memory between sessions — CLAUDE.md is the only persistent context it receives about the project. Every token here affects every phase of every agent task.

## Loading behavior

Claude Code walks **up** the directory tree at startup and loads every CLAUDE.md it finds — ancestor files load immediately. Files in **subdirectories** load lazily (only when Claude touches files there). **Sibling** directories never load each other's CLAUDE.md.

A global `~/.claude/CLAUDE.md` applies to all sessions regardless of project. Use `CLAUDE.local.md` (git-ignored) for personal preferences that shouldn't be shared with the team.

In monorepos: put shared conventions in the root CLAUDE.md; put component-specific instructions in component-level CLAUDE.md files.

## Structure: cover WHAT, WHY, HOW

- **WHAT** — stack, project layout, monorepo structure and shared packages
- **WHY** — overall purpose and the role of each major component
- **HOW** — build commands, test commands, environment setup, verification steps

## Instruction budget

Claude Code's built-in system prompt already consumes ~50 instructions. Frontier models handle ~150–200 total instructions reliably — beyond that, instruction-following degrades uniformly across all instructions, not just the new ones. Be selective.

## Length

Target under 200 lines. Include only content that applies universally — every session, every task. Claude ignores CLAUDE.md content it judges irrelevant to the current task, so bloated files dilute without adding coverage.

## Progressive disclosure

Offload rarely-needed detail to supplementary files (e.g. `agent_docs/conventions.md`, `agent_docs/building.md`). Reference them with a brief description in CLAUDE.md so Claude knows when to load them.

Prefer file:line pointers over embedded code snippets — snippets become stale; pointers stay accurate.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Code style rules in CLAUDE.md | Deterministic linters do this better; wastes instruction budget |
| Exhaustive command or schema dumps | Stuffs rarely-needed detail past the selective threshold |
| Task-specific instructions | Won't apply to future sessions; dilutes universally applicable guidance |
| Manually curating is not worth it | CLAUDE.md is the highest-leverage point of the harness — it is worth it |
