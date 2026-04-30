# skills

A workspace for authoring Claude Code skills. Each authored skill is a directory under `skills/<skill-name>/`.

## Stack
- Markdown for `SKILL.md` and supporting docs.
- No language runtime committed at the project level. Individual skills may bundle scripts in any language; declare runtime requirements inside that skill's directory.

## Directory Layout
```
skills/                    # Authored skills — source of truth for distribution
└── <skill-name>/
    ├── SKILL.md           # Required
    ├── REFERENCE.md       # Optional
    ├── EXAMPLES.md        # Optional
    └── scripts/           # Optional

.claude/skills/            # Skills loaded into this project's Claude session
└── write-a-skill/         # Authoring helper — see its SKILL.md

.claude/rules/             # Behavioral rules (load on demand — see index below)
LICENSE                    # MIT
README.md
```

## Canonical Commands
- Build: n/a
- Test:  n/a (skills are validated manually by loading them in a session)
- Lint:  n/a
- Run:   n/a

## Rules (load on demand)
Each rule file below is a focused behavioral contract. Read a rule file when its trigger matches your task — do not auto-load.

- `.claude/rules/skill-authoring.md` — read before creating, editing, or reviewing any skill (anything under `skills/` or `.claude/skills/`).
- `.claude/rules/git.md` — read before making any commit.
