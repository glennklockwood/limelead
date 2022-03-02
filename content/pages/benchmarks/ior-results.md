---
title: Parallel I/O Benchmarks
---

This page started as a place for me to keep track of the acceptance test
parameters were used to obtain the hero numbers on the file systems on which
I've worked, but it's evolving into a page on how to think about crafting
acceptance tests for parallel file systems.

Skip straight to the [Perlmutter](#perlmutter) section to see more musings on
_why_ the parameters used were chosen; I wrote the acceptance criteria for that
file system and remember why I did what I did.

## Cori

The Cori acceptance test for both the Lustre file system (cscratch) and the
burst buffer used IOR to obtain the peak numbers that were advertised.

### Lustre Phase I

For the peak Lustre performance (Phase I), we did

```
./IOR -w -a POSIX -F -C -e -g -k -b 4m -t 4m -s 1638 -o $SCRATCH/IOR_file -v
```

- 960 nodes, 4 processes per node
- 4 MiB transfer and block size
- 24 TiB total write size (which determined the segment count)
- -w and -r were run as separate sruns (to ensure cache was dropped)

```
./IOR -w -a MPIIO -c -C -g -b 8m -t 8m -k -H -v -s $((12*1024*1024/8/(960*32))) -o $SCRATCH/IOR_file
```

- 960 nodes, 32 processes per node
- 8 MiB transfers and block size
- 12 TiB total write size
- -w and -r run separately
- collective buffering explicitly disabled
- stripe size set to 8 MiB
- stripe count set to the total number of OSTs, from `lfs df $SCRATCH`

To summarize:

- 716,886.15 MiB/sec (POSIX file-per-process write)
- 646,835.37 MiB/sec (POSIX file-per-process read)
- 344,016.32 MiB/sec (MPI-IO shared-file write)
- 614,328.95 MiB/sec (MPI-IO shared-file read)

### Lustre Phase II

The same tests were performed at Phase II acceptance, but the Lustre
performance was diminished due to filling of OSTs.  To summarize, 960 nodes
gave:

- 562,701.01 MiB/sec (POSIX file-per-process write, KNL with 8 ppn, buffered I/O)
- 389,576.59 MiB/sec (POSIX file-per-process read, KNL with 8 ppn, buffered I/O)
- 624,666.33 MiB/sec (POSIX file-per-process write, KNL with 8 ppn, direct I/O)
- 397,262.65 MiB/sec (POSIX file-per-process read, KNL with 8 ppn, direct I/O)
- 478,170.92 MiB/sec (POSIX file-per-process write, Haswell with 4 ppn) - 66% of the Phase I acceptance
- 346,969.69 MiB/sec (POSIX file-per-process read, Haswell with 4 ppn) - 53% of the Phase I acceptance

There were no peak I/O numbers for MPI-IO shared-file I/O for Phase 2.

### DataWarp Phase I

DataWarp Phase I used 4480 processes (ppn=4) with the following IOR
command-line options:

- `./IOR -a MPIIO -g -t 512k -b 8g -o $DW_JOB_STRIPED/IOR_file -v`
- `./IOR -a POSIX -F -e -g -t 512k -b 8g -o $DW_JOB_STRIPED/IOR_file -v`
- `./IOR -a POSIX -F -e -g -t 4k -b 1g -o $DW_JOB_STRIPED/IOR_file -v -z`

To summarize,

- 832,451.89 MiB/sec (POSIX file-per-process write)
- 862,616.35 MiB/sec (POSIX file-per-process read)
- 334,627.84 MiB/sec (MPI-IO shared-file write)
- 765,847.30 MiB/sec (MPI-IO shared-file read)
- 12,527,427.06 IOP/sec (POSIX file-per-process write)
- 12,591,977.74 IOP/sec (POSIX file-per-process read)

### DataWarp Phase II

The Phase II IOR runs used between 44,000 and 44,080 processes (again, ppn=4) with the following IOR command-line options:

- `./IOR -a POSIX -F -e -g -t 1M -b 8G -o $DW_JOB_STRIPED/IOR_file -v`
- `./IOR -a MPIIO -g -t 1M -b 8G -o $DW_JOB_STRIPED/IOR_file -v`
- `./IOR -a POSIX -F -e -g -t 4k -b 1g -o $DW_JOB_STRIPED/IOR_file -v -z`

To summarize, the peak numbers were

- 1,493,373.74 MiB/sec (POSIX file-per-process write)
- 1,663,914.47 MiB/sec (POSIX file-per-process read)
- 1,300,578.87 MiB/sec (MPI-IO shared-file write; independent I/O)
- 1,259,295.00 MiB/sec (MPI-IO shared-file read; independent I/O)
- 13,135,292.56 IOP/sec (POSIX file-per-process write)
- 28,260,132.42 IOP/sec (POSIX file-per-process read)

## Community File System

### Phase I

The CFS Phase I file system was composed of seven IBM ESS GL8c appliances.
Access between clients and servers was via FDR InfiniBand.

The IOPS test was run using

```
mpirun -n 184 --map-by node ./ior -w -r -z -e -C -F -t 4k -b 1g -o /global/cfs/iorfpprandfile
```

- 28 nodes, 8 processes per node
- 4 KiB transfers
- 1 GiB blocks
- 184 GiB total output size
- random offsets, file-per-process access

The peak results were

- 551,934.28 write operations/sec
- 423,413.67 read operations/sec

The full performance test was run using

```
mpirun -n 408 --map-by node ./ior -w -r -e -C -F -t 1024k -b 32g -o /global/cfs/iorfppseqfile1MiB
```

- 51 nodes, 8 processes per node
- 1 MiB transfers
- 32 GiB blocks
- 12.75 TiB total output size
- sequential, file-per-process access

The peak results were

- 184,743.00 MiB/sec (POSIX file-per-process write)
- 155,214.17 MiB/sec (POSIX file-per-process read)

## Perlmutter

Perlmutter has a 36 petabyte all-flash Lustre file system composed of 274 OSSes
and 16 MDSes.

### Lustre Phase 1

There were bandwidth and IOPS tests run for Perlmutter's file system acceptance.

#### Bandwidth

Bandwidth tests used 1,382 compute nodes and 4 processes per node.  The node
count was dictated by the requirement that 90% of compute nodes could achieve
high performance.  We didn't require 100% of compute nodes because, in practice,
it's hard to get every single node up and running during the acceptance period
since hardware is still new.

The **write bandwidth** test was run as

```
srun ./ior -w -t 1m -b 1m -s 100000 -a POSIX -F -e -g -vv -C -o /pscratch/IOR-strided.out -D 45
```

This resulted in a bandwidth of 3,427,179.21 MiB/s.  Notably, I was able to
observe significantly higher write bandwidth by playing tricks; for example, 
running using 1,024 nodes, 4 processes per node, and a significantly higher
transfer size:

```
srun ./ior -w -F -e -g -vv -O lustrestripecount=1 -t 64m -b 64g -D 45 -k -o /global/homes/g/glock/testFile
```

yielded 4,435,971.20 MiB/s.  These larger transfer sizes better utilize
parallelization in RPCs which can increase overall performance, and I don't know
what the upper limit for the Phase 1 system was.

The **read bandwidth** test was run in two parts.  First, a dataset was created
that was large enough to take over 30 seconds to be read without hitting any
ends-of-file.  Once this dataset was created, it was then read using a
30-second stonewalled run:

```
# Generate dataset
srun ./ior -w -t 1m -b 1m -s 100000 -a POSIX -F -e -g -vv -C -o /pscratch/IOR-strided.out -k -O stoneWallingWearOut=1 -D 90

# Read dataset
srun ./ior -r -t 1m -b 1m -s 100000 -a POSIX -F -e -g -vv -C -o /pscratch//IOR-strided.out -k -D 30
```

The 30 seconds is significant because the acceptance criteria required that the
performance be sustained for 30 seconds.  Note that we do _not_ use stonewalling
wear-out on the second run because we are not trying to emulate the performance
of an application that was writing the same amount of data from all MPI
processes.  Instead, we were testing how much performance the file system could
sustain under any conditions.

This test resulted in a bandwidth of 3,818,284.19 MiB/s.

#### IOPS

IOPS tests used 230 nodes and 32 processes per node.  The node count reflects
15% of the compute nodes which was the requirement since it reflects the
most-likely case of a large number of small jobs all bursting random(ish) data
to and from the file system at once.  Like the bandwidth tests, this was not
intended to emulate a single application's I/O pattern; it was meant to
demonstrate the capability of the file system under duress.

The **write IOPS** test was run similar to the write bandwidth test:

```
srun ./ior -w -t 4k -z -a POSIX -F -b 16g -e -g -vv -C -D 45 -o /pscratch/IOR-random.write.out
```

There are problems with this way of testing since Lustre implements write-back
caching and random writes can be aggregated and reordered before they are sent
over the network to Lustre servers.  [There is no effective way to measure write
IOPS](https://glennklockwood.blogspot.com/2021/10/iops-are-dumb.html) so we just
ran a workload that emulated what a user would experience--write back caching
and all--and got a commensurately large number.  I would argue that this test
was not well conceived when I crafted it, but you would need a lot of clients
to drive a truly random write workload on the servers using `O_DIRECT`.

The performance from this test came back at 24,807,129.18 IOPS.

The **read IOPS** test was also run in two phases--first by generating a large
dataset to be read (using 4 MiB sequential transfers so that the dataset would
be large), then reading from it in 4 KiB transfers at random offsets:

```
# Generate dataset
srun ./ior -w -t 4m -k -a POSIX -F -b 16g -e -g -vv -C -D 45 -o /pscratch/IOR-random.read.out -O stoneWallingWearOut=1

# Read dataset
srun ./ior -r -t 4k -z -a POSIX -F -b 16g -e -g -vv -C -D 45 -o /pscratch/IOR-random.read.out
```

The performance of this test came back at 35,098,607.79 IOPS.  It's worth noting
that this test was client-limited; using more than 230 clients (15% of the total
node count) was found to drive this number significantly higher (116,434,587.92
read IOPS) using 1,024 clients.
