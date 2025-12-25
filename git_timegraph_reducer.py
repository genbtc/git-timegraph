#!/usr/bin/env python3

# git-timegraph Reducer
# Computes final per-path state from path_events and persists it
# Authoritative semantic stage (ctime/mtime/existence/blob)

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"


def reduce_paths(db):
    """
    Reduce path_events into final per-path state.
    Rules:
      - ctime = first introduction
      - mtime = last semantic change (committer time)
      - last event wins
      - change_type == 'D' => path does not exist
    """
    cur = db.cursor()

    # Ensure output table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reduced_paths (
            path TEXT PRIMARY KEY,
            exists INTEGER NOT NULL,
            blob TEXT,
            ctime INTEGER NOT NULL,
            mtime INTEGER NOT NULL
        )
    """)

    # Clear previous reduction
    cur.execute("DELETE FROM reduced_paths")

    query = """
        SELECT p.path,
               pe.change_type,
               pe.new_blob,
               c.committer_time
        FROM path_events pe
        JOIN paths p ON p.id = pe.path_id
        JOIN commits c ON c.oid = pe.commit_oid
        ORDER BY p.path, c.committer_time
    """

    path_state = {}

    for path, change_type, blob, commit_time in cur.execute(query):
        if path not in path_state:
            # First time this path appears
            if change_type == 'D':
                path_state[path] = {
                    'exists': 0,
                    'blob': None,
                    'ctime': commit_time,
                    'mtime': commit_time,
                }
            else:
                path_state[path] = {
                    'exists': 1,
                    'blob': blob,
                    'ctime': commit_time,
                    'mtime': commit_time,
                }
        else:
            # Subsequent events; last event wins
            if commit_time >= path_state[path]['mtime']:
                path_state[path]['mtime'] = commit_time
                if change_type == 'D':
                    path_state[path]['exists'] = 0
                    path_state[path]['blob'] = None
                else:
                    path_state[path]['exists'] = 1
                    path_state[path]['blob'] = blob
            else:
                # Time regression: ignore per spec
                pass

    # Persist reduced state
    for path, st in path_state.items():
        cur.execute(
            "INSERT OR REPLACE INTO reduced_paths VALUES (?, ?, ?, ?, ?)",
            (path, st['exists'], st['blob'], st['ctime'], st['mtime'])
        )

    db.commit()

    return path_state


def main():
    db = sqlite3.connect(DB_PATH)

    reduced = reduce_paths(db)

    # Optional inspection output
    for path, st in reduced.items():
        if st['exists']:
            print(f"{path}: ctime={st['ctime']}, mtime={st['mtime']}")
        else:
            print(f"{path}: DELETED at {st['mtime']}")

    db.close()


if __name__ == "__main__":
    main()

