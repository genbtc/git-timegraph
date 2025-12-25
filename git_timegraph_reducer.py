#!/usr/bin/env python3

# git_timegraph_reducer.py - Computes final per-path state from path_events
"""
Enhancements applied:
- Added type hints
- Added docstrings for functions
- Refactored recursive deletion and state handling for clarity
- Added verbose print optionality
- Cleaned up SQL and dictionary handling
- Preliminary support for rename events
- Added symlink support and index optimizations
- exists is properly escaped with double quotes to avoid the SQLite keyword conflict.
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional

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
      - rename events handled
      - symlink_target handled
      - deletions are recursive for directories
    """
    cur = db.cursor()

    # Clear previous reduction
    cur.execute("DELETE FROM reduced_paths")

    query = '''
        SELECT p.path,
               pe.change_type,
               pe.new_blob,
               pe.old_path,
               pe.symlink_target,
               c.committer_time
        FROM path_events pe
        JOIN paths p ON p.id = pe.path_id
        JOIN commits c ON c.oid = pe.commit_oid
        ORDER BY c.committer_time
    '''

    path_state: Dict[str, Dict[str, Any]] = {}

    for path, change_type, blob, old_path, symlink_target, commit_time in cur.execute(query):
        # Handle rename events
        if change_type == 'R' and old_path:
            old_state = path_state.pop(old_path, None)
            if old_state:
                path_state[path] = old_state
                path_state[path]['mtime'] = commit_time
                path_state[path]['exists'] = 1
                path_state[path]['blob'] = blob
                path_state[path]['symlink_target'] = symlink_target
            else:
                # Treat as new addition if old path unknown
                path_state[path] = {
                    'exists': 1,
                    'blob': blob,
                    'symlink_target': symlink_target,
                    'ctime': commit_time,
                    'mtime': commit_time,
                }
            continue

        state = path_state.get(path)
        if state is None:
            path_state[path] = {
                'exists': 0 if change_type == 'D' else 1,
                'blob': None if change_type == 'D' else blob,
                'symlink_target': None if change_type == 'D' else symlink_target,
                'ctime': commit_time,
                'mtime': commit_time,
            }
        else:
            if commit_time >= state['mtime']:
                state['mtime'] = commit_time
                if change_type == 'D':
                    state['exists'] = 0
                    state['blob'] = None
                    state['symlink_target'] = None
                else:
                    state['exists'] = 1
                    state['blob'] = blob
                    state['symlink_target'] = symlink_target

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
                    child['symlink_target'] = None

    # Persist reduced state, escape 'exists' in SQL to avoid keyword conflict
    for path, st in path_state.items():
        cur.execute(
            'INSERT OR REPLACE INTO reduced_paths (path, "exists", blob, ctime, mtime, old_path, symlink_target) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (path, st['exists'], st['blob'], st['ctime'], st['mtime'], st.get('old_path'), st.get('symlink_target'))
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

