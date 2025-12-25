# git-timegraph
git-timegraph is a utility for git plumbing to produce accurate date &amp; timestamps by walking the git commit history.
Created by genBTC @ gentoo IRC - Christmas 2025 (C) Dec 25, 2025
LICENSE falls under the AGPL3

## Usage:
```
genr8eofl@genr8too /usr/src/linux-dev/src/gentoo-public $ time ~/src/git-timegraph/git_timegraph.py .
Indexed 323 commits into /home/genr8eofl/src/git-timegraph/timegraph.sqlite
real	0m3.440s

genr8eofl@genr8too /usr/src/linux-dev/src/gentoo-public $ time ~/src/git-timegraph/git_timegraph_writer.py .
Files materialized in /home/genr8eofl/src/git-timegraph/checkout/
real	0m6.357s
```

### File Layout
```
git-timegraph/
├── LICENSE						# AGPL3 licensed
├── README.md               	# you are here
├── git_timegraph.py        	# main
├── git_plumbing.sh         	# shell git helpers
├── git_timegraph_reducer.py	# many to one reduction
├── git_timegraph_writer.py		# files materialize on disk
├── print_sqlite.py				# debug util dumps DB
├── schema.sql              	# sqlite db schema
└── timegraph.sqlite			# main database storage
```

#### Project Directory Structure (v0): 
```
    4790 Dec 25 12:49 .gitignore
   34523 Dec 25 12:04 LICENSE
    1950 Dec 25 17:37 README.md
     313 Dec 25 12:06 git_plumbing.sh
    4405 Dec 25 17:23 git_timegraph.py
    3462 Dec 25 17:20 git_timegraph_reducer.py
    2312 Dec 25 17:18 git_timegraph_writer.py
     458 Dec 25 12:06 print_sqlite.py
     776 Dec 25 12:05 schema.sql
 1273856 Dec 25 17:24 timegraph.sqlite
```

#### Architectural Design

The core pipeline is solid, deterministic, and fully functional:

Indexer (git_timegraph.py) → commits, paths, path_events

Reducer (git_timegraph_reducer.py) → reduced_paths, handles A/M/D, recursive deletion

Writer (git_timegraph_writer.py) → filesystem, handles parent/ancestor conflicts, deletions, timestamps
```
Materializing /home/genr8eofl/src/git-timegraph/checkout/selinux/useradd.te (mtime=1761525148)
Creating directory /home/genr8eofl/src/git-timegraph/checkout/selinux
Materializing /home/genr8eofl/src/git-timegraph/checkout/selinux/xevent3.te (mtime=1761525148)
Materializing /home/genr8eofl/src/git-timegraph/checkout/selinux/xfce4-interfaces.if (mtime=1761525148)
Creating directory /home/genr8eofl/src/git-timegraph/checkout/shstk
Materializing /home/genr8eofl/src/git-timegraph/checkout/shstk/shstk-txt-clang14-none-objdump-d.txt (mtime=1702750177)
Materializing /home/genr8eofl/src/git-timegraph/checkout/shstk/shstk.c (mtime=1702750177)
Materializing /home/genr8eofl/src/git-timegraph/checkout/welcome-to-gentoo.txt (mtime=1696206400)
Files materialized in /home/genr8eofl/src/git-timegraph/checkout/
```

Schema (schema.sql) → authoritative table definitions
```CREATE table blah```
