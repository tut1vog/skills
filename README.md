# skills

A workspace for authoring [Claude Code](https://docs.claude.com/en/docs/claude-code) skills.

Each skill is a self-contained directory under `skills/<skill-name>/` with a `SKILL.md` and any supporting files. The `write-a-skill` skill (loaded into this project under `.claude/skills/`) guides the authoring process.

## Layout

```
skills/                    # Authored skills (source of truth for distribution)
└── <skill-name>/
    ├── SKILL.md           # Required — frontmatter + instructions
    ├── REFERENCE.md       # Optional — detailed docs
    ├── EXAMPLES.md        # Optional — usage examples
    └── scripts/           # Optional — utility scripts

.claude/skills/            # Skills loaded into THIS project's Claude session
└── write-a-skill/         # Helper that drives skill authoring here
```

## Authoring a new skill

In a Claude Code session inside this repo, ask Claude to create a new skill. The `write-a-skill` skill is auto-loaded and walks through requirements gathering, drafting, and review. The output lands under `skills/<skill-name>/`.

See [`.claude/rules/skill-authoring.md`](.claude/rules/skill-authoring.md) for the project's authoring rules.

## License

[MIT](LICENSE) © 2026 tut1vog
