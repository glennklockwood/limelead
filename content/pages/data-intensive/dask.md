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
(like the one I did for [Parallel Computing with R](r/index.html)) given the
demand.

[Dask]: https://dask.org/

## Partitioning

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

## Scheduler

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

## Changing bag element granularity

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

## Memory Management and Distributed Mode

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

## Parquet

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

## pypy

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
