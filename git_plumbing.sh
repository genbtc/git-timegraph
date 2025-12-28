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

# Show diff between two commits (raw) including modes
git_diff_tree() {
    # --raw prints old mode, new mode, old blob, new blob, status, path
    git diff-tree -r --no-commit-id --pretty="" "$1" "$2"
}

# Dispatch
cmd="$1"
shift
"$cmd" "$@"

