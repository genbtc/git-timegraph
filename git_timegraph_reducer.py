#!/usr/bin/env python3

# git-timegraph Reducer
# Computes ctime and mtime per path from path_events
# V1 reducer, no rename detection yet

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"


def compute_timestamps(db):
    """
    Compute final per-path state from path_events.
    ctime = first introduction
    mtime = last semantic change
    If last change_type is 'D', the path does not exist.
    """
    path_state = {}

    query = """
        SELECT p.path,
               pe.change_type,
               c.committer_time
        FROM path_events pe
        JOIN paths p ON p.id = pe.path_id
        JOIN commits c ON c.oid = pe.commit_oid
        ORDER BY p.path, c.committer_time
    """

    for path, change_type, commit_time in db.execute(query):
        if path not in path_state:
            # First time we see this path
            if change_type == 'D':
                # Deleted before ever materialized: record non-existence
                path_state[path] = {
                    'exists': False,
                    'ctime': commit_time,
                    'mtime': commit_time,
                }
            else:
                path_state[path] = {
                    'exists': True,
                    'ctime': commit_time,
                    'mtime': commit_time,
                }
        else:
            # Subsequent events
            if commit_time >= path_state[path]['mtime']:
                path_state[path]['mtime'] = commit_time
                if change_type == 'D':
                    path_state[path]['exists'] = False
                else:
                    path_state[path]['exists'] = True
            else:
                # Time regression: ignore per spec
                pass

    return path_state


def main():
    db = sqlite3.connect(DB_PATH)

    timestamps = compute_timestamps(db)

    for path, times in timestamps.items():
        print(f"{path}: ctime={times['ctime']}, mtime={times['mtime']}")

    db.close()


if __name__ == "__main__":
    main()

