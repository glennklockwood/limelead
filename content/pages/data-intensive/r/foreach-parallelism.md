---
title: foreach-based Parallelism
order: 20
---

## 4. Introduction

The [foreach package][foreach cran page], which is authored by the folks at 
[Revolution Analytics][revolution analytics foreach whitepaper], is
functionally equivalent to the [lapply-based parallelism](lapply-parallelism.html)
discussed in the previous section, but it exposes the parallel functionality to
you (the programmer) in what may seem like a more intuitive and uniform way.  In
particular,

* you do not have to evaluate a function on each input object; rather, the code
  contained in the body of the <code>foreach</code> loop is what gets executed
  on each object
* your parallel code uses the same syntax across all of the possible parallel
  backends, so there is no need to switch between <code>lapply</code>,
  <code>mclapply</code>, and <code>parLapply</code>

Perhaps it is more sensible to illustrate what this means by comparing the
equivalent commands expressed using <code>lapply</code> and 
<code>foreach</code>:

    :::r
    mylist <- c( 1, 2, 3, 4, 5 )
    output1 <- lapply( mylist, FUN=function(x) { y = x + 1; y } )
    output2 <- foreach(x = mlist) %do% { y = x + 1; y }

Both codes iterate through every element in <var>mylist</var> and return a
list of the same length as <var>mylist</var> containing each of the elements
in <var>mylist</var> plus one.

However, there is an implicit assumption that **there are no side 
effects of the code being executed within the foreach loop**--that is, 
we assume that the contents of the loop body are not changing any variables
or somehow affecting any global state of the rest of our code.  For example,
the variable <var>y</var> is not guaranteed to contain 6 at the end of the 
foreach loop, and in fact, it is not even guaranteed to be defined.

## 4.1. Halfway to parallel

Going back to the simple k-means example, recall that this is what the most
simplified (serial) version of the code would look like:

    :::r
    data <- read.csv('dataset.csv')

    result <- kmeans(data, centers=4, nstart=100)

    print(result)

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

## 4.2. doMC: shared-memory parallelism

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

{{ figure("mclapply-vs-foreach-scaling.png", alt="mclapply Scaling") }}

The slightly greater speedup in the <code>foreach</code> case (<span 
style="color:red">red</span> line) is not significant since the dataset I used 
is a bit of a trivial case and only took a few seconds to run.

## 4.3. doSNOW: distributed-memory parallelism

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

    :::r
    data <- read.csv( 'dataset.csv' )

and clone it across all of your nodes:

    :::r
    clusterExport(cl, c('data'))

Thus, these approaches will not really help you solve problems that are too
large to fit into memory; in such cases, you either need to turn to special
out-of-core packages (e.g., the [ff][ff cran page] or
[bigmemory][bigmemory cran page] libraries) or turn to map/reduce-style
parallelism with a framework like Hadoop or Spark.  There are programming
tricks you can play to skirt around this (e.g., loading subsets of the input
data, distributing it, deleting that object, and then garbage collecting
before loading the next subset) but they rapidly become extremely complicated.

<hr>

These approaches to parallelism so far require explicitly calling specific
parallel libraries and deliberately restructuring algorithms to make them
amenable to parallelization.  In the next section, we will examine 
[alternative forms of parallelism](alternative-parallelism.html) that do _not_
require such significant changes to code.

<!-- references -->
[my parallel r github repository]: https://github.com/glennklockwood/paraR/tree/master/kmeans
[running r on hpc clusters]: on-hpc.html
[whats killing cloud interconnect performance]: http://glennklockwood.blogspot.com/2013/06/whats-killing-cloud-interconnect.html
[foreach cran page]: http://cran.r-project.org/web/packages/foreach/index.html
[revolution analytics foreach whitepaper]: http://www.revolutionanalytics.com/whitepaper/using-foreach-package-r-combine-iterators-and-other-functions
[ff cran page]: http://cran.r-project.org/web/packages/ff/index.html
[bigmemory cran page]: http://cran.r-project.org/web/packages/bigmemory/index.html
