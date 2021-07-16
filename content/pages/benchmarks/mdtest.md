---
title: Getting Started with mdtest
shortTitle: mdtest
---

mdtest is a simple I/O benchmarking tool that is now a part of the [IOR][]
suite of tools that issues a highly concurrent stream of metadata operations to
a storage system.  It is designed to demonstrate the peak rate at which a file
system is able to service operations including mkdir, stat, rmdir, creat, open,
close, and unlink.

When interpreting mdtest results, it is critical to realize that the peak
overall capability of a file system's metadata subsystem is not the sum of
each metadata operation's peak rate.  This makes understanding metadata
capability more difficult because

1. there are many more types of metadata operations (open, close, stat, unlink,
   ...) than data operations (read and write), and
2. the relative costs to service these metadata operations can vary widely
   (e.g., the CPU and disk overhead of an unlink vs. a stat)

[IOR]: https://github.com/hpc/ior

## mdtest Basics

The simplest possible mdtest run looks something like this:

    mpirun -n 2 mdtest -n 10

which will result in output that looks like this:

```
SUMMARY rate: (of 1 iterations)
   Operation                     Max            Min           Mean        Std Dev
   ---------                     ---            ---           ----        -------
   Directory creation          13936.880      13936.880      13936.880          0.000
   Directory stat              58661.594      58661.594      58661.594          0.000
   Directory rename            24125.994      24125.994      24125.994          0.000
   Directory removal           20365.642      20365.642      20365.642          0.000
   File creation               24392.579      24392.579      24392.579          0.000
   File stat                   50747.780      50747.780      50747.780          0.000
   File read                   36759.895      36759.895      36759.895          0.000
   File removal                50261.282      50261.282      50261.282          0.000
   Tree creation                2673.234       2673.234       2673.234          0.000
   Tree removal                 6168.094       6168.094       6168.094          0.000
```

From these results, we can see that mdtest runs in several _phases_:

1. **Tree creation** - create the directory structure in which subsequent tests
   will be run (the "_tree_")
2. **Directory tests** - test how fast _directories_ can be
   created/statted/renamed/destroyed
3. **File tests** - test how fast _files_ can be created/statted/read/destroyed
4. **Tree removal** - remove the directory structure (the _tree_)

The _directory test phase_ and _file test phase_ are comprised of individual
_steps_, and each step and phase are surrounded by barriers.

## Test Phases in Detail

{% call alert(type="warning") %}
Don't run mdtest without any arguments.  The default behavior is to do
nothing except create the tree where tests would normally run.
{% endcall %}

Let's walk through exactly what happens when you run the simplest case:

    mpirun -n 2 mdtest -n 10

First, mdtest creates the test directory in which all tests for the current
iteration will run as:

    mkdir ./out/test-dir.0-0

The time it takes for this to happen is _not_ reported by mdtest.

### Tree Creation

The tree creation test measures how long it takes to recursively create the
test's directory tree structure.  In our case, only a single tree with a base
directory is created:

    mkdir ./out/test-dir.0-0/mdtest_tree.0/

Note that the tree creation is always performed by rank 0, not in parallel.

### Directory Tests

mdtest then performs a series of directory tests.

First is the **directory creation step** which creates ten new
directories for each MPI rank (since we specified `-n 10`):

    mkdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0
    mkdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.0
    ...
    mkdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.9
    mkdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.9

Each directory is named `dir.mdtest.X.Y` where `X` is the MPI rank that created
the directory and `Y` ranges from 0 to `-n` minus one.

Then the **directory stat step** calls `stat(2)` on these twenty
directories:

    stat ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0
    stat ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.0
    ...
    stat ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.9
    stat ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.9

The MPI rank that created the directory is also the one that stats it here, but
we can control this behavior using the `-N` argument later.

The **directory rename step** follows and calls `rename(2)` on each of the
twenty directories:

    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0 ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0-XX
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.0 ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.0-XX
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.1 ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.1 ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.0
    ...
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.8 ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.7
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.8 ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.7
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0-XX ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.8
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.0-XX ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.8

The final step is the **directory removal step** which unlinks all twenty
directories:

    rmdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0
    rmdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.0
    ...
    rmdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.9
    rmdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.1.9

### File Tests

The file tests then commence in the same tree as the directory tests above.
Notice that these file tests create `file.mdtest.X.Y` whereas the directory
tests created inodes called `dir.mdtest.X.Y`.  The `X` and `Y` have the same
meaning in file tests as the directory tests above, and the tree
(`mdtest_tree.0`) remains untouched between these phases.

First is the **file creation step**.  Ten files per MPI rank are opened with
`O_CREAT`, then closed:  

    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.0
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.0
    ...
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.9
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.9

There are no barriers between these opens and closes, and mdtest has an option
(`-w`) that would let us optionally write some bytes to each of these files
between each open and close.  As such, the "file creation" can be thought of as
the rate at which a storage system can create files of an arbitrary size.
By default nothing is written (`-w 0` is implicit), so 0-byte files are created
in this example.

Next is the **file stat step** where `stat(2)` is called on each file:

    stat ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    stat ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.0
    ...
    stat ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9
    stat ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.9

The **file read step** follows and each file is opened and closed again.  

    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.0
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.0
    ...
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.9
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.1.9

If we had written data to these files during the file creation step, we
could have optionally read that data back out here using the `-e` parameter.
Since we didn't specify either `-w` or `-e` though, the timing reported
is just the time it takes to open each file, do nothing, then close it.

Finally, the **file removal step** unlinks each file created in this phase.

    unlink ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    ...
    unlink ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9

### Tree Removal

Once both file and directory tests are finished, the tree itself is cleaned up:

    rmdir ./out/test-dir.0-0/mdtest_tree.0/

We only had one directory as our tree, but trees can get more complicated
as we'll see below.  And as with tree creation, tree removal is serial and
always performed by rank 0.

Once this final phase is complete, the test directory for this iteration is
cleaned up:

    rmdir ./out/test-dir.0-0

The time it takes for this to happen is _not_ reported by mdtest.

## Selecting Phases and Steps

You can also choose to run a subset of the phases and steps above.

### Phase Selection

The tree tests (Tree Creation and Tree Removal) always run since file and
directory tests must run within a tree.

- `-F` runs only file tests and omits directory tests.
- `-D` runs only directory tests and omits file tests.

The default is both `-D -F`.

### Step Selection

You can also run a subset of test steps (create, stat, and removal) within each
phase.  If you specify one or more test steps, the others are disabled and will
just report rates of 0.0000.

- `-C` runs only creation steps for each phase
- `-T` runs only stat steps for each phase.  If used without `-C`, you will get
  a bunch of warnings about failed stat commands because there are no files or
  directories to stat.
- `-E` runs only the read step for the file test phase (mdtest doesn't
  implement any notion of 'reading' a directory).  If used without `-C`, you
  will crash out since there are no files to read.
- `-r` runs only removal steps for each phase.  If used without `-C`, you will
  get a bunch of warnings about failed stat commands because there are no
  files or directories to stat. 

You can mix and match these options to do things such as

    mpirun -n 2 mdtest -F -C -n 10

which will only test file creation rates.  It will also leave behind a bunch of
files in `./out` which you can inspect.

## Configuring the Tree

In our simple sample, the Tree Creation phase seemed pretty trivial because it
only created a single directory.  However you can make mdtest spread our ten
files across multiple directories using a couple different methods.

### Depth (-z)

The depth parameter (`-z`) controls how many subdirectories should be nested
below the base of our tree.  The default is 0, meaning all files/dirs are
created in the tree base (`./out/test-dir.0-0/mdtest_tree.0/`).  Setting this
to `-z 1` results in the following tree:

- `out/test-dir.0-0`
    - `mdtest_tree.0`
        - `mdtest_tree.1`

and `-z 3` results in the following:

- `out/test-dir.0-0/`
    - `mdtest_tree.0/`
        - `mdtest_tree.1/`
            - `mdtest_tree.2/`
                - `mdtest_tree.3/`

Files/directories then get evenly spread across all four of these tree levels.
So if we do

    mpirun -n 2 mdtest -F -C -z 3 -n 20 

We will get the following:

- `out/test-dir.0-0/mdtest_tree.0/`
    - **ten** files: `file.mdtest.0.0` through `file.mdtest.1.4`
    - **one** directory:`mdtest_tree.1/`
        - **ten** files: `file.mdtest.0.5` through `file.mdtest.1.9`
        - **one** directory: `mdtest_tree.2/`
            - **ten** files: `file.mdtest.0.10` through `file.mdtest.1.14`
            - **one** directory: `mdtest_tree.3/`
                - **ten** files: `file.mdtest.0.15` through `file.mdtest.1.19`

We created three nested directories under the root of our tree (`-z 3`) and a
total of forty files (`-n 20` and two MPI processes) broken into groups of ten
(five per MPI rank) evenly spread across four directories (our tree base plus
`-z 3`).

If you specify a number of items (`-n`) that is not evenly divisible _depth_ + 1
(`-z` + 1), the number of items will be rounded down so that every directory
contains an identical number of items.

### Branching Factor (-b)

The above example creates a very skinny tree, but we can create more branches
for each level of the tree by specifying a _branching factor_ using `-b`.  The
default is `-b 1`, but if we set it to `-b 2`:

    mpirun -n 2 mdtest -F -C -z 3 -b 2 -n 20

we get a tree that looks like

- `out/test-dir.0-0/mdtest_tree.0/`
    - `mdtest_tree.1/`
        - `mdtest_tree.3/`
            - `mdtest_tree.7/`
            - `mdtest_tree.8/`
        - `mdtest_tree.4/`
            - `mdtest_tree.9/`
            - `mdtest_tree.10/`
    - `mdtest_tree.2/`
        - `mdtest_tree.5/`
            - `mdtest_tree.11/`
            - `mdtest_tree.12/`
        - `mdtest_tree.6/`
            - `mdtest_tree.13/`
            - `mdtest_tree.14/`

So at each of our three levels of depth (`-z 3`), we now have two branches
(`-b 2`) and, as before, the number of items (`-n`) are evenly spread across
everything and rounded down to ensure that every directory contains the same
number of items.  In the above case with `-n 20`, our tree is so heavily
branched that we can only create two files (one per MPI rank) in each directory
of our tree.

Once you have decided on a suitable tree, the _number of items_ should be a
multiple of _depth_ &#215; _branching factor_

### Leaf-only Mode (-L)

If you'd rather only create files/directories in the outermost level of the tree
rather than at every level, use the `-L` parameter.

    mpirun -n 2 mdtest -F -C -z 3 -b 2 -L -n 20

This results in the same tree structure as above, but it spreads the files as

- `out/test-dir.0-0/mdtest_tree.0/`
    - `mdtest_tree.1/`
        - `mdtest_tree.3/`
            - `mdtest_tree.7/`
                - `file.mdtest.0.14` and `file.mdtest.1.14`
                - `file.mdtest.0.15` and `file.mdtest.1.15`
            - `mdtest_tree.8/`
                - `file.mdtest.0.16` and `file.mdtest.1.16`
                - `file.mdtest.0.17` and `file.mdtest.1.17`
        - `mdtest_tree.4/`
            - `mdtest_tree.9/`
                - `file.mdtest.0.18` and `file.mdtest.0.19` 
                - `file.mdtest.0.19` and `file.mdtest.1.19`
            - `mdtest_tree.10/`
                - `file.mdtest.0.20` and `file.mdtest.1.20`
                - `file.mdtest.0.21` and `file.mdtest.1.21`
    - `mdtest_tree.2/`
        - `mdtest_tree.5/`
            - `mdtest_tree.11/`
                - `file.mdtest.0.22` and `file.mdtest.1.22`
                - `file.mdtest.0.23` and `file.mdtest.1.23`
            - `mdtest_tree.12/`
                - `file.mdtest.0.24` and `file.mdtest.1.24`
                - `file.mdtest.0.25` and `file.mdtest.1.25`
        - `mdtest_tree.6/`
            - `mdtest_tree.13/`
                - `file.mdtest.0.26` and `file.mdtest.1.26`
                - `file.mdtest.0.27` and `file.mdtest.1.27`
            - `mdtest_tree.14/`
                - `file.mdtest.0.28` and `file.mdtest.1.28`
                - `file.mdtest.0.29` and `file.mdtest.1.29`

Again, our request for twenty items (`-n 20`) was rounded down to sixteen per
MPI process so that each leaf node would get the same number of files.

## Example Configurations

Here are some example mdtest configurations drawn from real-world use cases that
I've come across.

### IO500

The IO500 benchmark contains several mdtest runs.

mdtest-hard does

Option   | Purpose
---------|---------
-n #     | create # files/dirs per MPI process
-F       | only perform file tests
-P       | print both metadata rate and raw timings
-N 1     | do not read (`-e`) from the same node that wrote (`-w`)
-d X     | run test in directory X
-x X     | save stonewall progress from create phase to file named X
-t       | "time unique working directory overhead" (what does this mean?)
-w 3901  | write 3901 bytes to the file after it is created
-e 3901  | read 3901 bytes from each file after it is created

All parts of the mdtest-easy test do

Option   | Purpose
---------|---------
-n #     | create X files/dirs per MPI process
-F       | only perform file tests
-P       | print both metadata rate and raw timings
-N 1     | do not read (`-e`) from the same node that wrote (`-w`)
-d X     | run test in directory X
-x X     | save stonewall progress from create phase to file named X
-u       | each MPI process gets its own directory
-L       | only create files in leaf directories

And the following arguments are appended to run the different phases of mdtest-easy:

Phase              | Extra Args | Purpose
-------------------|------------|------
mdtest-easy-write  | -C -Y -W # | run create step, sync after every phase, and stonewall for # seconds
mdtest-easy-stat   | -T         | run stat step
mdtest-easy-delete | -r         | run removal step

### NERSC Acceptance Tests

The following tests were run on NERSC's Cori system as part of its file system
acceptance.  These arguments were used with a much older version of mdtest
(1.8.3) but the functionality is the same.

**Testing multiple files in a single directory**:

Option   | Purpose
---------|---------
-n 20    | create 20 files/dirs per MPI process
-i 3     | run each test three times
-F       | only perform file tests
-C       | run create step
-T       | run stat step
-r       | run removal step
-N 32    | files created by rank X are statted by rank X + 32
-v       | increase verbosity

**Testing multiple files in multiple directories**.  Note that multiple output
directories were specified here to allow one mdtest run to exercise multiple
metadata servers configured using Lustre DNE Phase 1 (remote directories):

Option   | Purpose
---------|---------
-n 20    | create 20 files/dirs per MPI process
-i 2     | run each test twice
-F       | only perform file tests
-C       | run create step
-T       | run stat step
-r       | run removal step
-u       | each MPI process gets its own directory
-v       | increase verbosity
-d ...   | specify multiple output directories

The exact argument specified for the `-d` option was:

```
-d $SCRATCH/mdt0/d1@$SCRATCH/mdt1/d2@$SCRATCH/mdt0/d3@$SCRATCH/mdt2/d4@$SCRATCH/mdt0/d5@$SCRATCH/mdt3/d6@$SCRATCH/mdt0/d7@$SCRATCH/mdt4/d8
```

**Testing a single file in a single directory**.  This test measured how well
access to a single file performed by creating a file and then statting it using
thousands of compute nodes.

Option   | Purpose
---------|---------
-n 1     | create one file per MPI process
-S       | use shared-file access (create one file, stat it with all ranks, then remove it)
-i 3     | run each test three times
-F       | only perform file tests
-C       | run create step
-T       | run stat step
-r       | run removal step
-N 32    | files created by rank X are statted by rank X + 32
-v       | increase verbosity

This is a strange run because the only meaningful metric is the _file stat_
rate; the other phases (create/removal) reflect rank 0 creating and removing the
single shared file.
