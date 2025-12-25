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
    992 Dec 25 12:52 README.md
    313 Dec 25 12:06 git_plumbing.sh
   4616 Dec 25 12:08 git_timegraph.py
   1409 Dec 25 12:23 git_timegraph_reducer.py
   3739 Dec 25 12:46 git_timegraph_writer.py
    458 Dec 25 12:06 print_sqlite.py
    776 Dec 25 12:05 schema.sql
 872448 Dec 25 12:10 timegraph.sqlite
```
