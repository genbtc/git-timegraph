PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS commits (
	oid TEXT PRIMARY KEY,
	committer_time INTEGER NOT NULL,
	author_time INTEGER NOT NULL,
	parent_oids TEXT NOT NULL,
	tree_oid TEXT NOT NULL,
	message TEXT
);

CREATE TABLE IF NOT EXISTS paths (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	path TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS path_events (
	path_id INTEGER NOT NULL,
	commit_oid TEXT NOT NULL,
	commit_time INTEGER NOT NULL,
	old_blob TEXT,
	new_blob TEXT,
	change_type TEXT NOT NULL,
	old_path TEXT,
	symlink_target TEXT,
	FOREIGN KEY(path_id) REFERENCES paths(id),
	FOREIGN KEY(commit_oid) REFERENCES commits(oid),
	PRIMARY KEY (path_id, commit_oid)
);

CREATE TABLE IF NOT EXISTS reduced_paths (
	path TEXT PRIMARY KEY,
	"exists" INTEGER NOT NULL,
	blob TEXT,
	ctime INTEGER NOT NULL,
	mtime INTEGER NOT NULL,
	old_path TEXT,
	symlink_target TEXT
);

-- Indexes for faster lookup
CREATE INDEX IF NOT EXISTS idx_reduced_paths_path ON reduced_paths(path);
CREATE INDEX IF NOT EXISTS idx_reduced_paths_old_path ON reduced_paths(old_path);

CREATE TABLE IF NOT EXISTS meta (
	key TEXT PRIMARY KEY,
	value TEXT
);
