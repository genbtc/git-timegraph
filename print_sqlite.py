#!/usr/bin/env python3
import sqlite3
from pathlib import Path
# Use absolute paths relative to this script for robustness
BASE_DIR = Path(__file__).parent.resolve()
db = sqlite3.connect(str(BASE_DIR / "timegraph.sqlite"))
for row in db.execute("""
    SELECT p.path, c.committer_time, pe.change_type
    FROM path_events pe
    JOIN paths p ON p.id = pe.path_id
    JOIN commits c ON c.oid = pe.commit_oid
    ORDER BY c.committer_time
"""):
    print(row)
