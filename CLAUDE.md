# skills

A workspace for authoring Claude Code skills. Each authored skill is a directory under `skills/<skill-name>/`.

## Stack
- Markdown for `SKILL.md` and supporting docs.
- No language runtime committed at the project level. Individual skills may bundle scripts in any language; declare runtime requirements inside that skill's directory.
- No build, test, lint, or run commands at the project level — skills are validated manually by loading them in a session.

## Directory Layout

See [README.md](README.md#layout) for the directory layout.

## Rules (load on demand)
Each rule file below is a focused behavioral contract. Read a rule file when its trigger matches your task — do not auto-load.

- `.claude/rules/skill-authoring.md` — read before creating, editing, or reviewing any skill (anything under `skills/` or `.claude/skills/`).
- `.claude/rules/git.md` — read before making any commit.
