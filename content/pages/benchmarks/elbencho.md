---
title: Getting Started with elbencho
shortTitle: elbencho
---

[elbencho][] is an I/O benchmarking tool developed by the illustrious Sven
Breuner to combine the best aspects of [fio]({filename}fio.md) and
[IOR][my ior blog] into a modern, flexible I/O testing tool.  It
is much friendlier to run on non-HPC parallel environments since it does not
rely on MPI for its inter-node synchronization, and it has really nice
features like a live text UI so you can watch I/O performance in real time.
Its code base is much cleaner and nicer than IOR as well.

{% call alert(type="info") %}
This page is a work in progress; I update it as I experiment with elbencho and
learn more.
{% endcall %}

[elbencho]: https://github.com/breuner/elbencho
[my ior blog]: https://blog.glennklockwood.com/2016/07/basics-of-io-benchmarking.html

## Getting Started 

### Single Client

To do an fio-like write bandwidth test, I do something like this:

```
mkdir elbencho.seq.1M
./bin/elbencho ./elbencho.seq.1M \
    --threads 8 \
    --size 1M \
    --block 1M \
    --blockvaralgo fast \
    --blockvarpct 0 \
    --sync \
    --mkdirs \
    --write \
    --delfiles \
    --deldirs \
    --nolive
```

where all of the arguments fall into one of several groups that affect what the
benchmark actually does.

By default, elbencho performs all I/Os to one file, analogous to the IOR
shared-file mode.  With that in mind, the following define the general
parameters of the benchmark:

- `elbencho.seq.1M` is the name of the output file or directory.
- `--threads 8` uses eight I/O threads
- `--size 8M` generates a file that is 8M (8,388,608 bytes) large
- `--block 1M` performs writes using 1M (1,048,576 bytes) transfers.  Since
  we're generating an 8 MiB file using 8 threads, this test will have each
  thread write exactly 1 MiB at different offsets.
- `--blockvaralgo fast` uses the "fast" algorithm for filling the write I/O buffers with randomized data
- `--blockvarpct 0` generates new random data in 0% of the write blocks (i.e., every write will contain the same randomized data)
- `--sync` calls sync after every step of the test to ensure that we capture the performance of writing data down to persistent media

The following define what tests to actually run:

- `--mkdirs` creates a directory in which each thread creates files
- `--write` performs a write test
- `--delfiles` deletes the files created during the `--write` phase
- `--deldirs` deletes the directories created during the `--mkdirs` phase

The following affects what information is actually presented to you:

- `--nolive` disables a curses-like live update screen that pops up for long-running test phases

The order of these options is not important.  elbencho will always order the
tests in the sensible way (create dirs, create files, write files, delete files,
delete dirs).

Since we only specified one output file (`elbencho.seq.1M`), all threads will
write to one shared file.  You can have elbencho create multiple files like
this:


```
./bin/elbencho ./outputfile.{0..4}
```

In this case, five files (`outputfile.0`, `outputfile.1`, etc) will be created
and filled in parallel.  [How different threads fill different offsets in
different files is described by Sven](https://github.com/breuner/elbencho/issues/28#issuecomment-1054708665).

### Multiple Clients

To run on a cluster, you need to be able to open TCP sockets between your
compute nodes.  Provided you can do that, first consult the official [Using
elbencho with Slurm](https://github.com/breuner/elbencho/blob/master/tools/slurm-examples.md)
page to get an idea of what has to happen.

At NERSC, I had to modify the provided example script to appear as follows:

```
#!/usr/bin/env bash
#SBATCH -J elbencho
#SBATCH -C gpu
#SBATCH -t 60:00
#SBATCH -G 0
#SBATCH -A nstaff
#SBATCH -N 8
#SBATCH --tasks-per-node 1
#SBATCH --cpus-per-task 16

ELBENCHO="$HOME/src/git/elbencho/bin/elbencho"

# Build elbencho compatible list of hostnames
HOSTNAMES=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | tr "\n" ",")

# Start service on all nodes - note you have to foreground process at NERSC
# to prevent srun from falling through, thinking the task is clean, and
# killing orphaned processes.
srun $ELBENCHO --service --foreground &

# Wait for the elbencho service to actually open up its http ports.  Without
# this, the next step may attempt to connect to elbencho services that haven't
# yet initialized, resulting in failure.
sleep 5

# Run benchmark
$ELBENCHO --hosts "$HOSTNAMES" \
         --threads 16 \
         --resfile elbencho-result.$SLURM_JOBID.txt \
         --size 1t \
         --block 1m \
         --blockvaralgo fast \
         --blockvarpct 100 \
         --write \
         /vast/$USER/elbencho.data

# Quit services
$ELBENCHO --quit --hosts "$HOSTNAMES"
```

We essentially run this like a hybrid MPI+OpenMP job such that there is one
elbencho service run on each of the eight compute nodes, and that process is
responsible for spawning 16 I/O threads.  You could run one thread per service
and 16 service processes per node like a straight MPI job I suppose.

## Metadata Testing

elbencho can also perform metadata performance testing like what mdtest does.
To test the rate at which a client create empty files, do something like

```
mkdir somedirs
./bin/elbencho --threads 1 \
               --size 0 \
               --files 10000 \
               --mkdirs \
               --write \
               --delfiles \
               --deldirs \
               ./somedirs
```

This will run, using a single thread (`--threads 1`), a test where 

1. a new directory is created called `/somedirs/r0/d0/` (`--mkdirs)
2. 10,000 new files are created (`--files 10000`)
3. nothing is written to them so they stay empty (`--size 0`)
4. those files are deleted (`--delfiles`)
5. the directory structure created in step 1 is all deleted (`--deldirs`)

Like with mdtest, the `--files` argument specifies the files to create _per
parallel worker_ - so using two threads will create twice as many files and
directories:

```
mkdir somedirs
./bin/elbencho --threads 2 \
               --size 0 \
               --files 10000 \
               --mkdirs \
               --write \
               ./somedirs
```

This will create the following:

```
$ find somedirs -type d
somedirs
somedirs/r0
somedirs/r0/d0
somedirs/r1
somedirs/r1/d0

$ find somedirs/r0 -type f | wc -l
10000

$ find somedirs/r1 -type f | wc -l
10000
```

You can force all threads to create all files in a single shared directory using
the `--dirsharing` argument.  Re-running the above example with this additional
argument gives us a different directory tree:

```
$ mkdir somedirs
$ ./bin/elbencho --threads 2 \
                 --size 0 \
                 --files 10000 \
                 --mkdirs \
                 --write \
                 --dirsharing \
                 ./somedirs

...

$ find somedirs -type d
somedirs
somedirs/r0
somedirs/r0/d0

$ find somedirs/r0 -type f | wc -l
20000
```

## File Per Process

The default mode for elbencho is to perform all I/O to a single file.  This
makes sense when you consider elbencho as a replacement to fio, but it can also
aggravate performance problems caused by file system locking which may not be
desirable.

To run elbencho in file-per-process mode (in a way analogous to `ior -F`), you
can do

```
$ mkdir somedirs
$ ./bin/elbencho --threads 32 \
                 --files 1 \
                 --size 1t \
                 --block 1m \
                 --dirsharing \
                 --mkdirs \
                 --sync \
                 --write \
                 ./somedirs
```

The important parts here are

* `--threads 32` is analogous to using 32 processes per node
* `--files 1` is files **per thread, per process**.  In this case, each of our
  32 threads will each create one file and will perform I/O to it exclusively.
* `--size 1t` will make **each file** 1 TiB.  In the above case we have 32
  threads, so we will create 32 &#215; 1 TiB files (or 32 TiB total spread
  over 32 files)
 * `--dirsharing` makes each thread and process create its files in a single shared
  directory.  This isn't strictly necessary, but this makes elbencho emulate the
  behavior of IOR's `-F` (file per process) option.
 
If you are running in multiprocess mode (using `--hosts`), each thread from each
process will create the number of files specified by `--files`.  For example,

```
$ srun -N 6 -n 6 \
       --nodelist node06,node07,node08,node09,node10,node11 \
       ./bin/elbencho --service --foreground

$ mkdir somedirs

$ elbencho --hosts node06,node07,node08,node09,node10,node11 \
           --threads 32 \
           --files 1 \
           --size 1t \
           --block 1m \
           --dirsharing \
           --mkdirs \
           --sync \
           --write \
           ./somedirs
```

The above

1. Starts one elbencho service on each of six nodes (`srun -N 6 -n 6`)
2. Creates the directory in which elbencho will generate its directory tree
3. Runs a test across six nodes, each with 32 processes per node, and each
   generating a single 1 TiB file.  A total of 6 &#215; 32 &#215; 1 = 192 files will
   be created.  That's a lot of data!
