---
title: Getting Started with md-workbench
shortTitle: md-workbench
---

{% call alert(type="info") %}
This page remains a work in progress.
{% endcall %}

{% call alert(type="warning") %}
Do not run md-workbench with the default parameters because they reflect a
bnechmark that will run for a very long time.
{% endcall %}

Let's take a look at what a simple md-workbench does:

    mpirun -n 2 md-workbench -I 11 -P 7 -D 3

## Phase 1

Rank 0 does

- `mkdir out/0_0`
- `mkdir out/0_1`
- `mkdir out/0_2`

and rank 1 does

- `mkdir out/1_0`
- `mkdir out/1_1`
- `mkdir out/1_2`

Then rank 0 creates a bunch of files:

- `open(out/0_0/file-0, O_CREAT)`
- write 3901 bytes to this file
- close this file
- ...
- `open(out/0_0/file-6, O_CREAT)`
- write 3901 bytes to this file
- close this file

then repeat this for `out/0_1` and `out/0_2`.

Then there's a barrier.

## Phase 2

Then rank 0 does:

- `stat(out/1_0/file-0)`
- `open(out/1_0/file-0)`
- read 3901 bytes from `$WORKDIR/out/1_0/file-0` - this is an absolute path, not a relative one
- `close($WORKDIR/out/1_0/file-0)`
- `unlink(./out/1_0/file-0)`

- `open(./out/1_0/file-7, O_CREAT)`
- write 3901 bytes to `$WORKDIR/out/1_0/file-7`
- `close($WORKDIR/out/1_0/file-7)`

This is repeated for `file-0` and `file-7` in different directories for a total
of 33 times, or `-I` times `-D`.  The mapping of MPI ranks to directories/files
here is shuffled relative to Phase 1.  Stay tuned for more information on how
this shuffling is determined.

Then there's a barrier.

## Phase 3

Finally, rank 0:

- unlinks the seven files in `./out/0_0/`
- `rmdir(./out/0_0/)`

Repeat for `0_1/` and `0_2/`.

Rank 1 does the same for its directories and files from Phase 1.
