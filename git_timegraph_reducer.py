#!/usr/bin/env python3

# git_timegraph_reducer.py - Computes final per-path state from path_events

import sqlite3
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"


def reduce_paths(db: sqlite3.Connection, verbose: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Reduce path_events into final per-path state.
    Rules:
      - ctime = first introduction
      - mtime = last semantic change (committer time)
      - last event wins
      - change_type == 'D' => path does not exist
      - deletions are recursive for directories
    """
    cur = db.cursor()

    # Clear previous reduction
    cur.execute("DELETE FROM reduced_paths")

    query = '''
        SELECT p.path,
               pe.change_type,
               pe.new_blob,
               c.committer_time
        FROM path_events pe
        JOIN paths p ON p.id = pe.path_id
        JOIN commits c ON c.oid = pe.commit_oid
        ORDER BY p.path, c.committer_time
    '''

    path_state: Dict[str, Dict[str, Any]] = {}

    for path, change_type, blob, commit_time in cur.execute(query):
        state = path_state.get(path)
        if state is None:
            path_state[path] = {
                'exists': 0 if change_type == 'D' else 1,
                'blob': None if change_type == 'D' else blob,
                'ctime': commit_time,
                'mtime': commit_time,
            }
        else:
            if commit_time >= state['mtime']:
                state['mtime'] = commit_time
                if change_type == 'D':
                    state['exists'] = 0
                    state['blob'] = None
                else:
                    state['exists'] = 1
                    state['blob'] = blob

    # Recursive deletions for directories
    sorted_paths = sorted(path_state.keys())
    for path in sorted_paths:
        st = path_state[path]
        if st['exists'] == 0:
            prefix = path + '/'
            for child_path in sorted_paths:
                if child_path.startswith(prefix):
                    child = path_state[child_path]
                    child['exists'] = 0
                    child['blob'] = None

    # Persist reduced state
    for path, st in path_state.items():
        cur.execute(
            "INSERT OR REPLACE INTO reduced_paths VALUES (?, ?, ?, ?, ?)",
            (path, st['exists'], st['blob'], st['ctime'], st['mtime'])
        )
        if verbose and st['exists']:
            print(f"{path}: ctime={st['ctime']}, mtime={st['mtime']}")
        elif verbose:
            print(f"{path}: DELETED at {st['mtime']}")

    db.commit()
    return path_state


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Reduce Git Timegraph path events into final state")
    parser.add_argument('--verbose', action='store_true', help='Print detailed reduction info')
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH)
    reduce_paths(db, verbose=args.verbose)
    db.close()


if __name__ == "__main__":
    main()

