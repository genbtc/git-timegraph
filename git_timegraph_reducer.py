#!/usr/bin/env python3

# git-timegraph Reducer
# Computes ctime and mtime per path from path_events
# V1 reducer, no rename detection yet

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"


def compute_timestamps(db):
    # Dictionary to hold per-path timestamps
    path_times = {}

    # Query path_events in commit_time order
    query = """
        SELECT p.path, c.committer_time
        FROM path_events pe
        JOIN paths p ON p.id = pe.path_id
        JOIN commits c ON c.oid = pe.commit_oid
        ORDER BY c.committer_time, p.path
    """

    for path, commit_time in db.execute(query):
        if path not in path_times:
            # First introduction: ctime = mtime = first commit_time
            path_times[path] = {'ctime': commit_time, 'mtime': commit_time}
        else:
            # Update mtime if commit_time is newer
            if commit_time >= path_times[path]['mtime']:
                path_times[path]['mtime'] = commit_time
            else:
                # Regression, ignore as per spec
                pass

    return path_times


def main():
    db = sqlite3.connect(DB_PATH)

    timestamps = compute_timestamps(db)

    for path, times in timestamps.items():
        print(f"{path}: ctime={times['ctime']}, mtime={times['mtime']}")

    db.close()


if __name__ == "__main__":
    main()

