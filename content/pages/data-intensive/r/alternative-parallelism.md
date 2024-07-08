---
title: Alternative Forms of Parallelism
order: 30
overrideLastMod: August 14, 2013
---

## 6. Introduction

The previous section on [foreach-based parallelism](foreach-parallelism.html)
covers deliberate ways in which certain algorithms can be parallelized, but it
is often an inordinate amount of effort to restructure an entire script to
fit within the lapply- or foreach-based parallelism models.  This section
discusses ugly, but often effective, ways in which R scripts can be parallelized
with less effort.

## 6.1 Poor-man's parallelism

The simplest, yet ugliest, way to parallelize your R code is to simply run
a bunch of copies of the same R script that each read in slightly different 
set of input parameters or data.  I call this "poor-man's parallelism" (or PMP)
because

1. you can use it without any special libraries, packages, or programs
2. you can program R scripts to utilize this without knowing anything about
   parallel programming
3. you can use multicore or multi-node parallelism without any added effort

For these reasons, poor-man's parallelism is, by far, the most popular way to
parallelize codes in my experience.  That doesn't mean it's the best way though;
it is simply the most accessible to the novice R programmer.  Hopefully the
previous sections on lapply- and foreach-based parallelism provide enough 
information to show that there are better ways to write portable, simplified 
parallel R scripts.

With that being said, sometimes it's just easiest to go the poor-man's route
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

{% call inset("Parallel Random Numbers") %}
When running many instances of the same script in parallel, it is 
particularly important to remember that computers generate pseudorandom numbers
by using some deterministic algorithm based on a seed value.  If the seed value
is not explicitly defined to be different for every parallel invocation of your
R script, you may run the risk of having every single copy of the R script use
an identical series of random numbers and literally performing the same exact
operations.

There are a variety of options for _parallel random number generation_
in R that are beyond the scope of this guide.  The reason I don't feel the need
to dive into them here is because newer versions of R have gotten reasonably
good at anticipating parallel execution and using highly random seeds for each
parallel invocation of the same R script.  In this k-means example, manually
calling <code>set.seed</code> is actually not necessary; I merely included it
here to show how we can get command-line arguments from an R script to affect
how one might use the same R script with PMP.
{% endcall %}

We then run four copies of this script using different inputs to generate
different randomized starts:

<pre>
$ <kbd>Rscript ./kmeans-pmp.R 1 &gt; output1.txt &amp;</kbd>
$ <kbd>Rscript ./kmeans-pmp.R 2 &gt; output2.txt &amp;</kbd>
$ <kbd>Rscript ./kmeans-pmp.R 3 &gt; output3.txt &amp;</kbd>
$ <kbd>Rscript ./kmeans-pmp.R 4 &gt; output4.txt &amp;</kbd>
$ <kbd>wait</kbd> # waits for all four backgrounded R scripts to finish
</pre>

Remembering that the trailing ampersand (&amp;) tells our Rscript to run in
the background, the above commands will run four invocations of our PMP k-means
example concurrently and return us to the shell when they're all finished.

While the code for our PMP k-means is extremely simple and very similar to
our very original k-means code, running this PMP code gives us four output files,
each containing one of our local minima.  It then falls on us as the programmer
to sift through those four outputs and determine which 
<var>result$tot.withinss</var> is the global minimum across our parallel
invocations.  Thus, we save time on programming by using PMP, but we have to
make up for it in sifting through our parallel outputs.  Ultimately, this is the
biggest disadvantage to using PMP over the more elegant <code>lapply</code>- 
or <code>foreach</code>-based approaches.

There are actually a lot of different tricks you can use to make PMP more
attractive, but I am hesitant to go through them in detail here since using PMP
is generally the most poor way to parallelize R code.  However, I will provide
the following tips:

* You can make your R script run like any other program by adding <code>#!/usr/bin/env Rscript</code> as the very first line of your script (the hashbang).  Once you've done this and made the script executable (<kbd>chmod +x kmeans-pmp.R</kbd>).  Once you've done this, you can run it by simply doing <kbd>./kmeans-pmp.R 1</kbd>.
* You can use an MPI-based bundler script to let MPI manage the distribution of your R tasks.  I've written such <a href="https://github.com/sdsc/sdsc-user/tree/master/bundler">an MPI-based bundler which can be found on GitHub</a>.
* You can easily combine PMP with shared-memory parallelism (<code>mclapply</code> or <code>doMC</code>) or hands-off parallelism (see below) to do multi-level parallelization.  Further combined with the MPI bundler in the previous bullet point, you can then launch a massive, hybrid parallel (shared-memory and MPI) R job without a huge amount of effort.

Just remember: poor-man's parallelism may be easier to code up front, but you
wind up paying for it when you have to do a lot of the recombination of the 
output by hand!

## 6.2. Hands-off parallelism

The final form of parallelism that can be used in R is what I call 
"hands-off" parallelism because, quite simply, you don't need to do anything to
use it as long as you are using a semi-modern version (&gt; 2.14) of R.

R has included OpenMP support for some time now, and newer versions of R 
enable OpenMP by default.  While this doesn't mean much for the core R libraries 
themselves (only the <code>colSums</code> and <code>dist</code> functions 
actually use OpenMP within the core R distribution as of version 3.0.2), a 
growing number of libraries on CRAN include OpenMP support _if your R 
distribution was also built with OpenMP_.

This can be good and bad; on the upside, you don't need to know anything
about parallelism to be able to use multiple CPU cores on your machine as long
as the R library you are using has this hands-off parallelism coded in.
However, this can also be extremely hazardous if you are trying to use any of
the other forms of parallelism we've discussed above.  For example, consider our
mclapply k-means example:

<pre>
library(parallel)

data &lt;- read.csv('dataset.csv')

parallel.function &lt;- function(i) {
    <span style="color:blue">some.special.kmeans.with.builtin.openmp( data, centers=4, nstart=i )</span>
}

results &lt;- mclapply( c(25, 25, 25, 25), FUN=parallel.function )

temp.vector &lt;- sapply( results, function(result) { result$tot.withinss } )
result &lt;- results[[which.min(temp.vector)]]

print(result)
</pre>

If instead of <code>kmeans</code>, our code's <code>parallel.function</code>
makes a call to some library with hands-off parallelism built in (e.g., <code>some.special.kmeans.with.builtin.openmp</code> 
as in the above example), we might actually be running four mclapply tasks 
_multiplied by_ the number of CPU cores in our system since hands-off 
parallelism can try to use _all of the CPU cores with each parallel 
worker_ (depending on the compiler used to build R).  Needless to say, 
trying to use more cores than the computer has will cause everything to grind 
to a halt, so you have to be extremely careful when dealing with a library 
that may include OpenMP support!

The safest way to protect yourself _against_ hands-off parallelism 
when using other forms of explicit (or "hands-on") parallelism is to explicitly
disable it using the OpenMP runtime API and setting
<var>OMP_NUM_THREADS</var> in your shell:

<pre>
$ <kbd>export OMP_NUM_THREADS=1</kbd>
</pre>

Whether hands-off parallelism will use only one core or all cores by
default is dependent upon the compiler used to build the R executable you are 
using.  This is a result of the ambiguity of the OpenMP standard which leaves 
the default "greediness" of OpenMP up to the OpenMP implementors, and I've seen
different compilers choose both one and all cores if <var>OMP_NUM_THREADS</var>
is not explicitly defined.  Just be mindful of the possibilities.

{% call alert(type="info") %}
As of R 3.0.2, only the <code>colSums()</code> and <code>dist()</code> builtin
functions actually support OpenMP.  However, third-party libraries from CRAN can
also include OpenMP, and as long as your installation of R was built with OpenMP
support, this poor-man's parallelism will be enabled whenever such a library
is installed with <code>install.packages()</code>
{% endcall %}

<!-- references -->
[my parallel r github repository]: https://github.com/glennklockwood/paraR/tree/master/kmeans
[running r on hpc clusters]: on-hpc.html
[whats killing cloud interconnect performance]: https://blog.glennklockwood.com/2013/06/whats-killing-cloud-interconnect.html
[foreach cran page]: http://cran.r-project.org/web/packages/foreach/index.html
[revolution analytics foreach whitepaper]: http://www.revolutionanalytics.com/whitepaper/using-foreach-package-r-combine-iterators-and-other-functions
