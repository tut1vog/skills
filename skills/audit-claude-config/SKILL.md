---
name: audit-claude-config
description: Audit a Claude Code project's configuration (.claude/, CLAUDE.md, .mcp.json) against the upstream best-practice repo at ~/.claude/best-practice and produce a findings report with verbatim doc quotes and proposed fixes. Pulls latest docs every run; refuses to audit unless the repo is installed and clean. Use when the user asks to audit, check, lint, or review their Claude Code configuration against best practices, or asks "am I doing X correctly" about subagents, skills, commands, MCP, memory, settings, or CLI flags. Optional topic argument narrows audit to one area.
---

# Audit Claude Config

Audit a Claude Code project's `.claude/`, `CLAUDE.md`, and `.mcp.json` against the upstream best-practice repo at `~/.claude/best-practice`. Produce a findings report; **never modify project files**.

## Process

### 1. Verify source (strict — block audit on any failure)

Run in order. If any step fails, **print fix instructions and exit without auditing**:

1. `~/.claude/best-practice` exists and resolves to a directory.
2. It contains `.git/`.
3. `git -C ~/.claude/best-practice remote get-url origin` returns `https://github.com/shanraisshan/claude-code-best-practice` (or `.git` variant).
4. `git -C ~/.claude/best-practice status --porcelain` is empty (clean tree).
5. `git -C ~/.claude/best-practice pull --ff-only` succeeds.

If missing or in a degraded state, print exactly (do **not** auto-clone):

```
Best-practice repo not installed (or in a degraded state).

Install:
  git clone https://github.com/shanraisshan/claude-code-best-practice ~/github.com/shanraisshan/claude-code-best-practice
  ln -s ~/github.com/shanraisshan/claude-code-best-practice ~/.claude/best-practice

Then re-run.
```

### 2. Locate project root

Walk up from cwd (max 8 levels) for a directory containing `.claude/` or `.git/`. That directory is the project root. None found → exit: "no Claude Code project found here — `cd` into a project first".

### 3. Select topics

If a topic arg was passed, it must be one of: `skills`, `subagents`, `commands`, `mcp`, `memory`, `settings`, `cli-startup-flags`, `power-ups`. Audit only that topic. Unknown topic → print the valid list, exit.

Otherwise auto-detect from project artifacts:

| Project artifact | Doc to load |
|---|---|
| `.claude/skills/*/SKILL.md` | `claude-skills.md` |
| `.claude/agents/*.md` | `claude-subagents.md` |
| `.claude/commands/*.md` | `claude-commands.md` |
| `.mcp.json` or `mcpServers` key in any `settings.json` | `claude-mcp.md` |
| `CLAUDE.md` or `.claude/rules/` | `claude-memory.md` |
| `.claude/settings.json` or `.claude/settings.local.json` | `claude-settings.md` |
| (always) | `claude-cli-startup-flags.md` |

`claude-power-ups.md` is loaded only via explicit topic arg.

List `~/.claude/best-practice/best-practice/*.md`. Any doc not in the mapping above is **unmapped** — note it in the report header. Any `.claude/<thing>/` artifact with no doc match (e.g. `hooks/`, `output-styles/`, `statusline.sh`) is **skipped (no doc)** — note in header.

### 4. Extract findings (grounded, quote-or-drop)

For each loaded doc:

1. Read the full doc.
2. Identify **authoritative claims** — sentences containing `must`, `should`, `required`, `avoid`, `don't`, `never`, `always`. Skip narrative prose, examples, and stylistic commentary.
3. Check the project against each claim.
4. If the project violates the claim, produce a finding. **Every finding must cite a verbatim quote from the doc as evidence.** If you cannot copy an exact quote, **drop the finding**. Do not paraphrase rules. Do not invent rules.
5. Severity: `required` if the claim uses `must`/`required`/`never`; otherwise `recommended`.

### 5. Emit report

Single markdown blob:

```
# Claude Config Audit
_Source: ~/.claude/best-practice (commit <sha>, pulled <ISO timestamp>)_
_Audited topics: <list>_
_Skipped (no doc): <list or "none">_
_Unmapped upstream docs: <list or "none">_

## Required (N findings)
### 1. [topic] <short title>
**Rule** (<doc>.md): "<verbatim quote>"
**Project state**: <file:line> — <observed>
**Proposed fix**: <imperative instructions the agent can follow later>

### 2. ...

## Recommended (M findings)
### 1. ...

## How to apply fixes
Tell me which findings to apply by number, e.g. "fix 1, 3" or "fix all required". I will follow the proposed-fix instructions outside this skill.
```

Findings numbered globally across both severity sections.

## Constraints

- Read-only — never edit project files; never auto-clone.
- Block audit on any source-health failure.
- Quote-or-drop: no paraphrased rules, no invented rules.
