#!/usr/bin/env python3

# git-timegraph Writer
# Materializes files from the database into a directory
# Sets mtime according to reducer timestamps
# Does not handle rename events yet

import sqlite3
import os
import subprocess
from pathlib import Path
from datetime import datetime

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


def materialize_files(db, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    path_info = get_latest_blobs(db)

    for path, info in path_info.items():
        blob_sha = info['blob']
        mtime = info['mtime']

        # Read blob content from git
        content = subprocess.check_output(['git', 'cat-file', '-p', blob_sha])

        target_path = output_dir / path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, 'wb') as f:
            f.write(content)

        # Set mtime
        os.utime(target_path, times=(mtime, mtime))


def main():
    import subprocess

    db = sqlite3.connect(DB_PATH)
    materialize_files(db, OUTPUT_DIR)
    db.close()

    print(f"Files materialized in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
