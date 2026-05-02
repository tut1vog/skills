---
name: create-skill
description: Create new agent skills with proper structure, progressive disclosure, and bundled resources. Use when user wants to create, write, or build a new skill.
---

# Creating Skills

## Process

1. **Detect prior grilling.** If the conversation already contains substantive Q&A about the to-be-created skill's design (purpose, use cases, scripts, references, trigger phrasing), proceed to step 2. Otherwise, invoke the `grill-me` skill via the Skill tool and grill until every branch of the design tree resolves. Cold use is not supported — grilling is mandatory.

2. **Summarize-and-confirm requirements.** Post one structured message derived from the grilling:

   - **Name:** `<skill-name>` (hyphens, never underscores)
   - **Purpose:** what the skill does, one sentence
   - **Trigger / Use when:** specific phrases or contexts
   - **Use cases:** concrete examples
   - **Scripts:** y/n; if y, which deterministic operations
   - **References:** any bundled docs or external pointers
   - **Other decisions:** anything else the grilling settled

   Ask the user to confirm or patch inline. Do not draft until confirmed.

3. **Draft** files in memory:
   - `SKILL.md` with frontmatter (`name`, `description`)
   - Additional reference files if SKILL.md exceeds 100 lines
   - Utility scripts if deterministic operations needed

4. **Ship-it confirm.** Show drafted files inline. Ask one question: *ship it, or changes?*
   - **Ship** → write files to disk under `skills/<skill-name>/`
   - **Changes** → iterate inline; re-confirm before writing

## Skill Structure

```
skill-name/
├── SKILL.md           # Main instructions (required)
├── REFERENCE.md       # Detailed docs (if needed)
├── EXAMPLES.md        # Usage examples (if needed)
└── scripts/           # Utility scripts (if needed)
    └── helper.js
```

## SKILL.md Template

```md
---
name: skill-name
description: Brief description of capability. Use when [specific triggers].
---

# Skill Name

## Quick start

[Minimal working example]

## Workflows

[Step-by-step processes with checklists for complex tasks]

## Advanced features

[Link to separate files: See [REFERENCE.md](REFERENCE.md)]
```

## Description Requirements

The description is **the only thing your agent sees** when deciding which skill to load. It's surfaced in the system prompt alongside all other installed skills.

**Format:**

- Max 1024 chars
- Third person
- First sentence: what it does
- Second sentence: "Use when [specific triggers]"

**Good:** `Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when user mentions PDFs, forms, or document extraction.`

**Bad:** `Helps with documents.`

## When to Add Scripts

Add utility scripts when the operation is deterministic (validation, formatting), the same code would be generated repeatedly, or errors need explicit handling.

## When to Split Files

Split into separate files when SKILL.md exceeds 100 lines, content has distinct domains, or advanced features are rarely needed.

## Review Checklist

Before Step 4 ship confirmation, verify:

- [ ] Description includes triggers ("Use when…")
- [ ] SKILL.md under 100 lines
- [ ] No time-sensitive info
- [ ] Consistent terminology
- [ ] Concrete examples included
- [ ] References one level deep
