---
date: "2013-08-14T00:00:00-07:00"
draft: false
title: "lapply-based Parallelism"
shortTitle: "lapply-based Parallelism"
parentdirs: [ 'data-intensive', 'r' ]
---

## Contents

* [3. Introduction](#3-introduction)
* [3.1. lapply: halfway to parallel](#3-1-lapply-halfway-to-parallel)
* [3.2. mclapply: shared-memory parallelism](#3-2-mclapply-shared-memory-parallelism)
* [3.3. parLapply: distributed-memory parallelism](#3-3-parlapply-distributed-memory-parallelism)
    * [3.3.1. MPI clusters](#3-3-1-mpi-clusters)
    * [3.3.2. PSOCK clusters](#3-3-2-psock-clusters)
    * [3.3.3. FORK clusters](#3-3-3-fork-clusters)

## 3. Introduction

lapply-based parallelism may be the most intuitively familiar way to parallelize
tasks in R because it extend R's prolific <code>lapply</code> function.  It is
the first class of parallelism options in R, and we will continue to use the
k-means clustering example described in the [introduction to parallel options
for R](parallel-options.html) page to demonstrate how such a task can be
parallelized in a reasonably familiar way.

## 3.1. lapply: halfway to parallel

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

## 3.2. mclapply: shared-memory parallelism

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

## 3.3. parLapply: distributed-memory parallelism

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

### 3.3.1. MPI clusters

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

### 3.3.2. PSOCK clusters

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

### 3.3.3. FORK clusters

Finally, <code>type="FORK"</code> behaves just like the <code>mclapply</code>
function discussed in the previous section.  Like <code>mclapply</code>, it can
only use the cores available on a single computer, but it does not require that
you <code>clusterExport</code> your data since all cores share the same memory.
You may find it more convenient to use a FORK cluster with 
<code>parLapply</code> than <code>mclapply</code> if you anticipate using the
same code across multicore _and_ multinode systems.

<hr>

[foreach-based parallelism](foreach-parallelism.html) is another way of 
thinking about this sort of parallelism and is covered in the next section.

<!-- references -->
[my parallel r github repository]: https://github.com/glennklockwood/paraR/tree/master/kmeans
[running r on hpc clusters]: on-hpc.html
[whats killing cloud interconnect performance]: http://glennklockwood.blogspot.com/2013/06/whats-killing-cloud-interconnect.html
[foreach cran page]: http://cran.r-project.org/web/packages/foreach/index.html
[revolution analytics foreach whitepaper]: http://www.revolutionanalytics.com/whitepaper/using-foreach-package-r-combine-iterators-and-other-functions
