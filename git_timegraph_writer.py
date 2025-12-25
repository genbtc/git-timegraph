#!/usr/bin/env python3

import sqlite3
import os
import subprocess
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"
OUTPUT_DIR = BASE_DIR / "checkout"


def delete_path(target_path):
    """Recursively delete file or directory."""
    if target_path.is_dir():
        for child in target_path.iterdir():
            delete_path(child)
        target_path.rmdir()
    elif target_path.exists():
        target_path.unlink()


def materialize_files(db, output_dir, repo_dir):
    """
    Writer phase.
    Consumes reduced_paths produced by the reducer.
    Deletes paths marked as non-existent.
    Handles file/dir conflicts on all ancestors.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    query = """
        SELECT path, "exists", blob, mtime
        FROM reduced_paths
    """

    for path, exists, blob, mtime in db.execute(query):
        target_path = output_dir / path

        if not exists:
            # deletion: remove path recursively if present
            if target_path.exists():
                delete_path(target_path)
            continue

        # ensure all parent directories exist
        parent = target_path.parent
        ancestors = []
        while parent != output_dir.parent:
            ancestors.append(parent)
            parent = parent.parent
        for ancestor in reversed(ancestors):
            if ancestor.exists() and ancestor.is_file():
                # A file exists where a directory is required
                delete_path(ancestor)
            ancestor.mkdir(exist_ok=True)

        # materialize file
        content = subprocess.check_output(
            ['git', 'cat-file', '-p', blob],
            cwd=repo_dir
        )

        with open(target_path, 'wb') as f:
            f.write(content)

        os.utime(target_path, times=(mtime, mtime))


def main():
    if len(sys.argv) != 2:
        print("usage: git_timegraph_writer <repo_dir>")
        sys.exit(1)

    repo_dir = Path(sys.argv[1]).resolve()

    db = sqlite3.connect(DB_PATH)
    materialize_files(db, OUTPUT_DIR, repo_dir)
    db.close()

    out = str(OUTPUT_DIR)
    if not out.endswith(os.sep):
        out += os.sep
    print(f"Files materialized in {out}")


if __name__ == "__main__":
    main()

