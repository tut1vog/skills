# skills

A workspace for authoring [Claude Code](https://docs.claude.com/en/docs/claude-code) skills.

Each skill is a self-contained directory under `skills/<skill-name>/` with a `SKILL.md` and any supporting files.

## Layout

```
skills/                    # Authored skills (source of truth for distribution)
└── <skill-name>/
    ├── SKILL.md           # Required — frontmatter + instructions
    ├── REFERENCE.md       # Optional — detailed docs
    ├── EXAMPLES.md        # Optional — usage examples
    └── scripts/           # Optional — utility scripts
scripts/
└── manage-skill.sh        # Install/uninstall skills to .claude/skills/
```

## Skills

- **audit-claude-config** — Audits a Claude Code project's configuration against upstream best practices and produces a findings report.
- **claude-md-principles-context** — Principles for writing high-quality CLAUDE.md files (structure, instruction budget, anti-patterns).
- **grill-me** — Interviews you relentlessly about a plan or design until reaching shared understanding.
- **guide-me** — Guided exploration of any concept with a tracked subtopic syllabus and quiz mode.
- **lint-instructions** — Lints instruction files for duplication, legacy negation, verbosity, ambiguous subjectivity, and decorative directives.
- **research-to-context-skill** — Researches a topic online and writes a reusable context skill file.
- **skills-as-context** — Explains the context-skill pattern and provides the canonical template for authoring one.
- **take-notes** — Writes a markdown note from conversation context and/or external sources.

## Authoring a new skill

In a Claude Code session inside this repo, ask Claude to author a new skill. Claude follows the rules in [`.claude/rules/skill-authoring.md`](.claude/rules/skill-authoring.md) (auto-loaded every session) — no manual setup needed. The output lands under `skills/<skill-name>/`.

## License

[MIT](LICENSE) © 2026 tut1vog
