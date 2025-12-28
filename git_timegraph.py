#!/usr/bin/env python3

# git_timegraph.py - main entry (V1 plumbing) updated to match reducer/writer
"""
Now implements Option 1: symlink detection via git object mode 120000.
Populates symlink_target in path_events; blob is NULL for symlinks.
"""

import subprocess
import sqlite3
import sys
from pathlib import Path
from typing import List, Tuple, Optional

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"
PLUMBING = BASE_DIR / "git_plumbing.sh"


def sh(cmd: str, cwd: Optional[Path] = None) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.PIPE, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}\n{e.stderr}")
        sys.exit(1)


def init_db(db: sqlite3.Connection) -> None:
    with open(BASE_DIR / "schema.sql") as f:
        db.executescript(f.read())


def get_or_create_path(db: sqlite3.Connection, path: str) -> int:
    cur = db.execute("SELECT id FROM paths WHERE path = ?", (path,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur = db.execute("INSERT INTO paths(path) VALUES (?)", (path,))
    return cur.lastrowid


def parse_commit(meta: str) -> Tuple[List[str], int, int, str, str]:
    parents = []
    author_time = None
    committer_time = None
    tree = None
    message = []

    in_message = False
    for line in meta.splitlines():
        if in_message:
            message.append(line)
            continue
        if line.startswith("parent "):
            parents.append(line.split()[1])
        elif line.startswith("author "):
            author_time = int(line.split()[-2])
        elif line.startswith("committer "):
            committer_time = int(line.split()[-2])
        elif line.startswith("tree "):
            tree = line.split()[1]
        elif line == "":
            in_message = True

    return parents, author_time, committer_time, tree, "\n".join(message)


def index_commits(db: sqlite3.Connection, repo_dir: Path, ref: str) -> List[str]:
    commits = sh(f"{PLUMBING} git_commits {ref}", cwd=repo_dir).splitlines()

    for oid in commits:
        meta = sh(f"{PLUMBING} git_commit_meta {oid}", cwd=repo_dir)
        parents, atime, ctime, tree, msg = parse_commit(meta)

        db.execute(
            """
            INSERT OR IGNORE INTO commits
            (oid, committer_time, author_time, parent_oids, tree_oid, message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (oid, ctime, atime, " ".join(parents), tree, msg),
        )

    db.commit()
    return commits


def index_diffs(db: sqlite3.Connection, repo_dir: Path, commits: List[str]) -> None:
    for oid in commits:
        cur = db.execute("SELECT parent_oids, committer_time FROM commits WHERE oid = ?", (oid,)).fetchone()
        parents = cur[0].split()
        ctime = cur[1]

        if not parents:
            out = sh(f"{PLUMBING} git_root_tree {oid}", cwd=repo_dir)
            for line in out.splitlines():
                _, mode, blob, path = line.split(maxsplit=3)
                pid = get_or_create_path(db, path)
                symlink_target = None
                if mode == '120000':
                    symlink_target = sh(f"git cat-file -p {blob}", cwd=repo_dir).strip()
                    blob = None

                db.execute(
                    """
                    INSERT OR IGNORE INTO path_events
                    (path_id, commit_oid, commit_time, old_blob, new_blob, change_type, old_path, symlink_target)
                    VALUES (?, ?, ?, NULL, ?, 'A', NULL, ?)
                    """,
                    (pid, oid, ctime, blob, symlink_target),
                )
            continue

        for parent in parents:
            diff = sh(f"{PLUMBING} git_diff_tree {parent} {oid}", cwd=repo_dir)
            for line in diff.splitlines():
                if not line.startswith(":"):
                    continue
                meta, path = line.split("\t", 1)
                parts = meta.split()
                old_blob = parts[2]
                raw_new_blob = parts[3]
                new_mode = parts[1]
                change = parts[4]

                pid = get_or_create_path(db, path)
                symlink_target = None
                blob = raw_new_blob
                if new_mode == '120000':
                    symlink_target = sh(f"git cat-file -p {raw_new_blob}", cwd=repo_dir).strip()
                    blob = None

                db.execute(
                    """
                    INSERT OR IGNORE INTO path_events
                    (path_id, commit_oid, commit_time, old_blob, new_blob, change_type, old_path, symlink_target)
                    VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
                    """,
                    (pid, oid, ctime, old_blob, blob, change, symlink_target),
                )

    db.commit()


def main():
    if len(sys.argv) != 2:
        print("usage: git-timegraph <repo_dir>")
        sys.exit(1)

    repo_dir = Path(sys.argv[1]).resolve()
    if not repo_dir.is_dir():
        print(f"Error: {repo_dir} is not a directory")
        sys.exit(1)

    db = sqlite3.connect(DB_PATH)
    init_db(db)

    ref = "HEAD"
    commits = index_commits(db, repo_dir, ref)
    index_diffs(db, repo_dir, commits)

    db.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('ref', ?)" , (ref,))
    db.commit()
    db.close()

    print(f"Indexed {len(commits)} commits into {DB_PATH}")


if __name__ == "__main__":
    main()

