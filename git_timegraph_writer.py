#!/usr/bin/env python3

# git-timegraph Writer (v2)
# Materializes files from database with pre-flight conflict detection
# Detects file/directory conflicts before attempting writes

import sqlite3
import os
import subprocess
from pathlib import Path
from collections import defaultdict
import sys

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"
OUTPUT_DIR = BASE_DIR / "checkout"


def get_latest_blobs(db):
    """Return the latest blob SHA and mtime per path"""
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
    """Build a tree representation of all paths, detecting file/dir conflicts"""
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


def materialize_files(db, output_dir, repo_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    path_info = get_latest_blobs(db)

    tree, conflicts = build_intermediate_tree(path_info.keys())
    if conflicts:
        print("Detected file/directory conflicts:")
        for c in conflicts:
            print(f"  {c}")
        print("Resolve conflicts manually or adjust paths.")
        return

    for path, info in path_info.items():
        blob_sha = info['blob']
        mtime = info['mtime']

        content = subprocess.check_output(['git', 'cat-file', '-p', blob_sha], cwd=repo_dir)

        target_path = output_dir / path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, 'wb') as f:
            f.write(content)

        os.utime(target_path, times=(mtime, mtime))


def main():
    if len(sys.argv) != 2:
        print("usage: git-timegraph-writer <repo_dir>")
        sys.exit(1)

    repo_dir = Path(sys.argv[1]).resolve()

    db = sqlite3.connect(DB_PATH)
    materialize_files(db, OUTPUT_DIR, repo_dir)
    db.close()

    print(f"Files materialized in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

