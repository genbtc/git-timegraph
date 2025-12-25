#!/usr/bin/env python3

# git_timegraph_writer.py - Materialize files from reduced_paths into checkout
"""
Refactored to use shared utilities from git_timegraph_utils.
"""
from git_timegraph_utils import delete_path, ensure_parents, handle_rename

import sqlite3
import subprocess
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"
OUTPUT_DIR = BASE_DIR / "checkout"

def materialize_files(db, output_dir: Path, repo_dir: Path, dry_run: bool = False, verbose: bool = False) -> None:
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    query = """
        SELECT path, "exists", blob, mtime, old_path
        FROM reduced_paths
    """

    for path, exists, blob, mtime, old_path in db.execute(query):
        target_path = output_dir / path

        # Handle rename using shared utility
        if old_path and old_path != path:
            old_target = output_dir / old_path
            new_target = target_path
            handle_rename(old_target, new_target, output_dir, dry_run=dry_run, verbose=verbose)

        if not exists:
            if target_path.exists():
                delete_path(target_path, dry_run=dry_run, verbose=verbose)
            continue

        ensure_parents(target_path, output_dir, dry_run=dry_run, verbose=verbose)

        if verbose:
            print(f"Materializing {target_path} (mtime={mtime})")

        if not dry_run:
            content = subprocess.check_output(['git', 'cat-file', '-p', blob], cwd=repo_dir)
            with open(target_path, 'wb') as f:
                f.write(content)
            os.utime(target_path, times=(mtime, mtime))

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Materialize Git Timegraph checkout")
    parser.add_argument('repo_dir', type=Path, help='Path to Git repository')
    parser.add_argument('--dry-run', action='store_true', help='Do not write to disk')
    parser.add_argument('--verbose', action='store_true', help='Print detailed actions')
    args = parser.parse_args()

    repo_dir = args.repo_dir.resolve()
    if not repo_dir.is_dir():
        print(f"Error: {repo_dir} is not a directory")
        sys.exit(1)

    db = sqlite3.connect(DB_PATH)
    materialize_files(db, OUTPUT_DIR, repo_dir, dry_run=args.dry_run, verbose=args.verbose)
    db.close()

    out = str(OUTPUT_DIR)
    if not out.endswith('/'):  # Use forward slash for consistency
        out += '/'
    print(f"Files materialized in {out}")

if __name__ == "__main__":
    main()

