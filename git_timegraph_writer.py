#!/usr/bin/env python3

# git-timegraph Writer (v3)
# Materializes files from database with conflict adjudication options

import sqlite3
import os
import subprocess
from pathlib import Path
from collections import defaultdict
import sys
import shutil

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"
OUTPUT_DIR = BASE_DIR / "checkout"

CONFLICT_POLICY = 'overwrite'  # options: 'abort', 'ignore', 'log', 'overwrite', 'rename'


def get_latest_blobs(db):
    path_info = {}
    query = """
        SELECT p.path, pe.new_blob, c.committer_time
        FROM path_events pe
        JOIN paths p ON p.id = pe.path_id
        JOIN commits c ON c.oid = pe.commit_oid
        ORDER BY c.committer_time
    """
    for path, blob, commit_time in db.execute(query):
        path_info[path] = {'blob': blob, 'mtime': commit_time}
    return path_info


def build_intermediate_tree(paths):
    tree = {}
    conflicts = set()
    for path in paths:
        parts = path.split('/')
        node = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                if part in node and isinstance(node[part], dict):
                    conflicts.add(path)
                node[part] = 'file'
            else:
                if part in node and node[part] == 'file':
                    conflicts.add('/'.join(parts[:i+1]))
                    node[part] = {}
                elif part not in node:
                    node[part] = {}
                node = node[part]
    return tree, conflicts


def resolve_conflict(target_path, policy):
    if policy == 'abort':
        raise RuntimeError(f"Conflict detected at {target_path}")
    elif policy == 'ignore':
        return False
    elif policy == 'log':
        print(f"Conflict detected (logged): {target_path}")
        return False
    elif policy == 'overwrite':
        if target_path.is_dir():
            shutil.rmtree(target_path)
        elif target_path.is_file():
            target_path.unlink()
        return True
    elif policy == 'rename':
        # For v3 we drop the suffix, treat same as log
        print(f"Conflict detected (rename policy skipped, read-only): {target_path}")
        return False
    else:
        raise ValueError(f"Unknown conflict policy: {policy}")


def materialize_files(db, output_dir, repo_dir, policy='abort'):
    output_dir.mkdir(parents=True, exist_ok=True)

    path_info = get_latest_blobs(db)
    tree, conflicts = build_intermediate_tree(path_info.keys())

    if conflicts and policy in ['abort', 'log']:
        for c in conflicts:
            print(f"Detected file/directory conflict: {c}")
        if policy == 'abort':
            raise RuntimeError("Aborting due to conflicts.")

    for path, info in path_info.items():
        target_path = output_dir / path

        # Conflict check before writing
        if target_path.exists():
            if target_path.is_dir() and target_path != output_dir:
                if not resolve_conflict(target_path, policy):
                    continue

        target_path.parent.mkdir(parents=True, exist_ok=True)

        content = subprocess.check_output(['git', 'cat-file', '-p', info['blob']], cwd=repo_dir)

        with open(target_path, 'wb') as f:
            f.write(content)

        os.utime(target_path, times=(info['mtime'], info['mtime']))


def main():
    if len(sys.argv) != 2:
        print("usage: git-timegraph-writer <repo_dir>")
        sys.exit(1)

    repo_dir = Path(sys.argv[1]).resolve()

    db = sqlite3.connect(DB_PATH)
    materialize_files(db, OUTPUT_DIR, repo_dir, policy=CONFLICT_POLICY)
    db.close()

    # Ensure trailing slash
    out_dir_str = str(OUTPUT_DIR)
    if not out_dir_str.endswith(os.sep):
        out_dir_str += os.sep
    print(f"Files materialized in {out_dir_str}")


if __name__ == "__main__":
    main()

