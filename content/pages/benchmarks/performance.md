---
title: Historical Performance Benchmarks
shortTitle: Performance Benchmarks
---

## Introduction

The specific benchmark used was a molecular dynamics simulation which involved
simulating a calcium aluminosilicate glass consisting of 6500 atoms at room
temperature under atmospheric pressure for 25,000 timesteps, or 25ps. The
radial cutoff distance was 5.5 Å. All of the data was able to fit into the
physical RAM of each system, resulting in no swapping. However, the simulation
code used tabulates the potentials and forces rather than recalculating them
at each time step, making the performance depend heavily on memory performance
(latency and bandwidth) and the cache hierarchy in addition to floating point
arithmetic.

All binaries were compiled with optimizations for the platform on which the
benchmark was being run, including any special SIMD instruction sets that the
compiler could generate on its own. There are differences in the optimizations
performed by the compilers, but I've tried to use each compiler's most
sensible set of optimization options.  To see the exact options I used for
each benchmark, in addition to a plethora of other metadata, you can view the
raw data used to generate this page in [my website's git repository].

<div class="d-none d-md-block">
Here is a graphical respresentation of the performance data:
<div id="barchart" style="width: 100%; height: 700px; margin-bottom: 1rem"></div>
</div>

Some measurements below also have an "Optimized Time" column.  This measurement
was made on a version of the application that periodically sorts the atomic
positions in memory to increase cache hit rate.  Because this optimization was
not available at the time I started doing these benchmarks, many of the older
systems do not have it.

## SPARC Processors

<div class="benchmark-table" data-isa="sparc"></div>

## MIPS Processors

<div class="benchmark-table" data-isa="mips"></div>

## POWER/PowerPC Processors

<div class="benchmark-table" data-isa="power"></div>

## PA-RISC Processors

<div class="benchmark-table" data-isa="parisc"></div>

## Itanium Processors

<div class="benchmark-table" data-isa="ia64"></div>

## ARM Processors

<div class="benchmark-table" data-isa="arm"></div>

## x86 Processors

<div class="benchmark-table" data-isa="x86"></div>

<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script src="benchmark-plot.js"></script>
<script src="benchmark-tables.js"></script>

[my website's git repository]: https://github.com/glennklockwood/limelead/tree/master/content/data/benchmarks
