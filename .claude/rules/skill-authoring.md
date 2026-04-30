# Skill authoring

## Rules

- **Always use the `write-a-skill` skill to create a new skill.** Do not draft a skill from scratch by inventing structure or filenames. Load `.claude/skills/write-a-skill/SKILL.md` and follow its Process section (gather requirements → draft → review with user) and the SKILL.md template defined there.
- **Author new skills under `skills/<skill-name>/`**, never directly inside `.claude/skills/`. `.claude/skills/` is reserved for skills that need to be loaded into *this* project's Claude session (e.g. `write-a-skill` itself). If a skill authored here also needs to be available to Claude in this repo, copy or symlink it into `.claude/skills/<skill-name>/` after it passes the review checklist — don't develop it there.
- **Required files in every skill**: `SKILL.md` with frontmatter (`name`, `description`). The description must follow the rules in `write-a-skill` (max 1024 chars, third person, "Use when ..." trigger sentence).
- **Split files** (REFERENCE.md, EXAMPLES.md, `scripts/`) only when the criteria in `write-a-skill` apply (SKILL.md > 100 lines, distinct domains, rarely-needed advanced features, deterministic operations).
- **Run the review checklist** from `write-a-skill` before considering a skill done.

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
