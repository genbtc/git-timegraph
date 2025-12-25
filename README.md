# git-timegraph
git-timegraph is a utility for git plumbing to produce accurate date &amp; timestamps by walking the git commit history.
Created by genBTC @ gentoo IRC - Christmas 2025 (C) Dec 25, 2025
LICENSE falls under the AGPL3

## Usage:
```
genr8eofl@genr8too ~/src/git-timegraph $ time ./git_timegraph.py /usr/src/linux-dev/src/gentoo-public
Indexed 323 commits into /home/genr8eofl/src/git-timegraph/timegraph.sqlite
real	0m3.440s
```

### File Layout
```
git-timegraph/
├── README.md               # you are here
├── git_timegraph.py        # main entry
├── git_plumbing.sh         # shell helpers
├── schema.sql              # sqlite schema
```

#### Project Directory Structure (v0): 
```
genr8eofl@genr8too ~/src/git-timegraph $ ls
   4688 Dec 25 12:04 .gitignore
  34523 Dec 25 12:04 LICENSE
    132 Dec 25 12:04 README.md
    313 Dec 25 12:06 git_plumbing.sh
   4616 Dec 25 12:08 git_timegraph.py
    458 Dec 25 12:06 print_sqlite.py
    776 Dec 25 12:05 schema.sql
 872448 Dec 25 12:10 timegraph.sqlite
```

