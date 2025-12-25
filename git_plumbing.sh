#!/usr/bin/env bash
set -euo pipefail

git_commits() {
    git rev-list --topo-order --reverse "$1"
}

git_commit_meta() {
    git cat-file -p "$1"
}

git_root_tree() {
    git ls-tree -r --full-tree "$1"
}

git_diff_tree() {
    git diff-tree -r --no-commit-id "$1" "$2"
}

# Dispatch
cmd="$1"
shift
"$cmd" "$@"
