#!/usr/bin/env bash
# Manage a skill from this repo via symlink (install or uninstall).
#
# Usage:
#   scripts/manage-skill.sh <skill-name> [project-path]
#   scripts/manage-skill.sh -u|--uninstall <skill-name> [project-path]
#
#   <skill-name>     Required. Directory name under skills/ in this repo.
#   [project-path]   Optional. If given, target <project-path>/.claude/skills/.
#                    If omitted, target ~/.claude/skills/ (user-level).
#   -u, --uninstall  Remove the symlink instead of installing it.
#                    Refuses to remove a non-symlink or a symlink whose target
#                    is not this repo's skills/<skill-name>.

set -euo pipefail

usage() {
  sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
}

mode="install"
args=()
for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    -u|--uninstall) mode="uninstall" ;;
    --) ;;
    -*) echo "error: unknown flag '$arg'" >&2; usage >&2; exit 1 ;;
    *) args+=("$arg") ;;
  esac
done

if [[ ${#args[@]} -lt 1 ]]; then
  usage >&2
  exit 1
fi

skill_name="${args[0]}"
project_path="${args[1]:-}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

src="$repo_root/skills/$skill_name"

if [[ "$mode" == "install" ]]; then
  if [[ ! -d "$src" ]]; then
    echo "error: skill '$skill_name' not found at $src" >&2
    exit 1
  fi
  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "error: $src is missing SKILL.md" >&2
    exit 1
  fi
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

target="$target_dir/$skill_name"

if [[ "$mode" == "uninstall" ]]; then
  if [[ ! -L "$target" && ! -e "$target" ]]; then
    echo "not installed: $target"
    exit 0
  fi
  if [[ ! -L "$target" ]]; then
    echo "error: $target exists but is not a symlink; refusing to remove" >&2
    exit 1
  fi
  existing="$(readlink "$target")"
  if [[ "$existing" != "$src" ]]; then
    echo "error: $target is a symlink to $existing, not $src; refusing to remove" >&2
    exit 1
  fi
  rm "$target"
  echo "unlinked: $target"
  exit 0
fi

mkdir -p "$target_dir"

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
