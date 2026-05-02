#!/usr/bin/env bash
# Install a skill from this repo via symlink.
#
# Usage: scripts/install-skill.sh <skill-name> [project-path]
#
#   <skill-name>    Required. Directory name under skills/ in this repo.
#   [project-path]  Optional. If given, link into <project-path>/.claude/skills/.
#                   If omitted, link into ~/.claude/skills/ (user-level install).

set -euo pipefail

usage() {
  sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
}

if [[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 1
fi

skill_name="$1"
project_path="${2:-}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

src="$repo_root/skills/$skill_name"
if [[ ! -d "$src" ]]; then
  echo "error: skill '$skill_name' not found at $src" >&2
  exit 1
fi
if [[ ! -f "$src/SKILL.md" ]]; then
  echo "error: $src is missing SKILL.md" >&2
  exit 1
fi

if [[ -z "$project_path" ]]; then
  target_dir="$HOME/.claude/skills"
else
  if [[ ! -d "$project_path" ]]; then
    echo "error: project path '$project_path' is not a directory" >&2
    exit 1
  fi
  project_path="$(cd "$project_path" && pwd)"
  target_dir="$project_path/.claude/skills"
fi

mkdir -p "$target_dir"
target="$target_dir/$skill_name"

if [[ -L "$target" ]]; then
  existing="$(readlink "$target")"
  if [[ "$existing" == "$src" ]]; then
    echo "already linked: $target -> $src"
    exit 0
  fi
  echo "error: $target already exists as a symlink to $existing" >&2
  echo "remove it manually to replace it" >&2
  exit 1
fi

if [[ -e "$target" ]]; then
  echo "error: $target already exists and is not a symlink" >&2
  exit 1
fi

ln -s "$src" "$target"
echo "linked: $target -> $src"
