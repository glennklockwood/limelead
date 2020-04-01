---
title: Dask in Practice
shortTitle: Dask
---

These are notes I took while doing the work for a paper I wrote that analyzed a
couple hundred million log files using [Dask][].  They may seem a little salty
because I took them while struggling to get a large analysis done under severe
time constraints, but Dask is generally quite good for performing simple
analysis of large data sets at scale.

If this information is of use to anyone, please send me an e-mail and let me
know.  I could use my experience and sample dataset as the basis for a tutorial
(like the one I did for [Parallel Computing with R](../r/index.html)) given the
demand.

[Dask]: https://dask.org/

## Analyzing large data sets

### Partitioning

Dask doesn't appear to have any notion of load balancing or rebalancing;
once a dataset is partitioned (often one partition per file), that is the
granularity at which all subsequent operations will operate.  `.repartition()`
nominally allows you to coarsen partitioning, but it still doesn't really
balance anything.  For example, I had a workflow where

- 214 files were read in
- a filter was applied to subselect a tiny fraction
- the tiny fraction was written out (still as 214, mostly empty, files)

I threw in a `.repartition(4)` in there to collapse most of those empty
files, but still wound up with

- file0: 0 bytes uncompressed
- file1: 3325928 bytes uncompressed
- file2: 756776 bytes uncompressed
- file3: 9195951 bytes uncompressed

DataFrame repartitioning lets you explicitly choose how many rows you should
create per shard.  It seems like bag-based parallelism is not really that
sophisticated; we should be encouraged to use arrays or dataframes instead.

If an extremely sparse dataset is committed to file by Dask though, the
following bash one-liner will nuke all the empty ones:

    :::sh
    for i in user48964_20190701-20190801_*.json.gz
    do
        [ $(gunzip -c $i | wc -c) -eq 0 ] && rm -v "$i"
    done

### Changing bag element granularity

`.map_partition(lambda x: ...)` passes a sequence of elements as x, but returns
a concatenated bag of elements at the end.  Thus you can use this to perform
operations on fragments (which fit in memory), but you cannot use this to
reduce on fragments easily.

What you can do is `.map_partition().to_delayed()` to get a list, one per
partition, of delay objects.  You can then make an iterator over these delay
objects, e.g.,

    :::python
    partition_contents = bag.map_partition(...).to_delayed()
    per_part_iterator = [x.compute() for x in partition_contents]

then pass this iterator to another bag creator:

    :::python
    dask.bag.from_sequence(per_part_iterator)

to create a _new_ bag whose elements are each the contents of the partition of
the original bag.

For whatever reason, you cannot simply do a `.from_sequence(partition_contents)`

### Bag Blocksize

It seems like the best way to control the granularity of bag-based workflows is
to

1. Coarsen your text files to the greatest extent possible - by default this
   would be a bad idea, since the number of partitions matches the number of
  files, but then...
2. Invoke `dask.bag.read_text()` using a `blocksize=` parameter that's something
   pretty big - 128 MiB isn't bad for parallel file systems.
3. Rewrite all the data to new files - this is I/O intensive and
   space-intensive, but it does store the data in a much more analysis-friendly
   format.
4. Reload the new files so your data is partitioned into, e.g., approximately
   128 MiB files.

Fortunately the `blocksize=` parameter seems to do the right thing when
`blocksize` doesn't match where newlines form.  I convinced myself of this
using the following test:

    :::python
    import dask
    import dask.bag
    import string

    # Create a test file with differentiators around 1024-byte boundaries
    with open('testfile.txt', 'w') as testfile:
        for letter in range(0, 4):
            testfile.write(string.ascii_lowercase[2*letter] 
                           + '0' * 1022 
                           + string.ascii_lowercase[2*letter+1])

    # Iterate over a bunch of different blocksizes and ensure it does
    # not affect the data that is ultimately loaded into memory
    last_bag = None
    for blocksize in (123, 512, 768, 1024, 1536, 1537, 2048, 3096):
        this_bag = dask.bag.read_text('testfile.txt', blocksize=blocksize).compute()
        if last_bag is None:
            last_bag = this_bag
        else:
            assert(last_bag == this_bag)

This is functionally equivalent to what Hadoop does in terms of rebuilding
records (lines) that are split between two workers.

### Parquet

It looks like working with Dask DataFrames is far faster than bags, and it may
be simpler to go from as primitive of a bag to a DataFrame as possible, and then
just rebuild DataFrames when more of the unstructured part of each bag (the
transfer metadata) is needed.

Parquet seemed like a more sensible ingest format for DataFrames than bags, but
there are a lot of problems with it.  Foremost, a naive operation like

    :::python
    >>> bag.to_dataframe().to_parquet()

will fail with a cryptic

    TypeError: expected list of bytes

error.  This is because the default index created by `to_dataframe()` is not
very well defined.  So you have to

    :::python
    >>> dataframe = bag.to_dataframe()
    >>> dataframe.index = dataframe.index.astype('i8')
    >>> dataframe.to_parquet()

There are also two backends; fastparquet seems to be preferred, but it is full
of very opaque errors or silent failures.  For example, I could not get compression to work--passing no `compression=` argument, passing `compression='GZIP'`, and passing `compression='snappy'` (with the `python-snappy` conda package installed) all resulted in identically sized files, all of which are significantly larger (22 GiB) than the 4.5 GiB gzipped json source dataset.

pyarrow is the official implementation provided by the Apache foundation, but the version that Dask requires is so new that it is in neither standard conda nor conda-forge, so you effectively can't use it in a supported way within Anaconda.  As such, I really don't know how well it works.


## Configuring and using the runtime framework

### Scheduler

The distributed scheduler provides a really nice web UI for seeing what's
happening, but its strictness in enforcing memory limits can cause all manner
of artificial problems on workloads that may require a lot of memory per task.
Workers will be killed if they use more than 95% of their allotted memory, and
if a worker gets killed too many times on the same task, that task will be
blacklisted from execution and the whole collection of tasks will deadlock.

If a workload seems to be causing workers to get killed for exceeding 95% of
their memory allocation, try using a local scheduler (processes or threads).
These schedulers will do whatever they do, and even if one task blows up memory,
as long as the sum of all tasks remains within the memory limits, all will be
well.  It may be worthwhile to run workers with no memory restrictions, but I
don't know what will happen in these cases (update: turns out it works; see
below)

### Memory Management and Distributed Mode

Trying to use a lot of memory with Dask is tough.  A three-month dataset is
approximately 90 GB when encoded as uncompressed JSON.  Persisting this into
memory takes substantially more though; for example, making traces of all user
data on this dataset used approximately 1 TB of memory using 16x 128GB Haswell
nodes.

It has also been my experience that you have to leave a lot of free memory (to
keep memory pressure down), or you'll see a lot of these error:

    distributed.utils_perf - INFO - full garbage collection released 185.02 MB from 96735 reference cycles (threshold: 10.00 MB)
    distributed.core - INFO - Event loop was unresponsive in Worker for 3.30s.  This is often caused by long-running GIL-holding functions or moving large chunks of data. This can cause timeouts and instability.

And indeed, the latter one will cause Tornado timeouts and overall job failure.
Experimenting with my 90 GB dataset and its associated processing revealed that
keeping overall memory utilization at around 50% is a good place to target when
determining the resources for a task.

Python seems like a pretty terrible language for memory-intensive processing
because it is garbage-collected.  I wonder if tasks would be happier if I 
interspersed sleeps into my tasks so GC can catch up.  I guess this is what the
memory manager built into Dask distributed does; it just realizes it will
constantly leak memory, so it periodically kills leaky workers?

The memory controls operate on a per-worker basis, which prevents host memory
from being fungible between cohosted workers.  At the same time, disabling
memory management results in eventual death due to memory leaks.  As such, a
reasonable formula appears to be one worker per host, but multiple _threads_
per worker.  Setting the thresholds _high_ (e.g., 80% of a big number is still
a big number) then lets the workers periodically get killed when they leak too
much.

A reasonable set of configurables for `~/.config/dask/distributed.yaml` might
be

    :::yaml
    worker:
      memory:
        target: False
        spill: False
        pause: 0.80  # fraction at which we pause worker threads
        terminate: 0.95  # fraction at which we terminate the worker

Finally, note that `.persist()` pins stuff in memory and will result in OOM
errors.  It appears that persisted objects are not allowed to spill to disk even
if running out of memory is imminent.

### On Slurm

[NERSC's guide to using Dask][] covers the basics of running Dask within a Slurm
batch environment.  I developed an interactive workflow based on this.  First,
get an interactive job that requests the correct number of nodes (`-N 16`) and
total Dask workers to spawn (`-n 128`) for a time that's generally long enough
to run the analysis:

    $ salloc -N 16 -n 128 -t 30:00 --qos interactive

As soon as the interactive session opens, do

    $ export SCHEDULE_FILE="$SCRATCH/scheduler_${SLURM_JOB_ID}.json"

so that this job has its own unique Dask scheduler file to which subsequent Dask
analyses can connect.

I then use a standalone Bash script that instantiates the Dask runtime
environment in the Slurm job called `start_dask_slurm.sh`:

    :::bash
    #!/usr/bin/env bash

    # delete any stale scheduler files
    SCHEDULE_FILE="${SCHEDULE_FILE:-$SCRATCH/scheduler_${SLURM_JOB_ID}.json}"
    if [ -f "$SCHEDULE_FILE" ]; then
        rm -f "$SCHEDULE_FILE"
    fi
    dask-scheduler --scheduler-file "$SCHEDULE_FILE" &
    sleep 5
    echo "Scheduler file: $SCHEDULE_FILE"

This is pretty straightforward and just launches the scheduler daemon and
generates the scheduler file to which all workers will have to connect.
I stuck a `sleep 5` in there because it's tempting to launch workers right
away, but they will freak out if the dask scheduler isn't fully bootstrapped
which can take a second or two.

Then I made a second script called `add_workers.sh`:

    :::bash
    #!/usr/bin/env bash
    #
    # Starts up a Dask cluster from within a Slurm job.  Does not pass -n or -N to
    # srun, so your batch job should already have this set up correctly.
    #
    NTHREADS=1
    NPROCS=1
    MEMLIMIT=""
    INTERFACE="ipogif0" # use Aries

    SCHEDULE_FILE="${SCHEDULE_FILE:-$SCRATCH/scheduler_${SLURM_JOB_ID}.json}"

    if [ ! -z "$MEMLIMIT" ]; then
        MEMLIMIT="--memory-limit $MEMLIMIT"
    fi

    echo "Scheduler file: $SCHEDULE_FILE"
    srun python3 $(which dask-worker) --interface=$INTERFACE --nthreads $NTHREADS --nprocs $NPROCS $MEMLIMIT --scheduler-file "$SCHEDULE_FILE" &

In practice, the `NTHREADS`, `NPROCS`, and `MEMLIMIT` variables set above are
the optimal values.  Fiddling with them can lead to things hanging because too
many threads are running at once; it's easier to let `srun` inherit the right
degree of parallelism from your `salloc` command.

Having the scheduler start separately from the workers being added is handy for
those cases where your analysis crashes because it runs out of memory.  Workers
will permanently die off, leaving the scheduler still running but with no
workers.  When that happens, you can just `add_workers.sh` without having to
kill and re-run `start_dask_slurm.sh`.

To kill the entire cluster, `ps ux | grep dask-scheduler` and kill the scheduler.

To kill just the workers, you can `ps ux | grep srun` and kill the parent srun
that launched all the workers.  The scheduler will remain up, allowing you to
re-run `add_workers.sh`.

Once the cluster is running, you can run Python scripts that point to
`$SCHEDULE_FILE` environment variable we set at the very beginning.  For
example,

    :::python
    import os
    import dask
    import dask.bag
    import dask.distributed

    SCHEDULER_FILE = os.environ.get("SCHEDULER_FILE")
    if SCHEDULER_FILE and os.path.isfile(SCHEDULER_FILE):
        client = dask.distributed.Client(scheduler_file=SCHEDULER_FILE)

    bag = dask.bag.read_text(glob.glob('*.json')).map(json.loads)
    # etc etc

[NERSC's guide to using Dask]: https://docs.nersc.gov/programming/high-level-environments/python/dask/

### pypy

Dask distributed is painfully slow for fine-grained tasks.  It may be because of
the pure Python implementation of its communication stack.  Does pypi make
things any faster?

    $ conda create -n pypy pypy3.6 -c conda-forge
    $ conda activate pypy
    $ pypy3 -mensurepip
    $ pypy3 -mpip install dask ...

You seem to have to manually install all the dependencies.  For h5py,

    :::sh
    export DYLD_LIBRARY_PATH=/Users/glock/anaconda3//pkgs/hdf5-1.10.4-hfa1e0ec_0/lib
    export C_INCLUDE_PATH=/Users/glock/anaconda3//pkgs/hdf5-1.10.4-hfa1e0ec_0/include
    export LIBRARY_PATH=/Users/glock/anaconda3//pkgs/hdf5-1.10.4-hfa1e0ec_0/lib

Unfortunately, weird stuff I was doing in my analysis (specifically with
`**kwargs`) was incompatible with pypy, so I never got to do a speed comparison.
