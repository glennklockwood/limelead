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

## mdtest Basics

{% call alert(type="warning") %}
Don't run mdtest without any arguments because the default behavior is to
almost do nothing.
{% endcall %}

The simplest possible mdtest run looks something like this:

    mpirun -n 1 mdtest -n 1

which will result in output that looks like this:

```
   Operation                     Max            Min           Mean        Std Dev
   ---------                     ---            ---           ----        -------
   Directory creation          43464.290      43464.290      43464.290          0.000
   Directory stat             476625.455     476625.455     476625.455          0.000
   Directory rename            95325.091      95325.091      95325.091          0.000
   Directory removal           75166.738      75166.738      75166.738          0.000
   File creation               51025.596      51025.596      51025.596          0.000
   File stat                  530924.557     530924.557     530924.557          0.000
   File read                  133152.508     133152.508     133152.508          0.000
   File removal               125203.104     125203.104     125203.104          0.000
   Tree creation               41943.040      41943.040      41943.040          0.000
   Tree removal                72315.586      72315.586      72315.586          0.000
```

What mdtest just did is the following:

### 1. Create Test Directory

mdtest first creates the test directory in which all tests for the current
iteration will run as:

    mkdir ./out/test-dir.0-0

The time it takes for this to happen is _not_ reported by mdtest.

### 2. Run Tree Creation Test Phase

There is a tree creation test that measures how long it takes to recursively
create a tree structure.  In our case, no meaningful test runs and only a single
tree is created:

    mkdir ./out/test-dir.0-0/mdtest_tree.0/

The behavior of this test is governed by the `-u` (unique directory per task)
and `-c` (collective creates) options.

### 3. Run Directory Test Phase

mdtest then performs a series of directory tests.  It first creates ten new
directories (since we specified `-n 10`):

    mkdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0
    ...
    mkdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.9

Then it calls `stat(2)` on these ten directories:

    stat ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0
    ...
    stat ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.9

Then it calls `rename(2)` each of the ten directories:

    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0 ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0-XX
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.1 ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0
    ...
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.8 ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.7
    rename ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0-XX ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.8

Then it unlinks all ten directories:

    rmdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.0
    ...
    rmdir ./out/test-dir.0-0/mdtest_tree.0/dir.mdtest.0.9

There are barriers between each of these steps after which the timing is
reported.

### 4. Run File Test Phase Phase

The file tests then commence in the same tree as the directory tests above.
Notice that whereas the directory tests created inodes called `dir.mdtest.X.Y`,
these file tests create `file.mdtest.X.Y`; the tree (`mdtest_tree.0`) remains
untouched between these phases.

There is a barrier, the timing is reported, and mdtest resumes to the next step.

#### File Creation

First is the _file creation_ test.  Ten files are opened with `_O_CREAT`, then
closed:  

    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.1
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.1
    ....
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.8
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.8
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9

There are no barriers between these opens and closes, and mdtest has an option
(`-w`) that would let us optionally write some bytes to each of these files
between each open and close.  By default nothing is written, so 0-byte files
are created here.

There is a barrier, the timing is reported, and mdtest resumes to the next step.

#### File Stat

Then `stat(2)` is called on each file:

    stat ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    ...
    stat ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9

There is a barrier, the timing is reported, and mdtest resumes to the next step.

#### File Read

Then each file is opened and closed again.  

    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    ...
    open ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9
    close /data/out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9

If we had written data to these files during the _file creation_ step, we
could have optionally read that data back out here using the `-e` parameter.
Since we didn't specify either of these parameters though, the timing reported
is just the time it takes to open each file, do nothing, then close it.

There is a barrier, the timing is reported, and mdtest resumes to the next step.

#### File Removal

Finally, each file is unlinked:

    unlink ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.0
    ...
    unlink ./out/test-dir.0-0/mdtest_tree.0/file.mdtest.0.9

There is a barrier, the timing is reported, and mdtest resumes to the next step.

### 5. Run Tree Removal Test Phase

Once both file and directory tests are finished, the tree itself is cleaned up:

    rmdir ./out/test-dir.0-0/mdtest_tree.0/

Because we didn't specify the parameters to make a directory tree, only our
single directory at the base of the tree is removed.

### 6. Destroy Test Directory

Finally, the test directory for this iteration is cleaned up:

    rmdir ./out/test-dir.0-0

The time it takes for this to happen is _not_ reported by mdtest.

[IOR]: https://github.com/hpc/ior

## Selecting Tests to Run

You can run only a subset of the phases and steps above.

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

    mpirun -n 1 mdtest -F -C -n 10

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
More concretely, if we do

    mpirun mdtest -F -C -z 3 -n 20 

We will get the following:

- `out/test-dir.0-0/mdtest_tree.0/`
    - `file.mdtest.0.0` through `file.mdtest.0.9`
    - `mdtest_tree.1/`
        - `file.mdtest.0.5` through `file.mdtest.0.19`
        - `mdtest_tree.2/`
            - `file.mdtest.0.10` through `file.mdtest.0.17`
            - `mdtest_tree.3/`
                - `file.mdtest.0.15` through `file.mdtest.0.19`

If you specify a number of items (`-n`) that is not evenly divisible _depth_ + 1
(`-z` + 1), the number of items will be rounded down so that every directory
contains an identical number of items.
