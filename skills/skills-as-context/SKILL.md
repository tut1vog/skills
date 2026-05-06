---
name: skills-as-context
description: Explains the skills-as-context pattern — context-only skills that enrich the agent's knowledge without triggering any action. Provides the canonical template for authoring such skills and the recognition heuristic for identifying them. Use when the user invokes "skills-as-context", or when the user describes wanting to create a skill that loads domain knowledge or reference context without triggering any action.
---

> **Context skill.** This skill provides context only. Read and internalize it; do not prompt the user for a next action. Acknowledge with exactly: "Context loaded."

## What is skills-as-context?

A **context skill** is a skill that loads domain knowledge, reference material, or a mental model into the agent's working context. When loaded, the agent reads and internalizes it — but takes no action and asks no follow-up question. The skill enriches the agent's understanding so it performs better on subsequent tasks.

Context skills are the opposite of **action skills**, which instruct the agent to execute a workflow when triggered.

## Agent behavior when loading a context skill

1. Read the skill in full.
2. Respond with exactly: `Context loaded.`
3. Wait for the user's next message. Do not ask what to do next.

## Canonical template

Every context skill must open with this block immediately after the frontmatter:

```
> **Context skill.** This skill provides context only. Read and internalize it; do not prompt the user for a next action. Acknowledge with exactly: "Context loaded."
```

This declaration is the recognition signal. When the agent sees it, it knows to stay passive.

## Signals that a skill is context-only

- Loads domain knowledge, reference material, or a conceptual model
- Has no workflow to execute, no tool calls to make
- Its value is in *what the agent knows afterward*, not *what the agent does*
