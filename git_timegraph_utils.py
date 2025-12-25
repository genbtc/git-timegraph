#!/usr/bin/env python3

# git_timegraph_utils.py - Shared utility functions for git_timegraph reducer and writer.
"""
Currently includes rename handling.
"""

from pathlib import Path

_dry_run_created_dirs = set()

def handle_rename(old_path: Path, new_path: Path, output_dir: Path, dry_run: bool = False, verbose: bool = False) -> None:
    """Move old_path to new_path, creating parent directories as needed."""
    if old_path.exists():
        if verbose:
            print(f"Renaming {old_path} -> {new_path}")
        if not dry_run:
            ensure_parents(new_path, output_dir, dry_run=dry_run, verbose=verbose)
            old_path.rename(new_path)

def ensure_parents(target_path: Path, output_dir: Path, dry_run: bool = False, verbose: bool = False) -> None:
    """Ensure all ancestor directories exist, handle file/dir conflicts."""
    parent = target_path.parent
    ancestors = []
    while parent != output_dir.parent:
        ancestors.append(parent)
        parent = parent.parent
    for ancestor in reversed(ancestors):
        if ancestor.exists() and ancestor.is_file():
            if verbose:
                print(f"File exists where directory needed: {ancestor}, deleting")
            if not dry_run:
                delete_path(ancestor, dry_run=dry_run, verbose=verbose)
        if not ancestor.exists():
            if dry_run:
                global _dry_run_created_dirs
                if ancestor in _dry_run_created_dirs:
                    continue
                _dry_run_created_dirs.add(ancestor)
            if verbose:
                print(f"Creating directory {ancestor}")
            if not dry_run:
                ancestor.mkdir(exist_ok=True)

def delete_path(target_path: Path, dry_run: bool = False, verbose: bool = False) -> None:
    """Recursively delete file or directory."""
    if verbose:
        print(f"Deleting {target_path}")
    if dry_run:
        return
    if target_path.is_dir():
        for child in target_path.iterdir():
            delete_path(child, dry_run=dry_run, verbose=verbose)
        target_path.rmdir()
    elif target_path.exists():
        target_path.unlink()
