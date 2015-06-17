---
date: "2013-08-14T00:00:00-07:00"
draft: false
title: "Parallel Options for R"
shortTitle: "Parallel Options"
parentdirs: [ 'data-intensive', 'r' ]
---

## Table of Contents

* [1. Introduction](#1-introduction)
* [2. The Parallel R Taxonomy](#2-the-parallel-r-taxonomy)
* [3. lapply-based parallelism][lapply-based parallelism]
    * [3.1. lapply: halfway to parallel](#3-1-lapply-halfway-to-parallel)
    * [3.2. mclapply: shared-memory parallelism](#3-2-mclapply-shared-memory-parallelism)
    * [3.3. parLapply: distributed-memory parallelism](#3-3-parlapply-distributed-memory-parallelism)
        * [3.3.1. MPI clusters](#3-3-1-mpi-clusters)
        * [3.3.2. PSOCK clusters](#3-3-2-psock-clusters)
        * [3.3.3. FORK clusters](#3-3-3-fork-clusters)
* [4. foreach-based parallelism][foreach-based parallelism]
    * [4.1. Halfway to parallel](#4-1-halfway-to-parallel)
    * [4.2. doMC: shared-memory parallelism](#4-2-domc-shared-memory-parallelism)
    * [4.3. doSNOW: distributed-memory parallelism](#4-3-dosnow-distributed-memory-parallelism)
* [5. Caveats with lapply- and foreach-based parallelism](#5-caveats-with-lapply-and-foreach-based-parallelism)
* [6. Poor man's parallelism][poor man's parallelism]
* [7. Hands-off parallelism][hands-off parallelism]
* [8. Map-Reduce-based parallelism with Hadoop][map-reduce-based parallelism]

## 1. Introduction

This page goes through various parallel libraries available to R programmers
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
[Running R on HPC Clusters][running r on hpc clusters] that goes through the
basics of how to actually run these example codes.
{{% /alertbox %}}
</div>

## 2. The Parallel R Taxonomy

There are a number of different ways to utilize parallelism to speed up a
given R script.  I like to think of them as generally falling into one of a few
broad categories of parallel R techniques though:

* [lapply-based parallelism][lapply-based parallelism]
* [foreach-based parallelism][foreach-based parallelism]
* [Poor man's parallelism][poor man's parallelism]
* [Hands-off parallelism][hands-off parallelism]
* [Map-Reduce-based parallelism][map-reduce-based parallelism]

Although there are an increasing number of additional libraries entering
CRAN that provide means to add parallelism that I have not included in this
taxonomy, they generally fall into (or close to) one of the above categories.

## 3. lapply-based parallelism

### 3.1. lapply: halfway to parallel

As with almost every form of parallel programming, you've got to take one
step backwards to make two steps forwards.  In a practical sense, that means
making our k-means calculator a little more complicated so that parallelizing
it becomes possible.  The following script is functionally the same as our
serial example above:

<pre>
data &lt;- read.csv('dataset.csv')

<span style="color:blue">parallel.function &lt;- function(i) {</span>
    kmeans( data, centers=4, nstart=<span style="color:blue">i</span> )
<span style="color:blue">}</span>

<span style="color:blue">results &lt;- lapply( c(25, 25, 25, 25), FUN=parallel.function )</span>

<span style="color:blue">temp.vector &lt;- sapply( results, function(result) { result$tot.withinss } )</span>
<span style="color:blue">result &lt;- results[[which.min(temp.vector)]]</span>

print(result)
</pre>

Seeing as how this code is functionally equivalent to the code in the 
previous section, there is a lot more complexity added here that ultimately
does nothing useful.  I've highlighted all of the new cruft we've had to add
to our code in <span style="color:blue">blue</span>, only those lines that
remain uncolored resemble the code that actually does the k-means calculation
in the simple, serial case.

Here are the key features of the changes:

1. The <code>kmeans</code> function is now wrapped in a custom function we
   are calling <code>parallel.function</code> that takes the number of starting
   positions (<code>nstart</code>) as its sole parameter, with the other input
   parameters for our <code>kmeans</code> call being hard-coded in as with the 
   serial example.
2. <code>lapply</code> is used to call this <code>parallel.function</code>
   four times now, instead of the single time it was called before
3. Each of the four invocations of <code>lapply</code> winds up calling
   <code>kmeans</code>, but each call to <code>kmeans</code> only does 25 starts
   instead of the full 100.  Overall, we're doing 4&#215;25 starts instead of
   the 1&#215;100 we were doing before, so there is no practical change in what
   we're doing.
4. <code>results</code> (with an s!) is now a list of four <code>kmeans</code>
   output data.
5. Knowing that we want to find the k-means result with the absolute lowest
   value for <code>results$tot.withinss</code>, we can use the 
   <code>which.min()</code> function to return the list index of <code>results</code>
   that has the minimum value.  However, <code>which.min()</code> operates only
   on vectors, so we need to build a vector of each <code>tot.withinss</code> value
   contained in the <code>results</code> list...
6. <code>sapply</code> does just that, and returns a vector comprised of each
   <code>tot.withinss</code> value from the list of k-means objects we've named
   <code>results</code>.  We name this vector (which contains the values of 
   each <code>tot.withinss</code>) <code>temp.vector</code>
7. Finally we use <code>which.min</code> to get the index of 
   <code>temp.vector</code> that contains the minimum value.  This index 
   corresponds to the index of <code>results</code> that has the minimum 
   <code>tot.withinss</code>

What was the point in making this k-means code so complicated?

The operative procedure here is that we divided a single call of 
<code>kmeans</code> into four calls of <code>kmeans</code>:

<div class="shortcode">
{{< figure src="kmeans-approach.png" link="kmeans-approach.png" alt="parallel k-means approach" >}}
</div>

Each of these four <code>kmeans</code> invocations only calculate a quarter of
the original 100 starting points, and since starting points are all independent,
we can now potentially run these four <code>kmeans</code> concurrently.

### 3.2. mclapply: shared-memory parallelism

Now that we have a parallelizable form of this simple k-means problem, 
actually parallelizing it is quite simple.  There are literally two changes you
have to make, highlighted in blue below:

<pre>
<span style="color:blue">library(parallel)</span>

data &lt;- read.csv('dataset.csv')

parallel.function &lt;- function(i) {
    kmeans( data, centers=4, nstart=i )
}

results &lt;- <span style="color:blue">mc</span>lapply( c(25, 25, 25, 25), FUN=parallel.function )

temp.vector &lt;- sapply( results, function(result) { result$tot.withinss } )
result &lt;- results[[which.min(temp.vector)]]

print(result)
</pre>

The <code>parallel</code> library, which comes with R as of version 2.14.0,
provides the <code>mclapply()</code> function which is a drop-in replacement for
lapply.  The "mc" stands for "multicore," and as you might gather, this function
distributes the <code>lapply</code> tasks across multiple CPU cores to be 
executed in parallel.

This is the first cut at parallelizing R scripts.  Using shared memory 
(multicore) tends to be much simpler because all parallel tasks automatically
share their R environments and can see the objects and variables we defined
before the parallel region that is encapsulated by <code>mclapply</code>.  All
of the hard work is in restructuring your problem to use lapply when, serially,
it wouldn't necessarily make sense.

The performance isn't half bad either.  By changing the <var>MC_CORES</var>
environment variable, we can see how well this <code>mclapply</code> approach
scales:

<div class="shortcode">
{{< figure src="mclapply-scaling.png" link="mclapply-scaling.png" alt="mclapply scaling" >}}
</div>

The downside is that this shared memory approach to parallelism in R is 
limited by how many cores your computer has.  Modern supercomputers achieve 
parallelism via _distributed memory_, meaning many nodes (discrete 
computers in their own right) do _not_ share memory and need to be 
explicitly given all of the variables and objects that were created outside of 
the parallel region.

### 3.3. parLapply: distributed-memory parallelism

To use more than one node's worth of CPU cores with lapply-style parallelism,
you have to use some type of networking so that each node can communicate with
each other and shuffle the relevant data around.  As such, there's a bit more
bookkeeping involved with using an _distributed memory_ version of
lapply, but fortunately, the actual logic of your application doesn't need to
change much.  Here is what a multi-node version of our parallel k-means would
look like using <code>parLapply</code> instead of <code>mclapply</code>:

<pre>
library(<span style="color:blue">snow</span>)

data &lt;- read.csv( 'dataset.csv' )

parallel.function &lt;- function(i) {
    ;kmeans( data, centers=4, nstart=i )
}

<span style="color:blue">cl &lt;- makeCluster( mpi.universe.size(), type="MPI" )</span>
<span style="color:blue">clusterExport(cl, c('data'))</span>

results &lt;- <span style="color:blue">parLapply</span>( <span style="color:blue">cl,</span> c(25,25,25,25), fun=parallel.function )

temp.vector &lt;- sapply( results, function(result) { result$tot.withinss } )
result &lt;- results[[which.min(temp.vector)]]
print(result)

<span style="color:blue">stopCluster(cl)</span>
<span style="color:blue">mpi.exit()</span>
</pre>

Once again, differences are highlighted in <span style="color:blue">blue</span>.
Notably,

1. We use the <code>snow</code> library instead of the <code>parallel</code>
   library.  This is not strictly necessary, but as I'll discuss below, having
   <code>snow</code> installed allows you to use a few additional parallel 
   backends.
2. We must create a "cluster" object using the <code>makeCluster</code> 
   function.  This "cluster" will be what determines what nodes and cores the
   <code>parLapply</code> function are available for work distribution.
3. Because we are using <em>distributed</em> memory, not all of our worker CPUs
   can see the data we have loaded into the main R script's memory.  Thus, we need
   to explicitly distribute that data to our worker nodes using the 
   <code>clusterExport</code> function.
4. To be completely proper, we need to tear down the cluster we built at the
   end of our script using <code>stopCluster(cl)</code>.  The
   <code>mpi.exit()</code> is required because we chose to use the
   <code>MPI</code> cluster type.

The "bookkeeping" required to set up and tear down clusters are the biggest
difference between using shared-memory <code>mclapply</code> and this 
distributed-memory <code>parLapply</code>, but <code>parLapply</code> is 
actually a generalization of <code>mclapply</code>.  This is a result of the
fact that when creating clusters using the <code>makeCluster</code> function,
you have the option to select different parallel backends that use shared 
memory _or_ distributed memory:

#### 3.3.1. MPI clusters

The <code>type="MPI"</code> uses MPI for its parallel operations, which is 
inherently capable of distributed memory.  There are a few benefits:

* You can utilize any high-performance networking like InfiniBand if it is available on your parallel computing hardware
* You can also leverage MPI's integration with your resource manager so that you don't need to know the hostnames of all of your job's nodes

But there are also some complications:

* You need to <a href="http://users.sdsc.edu/~glockwood/di/R-hpc.php#installinglibs:rmpi">install Rmpi</a>, which can be unpleasantly difficult
* You need to <a href="http://users.sdsc.edu/~glockwood/di/R-hpc.php#pbs:snow">launch your R script from within an MPI environment</a> which is a little more complicated

If your parallel computing platform already has MPI installed and you can
install Rmpi yourself (or have a handy staffmember who can help you), using
<code>type="MPI"</code> is definitely the best way to use distributed-memory
parallelism with <code>parLapply</code> simply because large parallel computers
are designed to run MPI at their foundations.  You might as well work with this
as much as you can.

#### 3.3.2. PSOCK clusters

The <code>type="PSOCK"</code> uses TCP sockets to transfer data between 
nodes.

The benefits:

* <code>PSOCK</code> is fully contained within the <code>parallel</code> library that ships with newer versions of R (&gt; 2.14) and does not require external libraries like Rmpi
* It also runs over regular old networks (and even the Internet!) so you don't need special networking as long as your cluster hosts can communicate with each other

But there are also some complications:

* You are stuck using TCP which is relatively [slow in terms of both bandwidth
  and latency][whats killing cloud interconnect performance]
* You need to explicitly give the hostnames of all nodes that will participate
  in the parallel computation

Creating a PSOCK cluster is similar to launching an MPI cluster, but instead
of simply saying how many parallel workers you want (e.g., with the call to
<code>mpi.universe.size()</code> we used in the MPI cluster example above), you
have to lay them all out, e.g.,

<div class="shortcode">
{{< highlight r >}}
mynodes &lt;- c( 'localhost', 'localhost', 'node1', 'node1', 'node2', 'node2' )
makeCluster( mynodes, type='PSOCK' )
{{< /highlight >}}
</div>

In the above example, we indicate that we will want to use two parallel
workers on the same machine from which this R script was launched 
(<code>localhost</code> appears twice) as well as two workers on a machine
named <code>node1</code> and two more on <code>node2</code>.

Ultimately, PSOCK works well in small-scale computing environments where
there are a lot of loosely coupled computers available.  For example, if your
lab has a few workstations that aren't in use, you can use all of their idle 
CPUs to process a single R job using <code>parLapply</code> without having to
configure any sort of complex parallel computing environment using PSOCK.

#### 3.3.3. FORK clusters

Finally, <code>type="FORK"</code> behaves just like the <code>mclapply</code>
function discussed in the previous section.  Like <code>mclapply</code>, it can
only use the cores available on a single computer, but it does not require that
you <code>clusterExport</code> your data since all cores share the same memory.
You may find it more convenient to use a FORK cluster with 
<code>parLapply</code> than <code>mclapply</code> if you anticipate using the
same code across multicore _and_ multinode systems.

## 4. foreach-based parallelism

The [foreach package][foreach cran page], which is authored by the folks at 
[Revolution Analytics][revolution analytics foreach whitepaper], is
functionally equivalent to the lapply-based parallelism discussed above, but
it exposes the parallel functionality to you (the programmer) in what may seem 
like a more intuitive and uniform way.  In particular,

* you do not have to evaluate a function on each input object; rather, the code contained in the body of the <code>foreach</code> loop is what gets executed on each object
* your parallel code uses the same syntax across all of the possible parallel backends, so there is no need to switch between <code>lapply</code>, <code>mclapply</code>, and <code>parLapply</code>

Perhaps it is more sensible to illustrate what this means by comparing the
equivalent commands expressed using <code>lapply</code> and 
<code>foreach</code>:

<div class="shortcode">
{{< highlight r >}}
mylist &lt;- c( 1, 2, 3, 4, 5 )
output1 &lt;- lapply( mylist, FUN=function(x) { y = x + 1; y } )
output2 &lt;- foreach(x = mlist) %do% { y = x + 1; y }
{{< /highlight >}}
</div>

Both codes iterate through every element in <var>mylist</var> and return a
list of the same length as <var>mylist</var> containing each of the elements
in <var>mylist</var> plus one.

However, there is an implicit assumption that **there are no side 
effects of the code being executed within the foreach loop**--that is, 
we assume that the contents of the loop body are not changing any variables
or somehow affecting any global state of the rest of our code.  For example,
the variable <var>y</var> is not guaranteed to contain 6 at the end of the 
foreach loop, and in fact, it is not even guaranteed to be defined.

### 4.1. Halfway to parallel

Going back to the simple k-means example, recall that this is what the most
simplified (serial) version of the code would look like:

<div class="shortcode">
{{< highlight r >}}
data &lt;- read.csv('dataset.csv')

result &lt;- kmeans(data, centers=4, nstart=100)

print(result)
{{< /highlight >}}
</div>

As with lapply-based parallelism, we have to take a step backwards to make
the code amenable to parallelization.  The foreach version of the k-means code
looks like this:

<pre>
<span style='color:blue'>library(foreach)</span>
data &lt;- read.csv('dataset.csv')

results &lt;- <span style='color:blue'>foreach( i = c(25,25,25,25) ) %do% {</span>
    kmeans( x=data, centers=4, nstart=<span style='color:blue'>i</span> )
<span style='color:blue'>}</span>

<span style='color:blue'>temp.vector &lt;- sapply( results, function(result)</span>
<span style='color:blue'>    { result$tot.withinss } )</span>
<span style='color:blue'>result &lt;- results[[which.min(temp.vector)]]</span>

print(result)
</pre>

Again, this is significantly more clunky than the simple three-line serial
k-means code; I've highlighted the differences in blue above.  However, if we
compare it to the lapply-style version of our k-means code, it is actually quite
similar.  Here is the same foreach code with the differences from lapply now
highlighted:

<pre>
<span style='color:blue'>library(foreach)</span>
data &lt;- read.csv('dataset.csv')

results &lt;- <span style='color:blue'>foreach( i = c(25,25,25,25) ) %do% </span>{
    kmeans( x=data, centers=4, nstart=i )
}

temp.vector &lt;- sapply( results, function(result)
    { result$tot.withinss } )
result &lt;- results[[which.min(temp.vector)]]

print(result)
</pre>

### 4.2. doMC: shared-memory parallelism

Once we've coerced our algorithm into the foreach-based formulation, it
becomes _very_ easy to parallelize it.  Instead of making a new call
parallelized form of lapply like <code>mclapply</code>, <code>foreach</code>
lets us _register a parallel backend_ by loading the appropriate backend
library and registering it:

<pre>
library(foreach)
<span style='color:blue'>library(doMC)</span>
data &lt;- read.csv('dataset.csv')

<span style='color:blue'>registerDoMC(4)</span>
results &lt;- foreach( i = c(25,25,25,25) ) %do<span style='color:blue'>par</span>% {
    kmeans( x=data, centers=4, nstart=i )
}

<span style='color:blue'>temp.vector &lt;- sapply( results, function(result)</span>
<span style='color:blue'>    { result$tot.withinss } )</span>
<span style='color:blue'>result &lt;- results[[which.min(temp.vector)]]</span>

print(result)
</pre>

The <code>doMC</code> library is what provides the "multicore" parallel 
backend for the <code>foreach</code> library.  Once loaded, all you have to do
to parallelize your loop is call <code>registerDoMC</code> to indicate the 
number of cores to use (four in the above example) and replace the <code>%do</code>
with <code>%dopar%</code> to tell <code>foreach</code> to use the parallel 
backend you just registered.

As one would hope, using <code>foreach</code> with the <code>doMC</code>
parallel backend provides the same speedup as <code>mclapply</code>:

<div class="shortcode">
{{< figure src="mclapply-vs-foreach-scaling.png" link="mclapply-vs-foreach-scaling.png" alt="mclapply Scaling" >}}
</div>

The slightly greater speedup in the <code>foreach</code> case (<span 
style="color:red">red</span> line) is not significant since the dataset I used 
is a bit of a trivial case and only took a few seconds to run.

### 4.3. doSNOW: distributed-memory parallelism

Just as we used the <code>snow</code> library to perform multi-node, 
distributed-memory parallelization with <code>parLapply</code>, we can use the
<code>doSNOW</code> parallel backend with <code>foreach</code> to perform
distributed-memory parallelization.  Here is what our k-means example would look
like:

<pre>
library(foreach)
library(do<span style='color:blue'>SNOW</span>)
data &lt;- read.csv('dataset.csv')
<span style='color:blue'>cl &lt;- makeCluster( mpi.universe.size(), type='MPI' )</span>
<span style='color:blue'>clusterExport(cl,c('data'))</span>
registerDo<span style='color:blue'>SNOW</span>(<span style='color:blue'>cl</span>)
results &lt;- foreach( i = c(25,25,25,25) ) %dopar% {
    kmeans( x=data, centers=4, nstart=i )
}

temp.vector &lt;- sapply( results, function(result) 
    { result$tot.withinss } )
result &lt;- results[[which.min(temp.vector)]]

print(result)
<span style='color:blue'>stopCluster(cl)</span>
<span style='color:blue'>mpi.exit()</span>
</pre>

The differences between the <code>doMC</code> and <code>doSNOW</code> version
of this foreach k-means example are highlighted in blue.  We really only had to 
make three changes:

1. we replaced <code>doMC</code> with <code>doSNOW</code> and used the
   corresponding backend registration function, <code>registerDoSNOW</code>
2. we had to create a cluster object just like we did with
   <code>parLapply</code>
3. we also had to export our input data to all worker nodes using
   <code>clusterExport</code>, also like we did with <code>parLapply</code>

Everything we learned about the types of clusters we can create for 
<code>parLapply</code> also work with the <code>doSNOW</code> backend for
foreach.  It follows that we also have to be mindful of distributing all of 
the data we will need our workers to see via the <code>clusterExport</code> 
call when using MPI or SOCK clusters.  At the end of the day though, there 
aren't any fundamental differences between the things we can do with these 
cluster objects when moving from <code>parLapply</code> to <code>doSNOW</code>.

## 5. Caveats with lapply- and foreach-based parallelism

Ultimately, using these lapply- and foreach-style approaches to 
parallelizing your R scripts works well if your R script is very CPU-intensive 
and spends a lot of time just doing processing on a relatively small-ish 
dataset.  I often see people use this approach under conditions when they want 
to

* try many different statistical models on the same set of data
* run the same statistical model on many different datasets
* ...or just about any other case where many independent calculations must be performed

The biggest downside to using these methods is that **you are still limited by
the amount of memory you have in a single node** as far as how large of a
dataset you can process.  This is because you still load the entire dataset
into memory on the master process:

<div class="shortcode">
{{< highlight r >}}
data &lt;- read.csv( 'dataset.csv' )
{{< /highlight >}}
</div>

and clone it across all of your nodes:

<div class="shortcode">
{{< highlight r >}}
clusterExport(cl, c('data'))
{{< /highlight >}}
</div>

<p>Thus, these approaches will not really help you solve problems that are too
large to fit into memory; in such cases, you either need to turn to special
out-of-core packages (e.g., the <code><a href="http://cran.r-project.org/web/packages/ff/index.html">ff</a></code> or <code><a href="http://cran.r-project.org/web/packages/bigmemory/index.html">bigmemory</a></code> libraries)
or turn to map/reduce-style parallelism with a framework like Hadoop or 
Spark.  There are programming tricks you can play to skirt around this (e.g.,
loading subsets of the input data, distributing it, deleting that object, and
then garbage collecting before loading the next subset) but they rapidly become
extremely complicated.</p>

## 6. Poor man's parallelism

The simplest, yet ugliest, way to parallelize your R code is to simply run
a bunch of copies of the same R script that each read in slightly different 
set of input parameters or data.  I call this "poor man's parallelism" (or PMP)
because

1. you can use it without any special libraries, packages, or programs
2. you can program R scripts to utilize this without knowing anything about
   parallel programming
3. you can use multicore or multi-node parallelism without any added effort

For these reasons, poor man's parallelism is, by far, the most popular way to
parallelize codes in my experience.  That doesn't mean it's the best way though;
it is simply the most accessible to the novice R programmer.  Hopefully the
previous sections on lapply- and foreach-based parallelism provide enough 
information to show that there are better ways to write portable, simplified 
parallel R scripts.

With that being said, sometimes it's just easiest to go the poor man's route
and run a ton of R scripts all at once.  Perhaps the easiest way to efficiently
do this is to have the R script read in some input from the command line so that
the same script can be called multiple times _without modification_ to
generate the parallel outputs desired.  For example, let's rewrite our k-means
script using PMP:

<pre>
<span style='color:blue'>args &lt;- commandArgs(TRUE)</span>
<span style='color:blue'>set.seed(args[1])</span>

data &lt;- read.csv('dataset.csv')

result &lt;- kmeans(data, centers=4, nstart=25)

print(result)
</pre>

I've highlighted the additional code to support PMP when compared to our
very first serial k-means code.  Unlike the lapply- and foreach-based 
approaches, we don't have to mangle our code to make it amenable to 
parallelization; rather, we

1. take input from the command line so that we have a mechanism to distinguish one particular execution of this script from another
2. use this command-line input to set the random number generator's seed value

<div class="shortcode">
{{% inset "Parallel Random Numbers" %}}
When running many instances of the same script in parallel, it is 
particularly important to remember that computers generate pseudorandom numbers
by using some deterministic algorithm based on a seed value.  If the seed value
is not explicitly defined to be different for every parallel invocation of your
R script, you may run the risk of having every single copy of the R script use
an identical series of random numbers and literally performing the same exact
operations.<br><br>
There are a variety of options for _parallel random number generation_
in R that are beyond the scope of this guide.  The reason I don't feel the need
to dive into them here is because newer versions of R have gotten reasonably
good at anticipating parallel execution and using highly random seeds for each
parallel invocation of the same R script.  In this k-means example, manually
calling <code>set.seed</code> is actually not necessary; I merely included it
here to show how we can get command-line arguments from an R script to affect
how one might use the same R script with PMP.
{{% /inset %}}
</div>


<p>We then run four copies of this script using different inputs to generate
different randomized starts:</p>
<blockquote>
<div>$ <kbd>Rscript ./kmeans-pmp.R 1 &gt; output1.txt &amp;</kbd></div>
<div>$ <kbd>Rscript ./kmeans-pmp.R 2 &gt; output2.txt &amp;</kbd></div>
<div>$ <kbd>Rscript ./kmeans-pmp.R 3 &gt; output3.txt &amp;</kbd></div>
<div>$ <kbd>Rscript ./kmeans-pmp.R 4 &gt; output4.txt &amp;</kbd></div>
<div>$ <kbd>wait</kbd> # waits for all four backgrounded R scripts to finish</div>
</blockquote>

<p>Remembering that the trailing ampersand (&amp;) tells our Rscript to run in
the background, the above commands will run four invocations of our PMP k-means
example concurrently and return us to the shell when they're all finished.</p>

<p>While the code for our PMP k-means is extremely simple and very similar to
our very original k-means code, running this PMP code gives us four output files,
each containing one of our local minima.  It then falls on us as the programmer
to sift through those four outputs and determine which 
<var>result$tot.withinss</var> is the global minimum across our parallel
invocations.  Thus, we save time on programming by using PMP, but we have to
make up for it in sifting through our parallel outputs.  Ultimately, this is the
biggest disadvantage to using PMP over the more elegant <code>lapply</code>- 
or <code>foreach</code>-based approaches.</p>

<p>There are actually a lot of different tricks you can use to make PMP more
attractive, but I am hesitant to go through them in detail here since using PMP
is generally the poorest way to parallelize R code.  However, I will provide
the following tips:</p>
<ul>
<li>You can make your R script run like any other program by adding <code>#!/usr/bin/env Rscript</code> as the very first line of your script (the hashbang).  Once you've done this and made the script executable (<kbd>chmod +x kmeans-pmp.R</kbd>).  Once you've done this, you can run it by simply doing <kbd>./kmeans-pmp.R 1</kbd>.</li>
<li>You can use an MPI-based bundler script to let MPI manage the distribution of your R tasks.  I've written such <a href="https://github.com/sdsc/sdsc-user/tree/master/bundler">an MPI-based bundler which can be found on GitHub</a>.</li>
<li>You can easily combine PMP with shared-memory parallelism (<code>mclapply</code> or <code>doMC</code>) or hands-off parallelism (see below) to do multi-level parallelization.  Further combined with the MPI bundler in the previous bullet point, you can then launch a massive, hybrid parallel (shared-memory and MPI) R job without a huge amount of effort.</li>
</ul>
<p>Just remember: poor man's parallelism may be easier to code up front, but you
wind up paying for it when you have to do a lot of the recombination of the 
output by hand!</p>

<hr />

## 7. Hands-off parallelism

<p>The final form of parallelism that can be used in R is what I call 
"hands-off" parallelism because, quite simply, you don't need to do anything to
use it as long as you are using a semi-modern version (&gt; 2.14) of R.</p>
<p>R has included OpenMP support for some time now, and newer versions of R 
enable OpenMP by default.  While this doesn't mean much for the core R libraries 
themselves (only the <code>colSums</code> and <code>dist</code> functions 
actually use OpenMP within the core R distribution as of version 3.0.2), a 
growing number of libraries on CRAN include OpenMP support <em>if your R 
distribution was also built with OpenMP</em>.</p>
<p>This can be good and bad; on the upside, you don't need to know anything
about parallelism to be able to use multiple CPU cores on your machine as long
as the R library you are using has this hands-off parallelism coded in.  
However, this can also be extremely hazardous if you are trying to use any of
the other forms of parallelism we've discussed above.  For example, consider our
mclapply k-means example:</p>
<blockquote>
<div>library(parallel)</div>
<div>&nbsp;</div>
<div>data &lt;- read.csv('dataset.csv')</div>
<div>&nbsp;</div>
<div>parallel.function &lt;- function(i) {</div>
<div> &nbsp;<span style="color:blue">some.special.kmeans.with.builtin.openmp( data, centers=4, nstart=i )</span></div>
<div>}</div>
<div>&nbsp;</div>
<div>results &lt;- mclapply( c(25, 25, 25, 25), FUN=parallel.function )</div>
<div>&nbsp;</div>
<div>temp.vector &lt;- sapply( results, function(result) { result$tot.withinss } )</div>
<div>result &lt;- results[[which.min(temp.vector)]]</div>
<div>&nbsp;</div>
<div>print(result)</div>
</blockquote>
<p>If instead of <code>kmeans</code>, our code's <code>parallel.function</code>
makes a call to some library with hands-off parallelism built in (e.g., <code>some.special.kmeans.with.builtin.openmp</code> 
as in the above example), we might actually be running four mclapply tasks 
<em>multiplied by</em> the number of CPU cores in our system since hands-off 
parallelism can try to use <em>all of the CPU cores with each parallel 
worker</em> (depending on the compiler used to build R).  Needless to say, 
trying to use more cores than the computer has will cause everything to grind 
to a halt, so you have to be extremely careful when dealing with a library 
that may include OpenMP support!</p>
<p>The safest way to protect yourself <em>against</em> hands-off parallelism 
when using other forms of explicit (or "hands-on") parallelism is to explicitly
disable it using the OpenMP runtime API and setting
<var>OMP_NUM_THREADS</var> in your shell:</p>
<blockquote>
<div>$ <kbd>export OMP_NUM_THREADS=1</kbd></div>
</blockquote>
<p>Whether hands-off parallelism will use only one core or all cores by
default is dependent upon the compiler used to build the R executable you are 
using.  This is a result of the ambiguity of the OpenMP standard which leaves 
the default "greediness" of OpenMP up to the OpenMP implementors, and I've seen
different compilers choose both one and all cores if <var>OMP_NUM_THREADS</var>
is not explicitly defined.  Just be mindful of the possibilities.</p>

<!-- the colSums() and dist() calls uses OpenMP as of 3.0.2.  That's it. -->

## Map-Reduce-based parallelism with Hadoop

<!-- references -->
[my parallel r github repository]: https://github.com/glennklockwood/paraR/tree/master/kmeans
[running r on hpc clusters]: on-hpc.html
[lapply-based parallelism]: #3-lapply-based-parallelism
[foreach-based parallelism]: #4-foreach-based-parallelism
[poor man's parallelism]: #5-poor-man-s-parallelism
[hands-off parallelism]: #7-hands-off-parallelism
[map-reduce-based parallelism]: #8-map-reduce-based-parallelism-with-hadoop
[whats killing cloud interconnect performance]: http://glennklockwood.blogspot.com/2013/06/whats-killing-cloud-interconnect.html
[foreach cran page]: http://cran.r-project.org/web/packages/foreach/index.html
[revolution analytics foreach whitepaper]: http://www.revolutionanalytics.com/whitepaper/using-foreach-package-r-combine-iterators-and-other-functions
