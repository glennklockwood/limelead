---
title: Benchmarks
date: 2015-06-21T00:00:00-07:00
parentDirs: [ benchmarks ]
---

The specific benchmark used was a molecular dynamics simulation which involved
simulating a calcium aluminosilicate glass consisting of 6500 atoms at room
temperature under atmospheric pressure for 25,000 timesteps, or 25ps. The
radial cutoff distance was 5.5 Å. All of the data was able to fit into the
physical RAM of each system, resulting in no swapping. However, the simulation
code used tabulates the potentials and forces rather than recalculating them
at each time step, making the performance depend heavily on memory performance
in addition to floating point arithmetic.

All binaries were compiled with optimizations for the platform on which the
benchmark was being run, including any special SIMD instruction sets that the
compiler could generate on its own. There are differences in the optimizations
performed by the compilers, but I've tried to use each compiler's most
sensible set of optimization options.

## SPARC Processors

<div class="shortcode">
{{< processor-benchmark-table "sparc_processors" >}}
</div>

## MIPS Processors

<div class="shortcode">
{{< processor-benchmark-table "mips_processors" >}}
</div>

## POWER/PowerPC Processors

<div class="shortcode">
{{< processor-benchmark-table "power_processors" >}}
</div>

## PA-RSIC Processors

<div class="shortcode">
{{< processor-benchmark-table "parisc_processors" >}}
</div>

## ARM Processors

<div class="shortcode">
{{< processor-benchmark-table "arm_processors" >}}
</div>

## x86 Processors

<div class="shortcode">
{{< processor-benchmark-table "x86_processors" >}}
</div>

