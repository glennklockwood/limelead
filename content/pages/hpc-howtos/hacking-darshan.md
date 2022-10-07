---
title: Hacking Darshan
shortTitle: Hacking Darshan
order: 100
---

## Introduction

[Darshan][] is a very useful profiling tool that intercepts I/O calls within HPC
applications to perform lightweight profiling.  If you are interested in using
it to profile your applications, you should see [Building and Managing
Darshan]({filename}managing-darshan.md).

This page contains notes on how Darshan works internally with an eye towards
extending its functionality.

## Global Core Initialization

The `darshan_core_initialize()` function is called at initialization (either via the GNU C constructor, or at `MPI_Init()`).  It does the following:

- check for environmental overrides (DARSHAN_MEM_ALIGNMENT_OVERRIDE, DARSHAN_JOBID_OVERRIDE, DARSHAN_MOD_MEM_OVERRIDE)
- set jobid
- malloc the core structure and structures for
  1. header (`struct darshan_header`)
  2. job metadata (`struct darshan_job`)
  3. executable name
  4. "name record buffer"
  5. module scratchpad
- populate header
- set job-level metadata (uid, start time, nprocs, jobid)
- record any MPI-IO hints specified for Darshan log output (`darshan_log_record_hints_and_ver()`)
- populate mount table (`darshan_get_exe_and_mounts()`)
- initialize static modules (`mod_static_init_fns[]` table)

## Per-module Initialization

When a wrapped function is called, it checks to see if its parent module has been initialized via a `*_PRE_RECORD` macro (e.g., `POSIX_PRE_RECORD`).

If the core is enabled and the module's runtime metadata is not, call the module's `*_runtime_initialize` function (e.g., `posix_runtime_initialize()`.

The `*_runtime_initialize()` function does

- estimate how much memory it will need
- call `darshan_core_register_module()` to trigger memory allocation which is done exclusively by the core
- bail out if the core refused to give sufficient memory
- malloc and memset the runtime metadata structure
- enable DXT if `DXT_ENABLE_IO_TRACE` is defined

Most of the magic happens in the Darshan core's `darshan_core_register_module()` which does the following:

- malloc and memset the module's metadata (`struct darshan_core_module`)
- set the module's initial offset in the Darshan heap (`mod->rec_buf_start`)
- map the module's shutdown function (`mod->mod_shutdown_func`)
- update the core's module list to reflect the addition of the new module
- pass back the actually allocated size of the buffer via the `inout_mod_buf_size` input pointer
- pass back the system memory alignment to the module via the `sys_mem_alignment` input pointer (??? which modules need this?)
- pass back the MPI rank via the `rank` input pointer

It's interesting to note that Darshan knows what modules are available at compile-time, and each module and the core has a shared understanding of each module's unique module ID.


## Global Core Finalization

The `darshan_core_shutdown()` function is called at shutdown (either via GNU C destructor or `MPI_Finalize()`).  It does the following:

- **ensure shutdown timing is synchronized** using `MPI_Barrier()`
- unplug the core (`final_core = darshan_core; darshan_core = NULL`)
- set the job end time
- **calculate the job's overall start and end times** using global min/max `MPI_Reduce()`s and commit those to the final core's job metadata
- allocate a buffer to help with log compression
- allocate a buffer to store the Darshan log path (done in heap because it needs to be shared via MPI?)
- **calculate log file path** on rank 0, then broadcast it to all nodes.  Check that everyone has a valid log path name and collectively fail if not.
- **identify modules that registered** during the app runtime across all MPI processes via `MPI_Allreduce()`
- **determine common record names** across all MPI processes (which files were opened by everyone) via `darshan_get_shared_records()`
- collectively **open log file** and collectively check for errors
- rank 0 **writes the job metadata and mount table** and leaves room for an uncompressed log header.  Check for errors and collectively fail if rank 0 failed in the aforementioned task
- **write the name->record mapping** by calling `darshan_log_write_name_record_hash()`
  - MPI ranks > 0 remove all their shared records names from the filename->record map (since they are already reduced and represented on rank0 at this point)
  - rebuild record map on rank>0 such that unique records are at the front of the list of mappings and shared records are at the end
  - then call `darshan_log_append_all()` which does a collective append
- loop through all the modules; **this is described below**
- determine which MPI ranks ran out of memory via `MPI_Reduce()`
- determine the total number of active modules (never-activated modules aren't written to the final log file)
- write the Darshan log header from rank 0 and collectively fail on error (`MPI_Bcast()` the return value of the `MPI_File_write_at()`)
- close the Darshan log file and rename it from `*.darshan_partial` to `*.darshan`

The "loop through all the modules" loop does the following:

- flags all globally never-active modules so they don't get written to the Darshan log
- set the shared record list for this module (`mod_shared_recs[]`)
- call the module's shutdown function _if_ the module was used locally.  _how does this work if a module is only used by some MPI processes?  `MPI_COMM_WORLD` is passed to the module-specific shutdown reducer which would cause a deadlock if not all modules are doing posix, right?_


All Darshan modules' shutdown functions must have the following prototype:

| argument               | intent  | meaning                                  |
|------------------------|---------|------------------------------------------|
| `MPI_Comm mod_comm`    | in      | MPI communicator to run collectives with |
| `darshan_record_id *shared_recs` | in | pointer to start of shared records  |
| `int shared_rec_count` | in      | count of shared data records             |
| `void **mod_buf`       | in/out  | pointer to start of the module's records |
| `int *mod_buf_sz`      | out     | number of records                        |

[Darshan]: https://www.mcs.anl.gov/research/projects/darshan/
