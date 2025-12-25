#!/usr/bin/env python3

# git_timegraph.py - main entry (V1 plumbing) updated to match reducer/writer

import subprocess
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "timegraph.sqlite"
PLUMBING = BASE_DIR / "git_plumbing.sh"


def sh(cmd, cwd=None):
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.PIPE, cwd=cwd)


def init_db(db):
    with open(BASE_DIR / "schema.sql") as f:
        db.executescript(f.read())


def get_or_create_path(db, path):
    cur = db.execute("SELECT id FROM paths WHERE path = ?", (path,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur = db.execute("INSERT INTO paths(path) VALUES (?)", (path,))
    return cur.lastrowid


def parse_commit(meta):
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


def index_commits(db, repo_dir, ref):
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


def index_diffs(db, repo_dir, commits):
    for oid in commits:
        cur = db.execute("SELECT parent_oids, committer_time FROM commits WHERE oid = ?", (oid,)).fetchone()
        parents = cur[0].split()
        ctime = cur[1]

        if not parents:
            out = sh(f"{PLUMBING} git_root_tree {oid}", cwd=repo_dir)
            for line in out.splitlines():
                _, _, blob, path = line.split(maxsplit=3)
                pid = get_or_create_path(db, path)
                db.execute(
                    """
                    INSERT OR IGNORE INTO path_events
                    (path_id, commit_oid, commit_time, old_blob, new_blob, change_type)
                    VALUES (?, ?, ?, NULL, ?, 'A')
                    """,
                    (pid, oid, ctime, blob),
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
                new_blob = parts[3]
                change = parts[4]

                pid = get_or_create_path(db, path)

                db.execute(
                    """
                    INSERT OR IGNORE INTO path_events
                    (path_id, commit_oid, commit_time, old_blob, new_blob, change_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (pid, oid, ctime, old_blob, new_blob, change),
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

