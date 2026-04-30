# Git

**When to read this**: read before making any commit.

## Rules

- **One logical change per commit.** A new skill, a rule update, and a README edit are three separate commits — not one.
- **Conventional-commit-style subject**: `<type>(<scope>): <imperative summary>` under 72 chars. Common types: `feat`, `fix`, `docs`, `chore`, `refactor`. Scope is usually the skill name (e.g. `pdf-tools`) or `meta` for project-wide changes.
- **Body** (optional, blank line after subject): explain *why*, not *what* — the diff already shows what.
- **Stage explicitly.** Use `git add <path>` with named paths. Avoid `git add -A` and `git add .` — they sweep in unintended files.
- **Never commit** files matching `*.local.*` (already gitignored), `.env*`, or anything containing credentials. If you see a secret in a diff, stop and remove it before committing.
- **Branch `main` is the trunk.** No remote is configured by default; do not add or push to a remote without explicit user confirmation.
- **Never** run `git push --force`, `git reset --hard`, or `git clean -fd` without explicit user confirmation — they destroy work.
- **Do not amend** commits the user can't see. Prefer a new commit; amend only when fixing the commit message of a commit you just made and have not shared.

## Examples

Good commit subjects:

```
feat(pdf-tools): add new skill for PDF text and table extraction
docs(meta): clarify skills/ vs .claude/skills/ split in README
fix(write-a-skill): correct frontmatter example in SKILL.md
chore(meta): initialize project scaffolding (CLAUDE.md, rules, license)
```

Good staging:

```
git add skills/pdf-tools/SKILL.md skills/pdf-tools/scripts/extract.py
git commit -m "feat(pdf-tools): add new skill for PDF text and table extraction"
```

Bad (do not do this):

```
git add -A                     # sweeps in unrelated files
git commit -m "updates"        # not conventional, not informative
git push --force origin main   # destructive, no user confirmation
```
