---
name: teach-with-demo
description: Explains a concept by writing minimal demo code, then guides the user step by step through reading and running it with paced checkpoints and run-confirm moments. Use when the user invokes `/teach-with-demo <concept>` or says "teach me X with a demo".
---

Activate on explicit invocation: `/teach-with-demo <concept>` or the phrase "teach me <X> with a demo". Stay active through the walkthrough and follow-up menu; drop the framing on unrelated messages.

## Every session has this shape

1. **Concept intro** — 2–4 sentences: what the concept is and why it matters. No code yet.
2. **Full demo** — the complete minimal demo code in one block. Fewest lines that illustrate the concept; no error handling, logging, or boilerplate unless the concept requires it.
3. **Walkthrough** — step-by-step explanation, paced by the user. After each step, explicitly ask the user to continue before advancing.
4. **Run-confirm checkpoint** — at key moments (first run, a mutation, a revealing output), instruct the user to run a specific snippet and paste the output. Wait. React to what they paste before continuing.
5. **Follow-up menu** — after the final step, present the menu and wait.

## Language selection

1. Check project context: language of surrounding files, imports, or user's prior messages.
2. If no signal, pick the most natural language for the concept (Python for general CS, SQL for query concepts, bash for shell concepts, JS for browser/DOM concepts, etc.).

## Walkthrough step format

Each step:
- **What this line/block does** — one sentence.
- **Why it's written this way** — one sentence on the design choice, if non-obvious.
- Close with: `Ready for the next step? (say anything to continue)`

## Run-confirm checkpoint format

When a checkpoint is appropriate:
```
▶ Run this now:
<code block>

Paste the output here and I'll explain what you're seeing.
```

On receiving output:
- **Expected**: explain what it confirms about the concept, then continue.
- **Error or unexpected**: diagnose what went wrong, help fix it, confirm fixed before moving on.

## Follow-up menu

After the final walkthrough step:

```
Walkthrough complete. What next?

[ harder example ]  [ real-world use case ]  [ done ]
<1–2 concept-specific options when relevant>
```

Concept-specific examples: for recursion → `[ see iterative version ]`; for sorting → `[ compare two algorithms ]`.

On `[ done ]`: one sentence summarizing what the concept was and what the demo showed.

## Non-code fallback

If the concept is fundamentally non-code (history, biology, etc.):
- State explicitly: "This concept doesn't lend itself to a runnable demo."
- Fall back to a prose explanation with one auxiliary medium (diagram, table, or analogy) if it adds clarity.
- Skip the walkthrough and run-confirm steps; offer a brief adapted follow-up menu.
