#!/usr/bin/env python3

import sqlite3
import os
import subprocess
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"
OUTPUT_DIR = BASE_DIR / "checkout"


def materialize_files(db, output_dir, repo_dir):
    """
    Writer phase.
    Consumes reduced_paths produced by the reducer.
    No history walking, no semantic decisions.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    query = """
        SELECT path, exists, blob, mtime
        FROM reduced_paths
    """

    for path, exists, blob, mtime in db.execute(query):
        target_path = output_dir / path

        if not exists:
            # deletion: remove if present
            if target_path.exists():
                if target_path.is_dir():
                    os.rmdir(target_path)
                else:
                    target_path.unlink()
            continue

        # materialize file
        target_path.parent.mkdir(parents=True, exist_ok=True)

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

