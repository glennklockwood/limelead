---
title: Getting Started with elbencho
shortTitle: elbencho
---

[elbencho][] is an I/O benchmarking tool developed by the illustrious Sven
Breuner to combine the best aspects of fio and IOR into a modern, flexible
I/O testing tool.  It is much friendlier to run on non-HPC parallel environments
since it does not rely on MPI for its inter-node synchronization, and it has
really nice features like a live text UI so you can watch I/O performance in
real time.  Its code base is much cleaner and nicer than IOR as well.

{% call alert(type="info") %}
This page is a work in progress; I update it as I experiment with elbencho and
learn more.
{% endcall %}

## Getting Started - Single Client

To do an fio-like write bandwidth test, I do something like this:

```bash
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

The following define the general parameters of the benchmark:

- `--threads 8` uses eight I/O threads
- `--size 1M` generates a file that is 1M (1,048,576 bytes) large
- `--block 1M` performs writes using 1M (1,048,576 bytes) transfers
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

By default, elbencho performs all I/Os to one file, analogous to the IOR
shared-file mode.  You can have elbencho create multiple files like this:


```
./bin/elbencho ./outputfile.{0..4}
```

In this case, five files (`outputfile.0`, `outputfile.1`, etc) will be created
and filled in parallel, but I'm not completely clear on what the relationship
between processes, threads and offsets in each file is.

{% call alert(type="info") %}
elbencho does not appear to designed to test metadata rates, so you should not
expect it to make millions of files or create empty files.  See [this
issue](https://github.com/breuner/elbencho/issues/28) for my notes on what
doesn't work.
{% endcall %}

## Getting Started - Multiple Clients

To run on a cluster, you need to be able to open TCP sockets between your
compute nodes.  Provided you can do that, first consult the official [Using
elbencho with Slurm](https://github.com/breuner/elbencho/blob/master/tools/slurm-examples.md)
page to get an idea of what has to happen.

At NERSC, I had to modify the provided example script to appear as follows:

```bash
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

[elbencho]: https://github.com/breuner/elbencho
