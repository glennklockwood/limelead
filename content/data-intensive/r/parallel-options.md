---
date: "2013-08-14T00:00:00-07:00"
draft: false
title: "Parallel Options for R"
shortTitle: "Parallel Options"
last_mod: "August 14, 2013"
parentdirs: [ 'data-intensive', 'r' ]
---

## Contents

* [1. Introduction](#1-introduction)
* [2. The parallel R taxonomy](#2-the-parallel-r-taxonomy)
* [3. lapply-based parallelism](lapply-parallelism.html)
    * [3.1. lapply: halfway to parallel](lapply-parallelism.html#3-1-lapply-halfway-to-parallel)
    * [3.2. mclapply: shared-memory parallelism](lapply-parallelism.html#3-2-mclapply-shared-memory-parallelism)
    * [3.3. parLapply: distributed-memory parallelism](lapply-parallelism.html#3-3-parlapply-distributed-memory-parallelism)
        * [3.3.1. MPI clusters](lapply-parallelism.html#3-3-1-mpi-clusters)
        * [3.3.2. PSOCK clusters](lapply-parallelism.html#3-3-2-psock-clusters)
        * [3.3.3. FORK clusters](lapply-parallelism.html#3-3-3-fork-clusters)
* [4. foreach-based parallelism](foreach-parallelism.html)
    * [4.1. Halfway to parallel](foreach-parallelism.html#4-1-halfway-to-parallel)
    * [4.2. doMC: shared-memory parallelism](foreach-parallelism.html#4-2-domc-shared-memory-parallelism)
    * [4.3. doSNOW: distributed-memory parallelism](foreach-parallelism.html#4-3-dosnow-distributed-memory-parallelism)
* [5. Caveats with lapply- and foreach-based parallelism](foreach-parallelism.html#5-caveats-with-lapply-and-foreach-based-parallelism)
* [6. Alternative forms of parallelism](alternative-parallelism.html)
    * [6.1. Poor-man's parallelism](alternative-parallelism.html#6-1-poor-man-s-parallelism)
    * [6.2. Hands-off parallelism](alternative-parallelism.html#6-2-hands-off-parallelism)
* [7. Map-Reduce-based parallelism with Hadoop](mapreduce-parallelism.html)
    * [7.1. Halfway to parallel](mapreduce-parallelism.html#7-1-halfway-to-parallel)
    * [7.2. Hadoop Streaming](mapreduce-parallelism.html#7-2-hadoop-streaming)
    * [7.3. RHIPE](mapreduce-parallelism.html#7-3-rhipe)
    * [7.4. RHadoop](mapreduce-parallelism.html#7-4-rhadoop)

## 1. Introduction

This tutorial goes through various parallel libraries available to R programmers
by applying them all to solve a very simple parallel problem: k-means 
clustering.  Although trivially parallel, k-means clustering is conceptually
simple enough for people of all backgrounds to understand, yet it can 
illustrate most of the core concepts common to all parallel R scripts.

Algorithmically, k-means clustering involves arriving at some solution (a
_local minima_) by iteratively approaching it from a randomly selected 
starting position.  The more random starts we attempt, the more local minima
we get.   For example, the following diagram shows some random data (top left)
and the result of applying k-means clustering from three different random 
starting guesses:

<div class="shortcode">
{{< figure src="kmeans-cluster.png" link="kmeans-cluster.png" alt="parallel k-means concept" >}}
</div>

We can then calculate some value (I think of it as an _energy function_) that
represents the error in each of these local minima.  Finding the smallest
error (the lowest "energy") from all of the starting positions (and their
resulting local minima) gives you the "best" overall solution (the _global
minimum_.  However, finding this global minimum is what we call an _NP-hard
problem_, meaning you'd need infinite time to be sure you've truly found the
absolute best answer possible.   Thus, we rely on increasing the number of
random starts to get as close as we can to this one true global minimum.

The simplest example of a k-means calculation in R looks like

<div class="shortcode">
{{< highlight r "linenos=inline" >}}
data &lt;- read.csv('dataset.csv')

result &lt;- kmeans(data, centers=4, nstart=100)

print(result)
{{< /highlight >}}
</div>

This code tries to find four cluster centers using 100 starting positions, 
and the value of <var>result</var> is the k-means object containing the 
minimal <var>result$tot.withinss</var> value for all 100 starts.  We'll now
look at a couple of different ways we can parallelize this calculation.  All of
the example codes presented here can be found in [my Parallel R GitHub 
repository][my parallel r github repository].

<div class="shortcode">
{{% alertbox info %}}
This guide is adapted from a talk I give, and it assumes that you already
know how to actually run R jobs on parallel computing systems.  I wrote a guide,
[Running R on HPC Clusters](on-hpc.html) that goes through the basics of how
to actually run these example codes.
{{% /alertbox %}}
</div>

## 2. The parallel R taxonomy

There are a number of different ways to utilize parallelism to speed up a
given R script.  I like to think of them as generally falling into one of a few
broad categories of parallel R techniques though:

* [lapply-based parallelism](lapply-parallelism.html)
* [foreach-based parallelism](foreach-parallelism.html)
* [Poor-man's parallelism and hands-off parallelism](alternative-parallelism.html)
* [Map-Reduce-based parallelism](mapreduce-parallelism.html)

Although there are an increasing number of additional libraries entering
CRAN that provide means to add parallelism that I have not included in this
taxonomy, they generally fall into (or close to) one of the above categories.

To illustrate how these forms of parallelism can be used in practice, the
remainder of this guide will demonstrate how a solution to the aforementioned
k-means clustering problem can be found using these parallel methods.

To begin, the most straightforward form of parallelism for R programmers is
[lapply-based parallelism which is covered in the next section](lapply-parallelism.html).

<!-- references -->
[my parallel r github repository]: https://github.com/glennklockwood/paraR/tree/master/kmeans
[running r on hpc clusters]: on-hpc.html
[whats killing cloud interconnect performance]: http://glennklockwood.blogspot.com/2013/06/whats-killing-cloud-interconnect.html
[foreach cran page]: http://cran.r-project.org/web/packages/foreach/index.html
[revolution analytics foreach whitepaper]: http://www.revolutionanalytics.com/whitepaper/using-foreach-package-r-combine-iterators-and-other-functions
