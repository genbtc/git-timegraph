#!/usr/bin/env python3

# git_timegraph_writer.py - Materialize files from reduced_paths into checkout
"""
Refactored for symlink support, correct utime handling, and verbose symlink printing.
"""

import sqlite3
import subprocess
import os
from pathlib import Path
import sys

from git_timegraph_utils import delete_path, ensure_parents, handle_rename

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"
OUTPUT_DIR = BASE_DIR / "checkout"

def materialize_files(db, output_dir: Path, repo_dir: Path, dry_run: bool = False, verbose: bool = False) -> None:
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    query = """
        SELECT path, "exists", blob, mtime, old_path, symlink_target
        FROM reduced_paths
    """

    for path, exists, blob, mtime, old_path, symlink_target in db.execute(query):
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

        if symlink_target:
            if dry_run:
                if verbose:
                    print(f"{target_path} -> {symlink_target}")
            else:
                if target_path.exists() or target_path.is_symlink():
                    delete_path(target_path, dry_run=dry_run, verbose=verbose)
                os.symlink(symlink_target, target_path)
                if verbose:
                    print(f"{target_path} -> {symlink_target}")
        else:
            if dry_run:
                if verbose:
                    print(f"Would write file {target_path}")
            else:
                content = subprocess.check_output(['git', 'cat-file', '-p', blob], cwd=repo_dir)
                with open(target_path, 'wb') as f:
                    f.write(content)
                os.utime(target_path, times=(mtime, mtime))

        if verbose and not symlink_target:
            print(f"Materializing {target_path} (mtime={mtime})")


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
    if not out.endswith('/'):
        out += '/'
    print(f"Files materialized in {out}")


if __name__ == "__main__":
    main()

