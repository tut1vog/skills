# Skill authoring

## Rules

- **Always use the `create-skill` skill to create a new skill.** Do not draft a skill from scratch by inventing structure or filenames. Load `skills/create-skill/SKILL.md` and follow its Process section and the SKILL.md template defined there.
- **Author new skills under `skills/<skill-name>/`**, never directly inside `.claude/skills/`. `.claude/skills/` is reserved for skills that need to be loaded into *this* project's Claude session. If a skill authored here also needs to be available to Claude in this repo, copy or symlink it into `.claude/skills/<skill-name>/` after it passes the review checklist — don't develop it there.
- **Required files in every skill**: `SKILL.md` with frontmatter (`name`, `description`). The description must follow the rules in `create-skill` (max 1024 chars, third person, "Use when ..." trigger sentence).
- **Split files** (REFERENCE.md, EXAMPLES.md, `scripts/`) only when the criteria in `create-skill` apply (SKILL.md > 100 lines, distinct domains, rarely-needed advanced features, deterministic operations).
- **Run the review checklist** from `create-skill` before considering a skill done.

## Examples

Creating a new skill named `pdf-tools`:

```
skills/pdf-tools/
├── SKILL.md         # name: pdf-tools; description: "...Use when working with PDFs..."
├── REFERENCE.md     # only if SKILL.md outgrows 100 lines or has rarely-used details
└── scripts/
    └── extract.py   # only if a deterministic operation needs explicit code
```

Bad layout (do not do this):

```
.claude/skills/pdf-tools/SKILL.md   # wrong location for a newly authored skill
skills/pdf-tools.md                 # missing directory + frontmatter structure
```
