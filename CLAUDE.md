# skills

A versioned workspace for authoring and publishing reusable Claude Code skills — each skill is a self-contained directory consumable by any Claude Code project. Each authored skill lives under `skills/<skill-name>/`.

## Stack
- Markdown for `SKILL.md` and supporting docs.
- No language runtime committed at the project level. Individual skills may bundle scripts in any language; declare runtime requirements inside that skill's directory.
- No build, test, lint, or run commands at the project level — skills are validated manually by loading them in a session.

## Directory Layout

See [README.md](README.md#layout) for the directory layout.

`skills/` is for authoring; `.claude/skills/` is where installed skills live (managed by `scripts/manage-skill.sh`, not edited directly).
