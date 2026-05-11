---
name: vibe-coder-self-assessment
description: Grills the user on domain knowledge relevant to their project to surface gaps they may not know they have. Use when the user wants to check if they know enough to vibe code this project, or invokes "vibe-coder-self-assessment".
disable-model-invocation: true
---

Scan the project files to understand the tech stack, domain, and goals. If the user appended a prompt, use it to narrow the scope.

Identify all domain knowledge areas a competent practitioner would know that a vibe coder might not realize they need. Announce the areas upfront before asking anything.

Then grill the user relentlessly — scenario-framed questions that mirror real situations they'll face. Ask one question at a time. If an answer is shallow, follow up. After each exchange, reveal a reference answer they can peek at or ignore.

Do not ask about code details, syntax, or APIs — only concepts, tradeoffs, and failure modes.

When all areas are covered, summarize by domain: one-line signal (solid / partial / gap) with a brief note.
