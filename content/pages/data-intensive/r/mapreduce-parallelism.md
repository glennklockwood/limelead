---
title: Map-reduce-based Parallelism
order: 40
overrideLastMod: August 14, 2013
---

## 7. Introduction

The previous pages on [lapply-based](lapply-parallelism.html), 
[foreach-based](foreach-parallelism.html), and [alternative forms of
parallelism](alternative-parallelism.html) are all optimized for parallelizing
problems where the CPU is the ultimate bottleneck between you and your results.
As mentioned in the [Caveats with lapply- and foreach-based parallelism](foreach-parallelism.html#5-caveats-with-lapply-and-foreach-based-parallelism)
section, though, there are some problems where the size of your dataset is the
biggest hurdle because it cannot fit into the memory of your workstation.

The map-reduce paradigm works around that limitation by splitting your dataset
up into manageable sizes _before_ your parallel R scripts begin processing them.

<span style="color:red">Unfortunately I have not had the time to turn this section into
prose.  If you are interested in learning more about using Hadoop with R, please
contact me and let me know!</span>  I have the material for this section in
slides already; I just haven't had the motivation to turn it into a tutorial.

## 7.1. Halfway to parallel

## 7.2. Hadoop Streaming

## 7.3. RHIPE

## 7.4. RHadoop

<!-- references -->
