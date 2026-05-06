# Skill authoring

## Rules

- **Author new skills under `skills/<skill-name>/`**, never directly inside `.claude/skills/`. `.claude/skills/` is reserved for skills installed into this project's session via `scripts/manage-skill.sh`.
- **Required files in every skill**: `SKILL.md` with frontmatter fields `name` and `description`.
- **Description format**: max 1024 chars, written in third person. First sentence states what the skill does. Second sentence starts with "Use when …" and lists specific triggers.
- **Split files** (`REFERENCE.md`, `EXAMPLES.md`, `scripts/`) only when: `SKILL.md` exceeds 100 lines, content spans distinct domains, advanced features are rarely needed, or a deterministic operation benefits from an explicit script.
- **Skill names use hyphens**, never underscores — in directory names and frontmatter.
- **Context skill names must end with `-context`** — any skill whose `SKILL.md` begins with the `> **Context skill.**` banner must have a name (and directory) ending in `-context` (e.g. `claude-md-principles-context`).

## Review checklist

Before considering a skill done, verify:

- [ ] If this is a context skill (`> **Context skill.**` banner present), directory and `name` end with `-context`
- [ ] `description` includes a "Use when …" trigger sentence
- [ ] `SKILL.md` is under 100 lines
- [ ] No time-sensitive information embedded
- [ ] Terminology is consistent throughout
- [ ] Use concrete example to explain complex concepts
- [ ] External references are one level deep (no chains)
