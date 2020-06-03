---
title: Parallel I/O Benchmarks
---

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
