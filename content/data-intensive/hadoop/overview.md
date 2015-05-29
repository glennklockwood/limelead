---
date: "2015-05-23T10:53:52-07:00"
draft: false
title: "Conceptual Overview of Map-Reduce and Hadoop"
shortTitle: Overview of Hadoop
parentdirs: [ 'data-intensive', 'hadoop' ]
---

<h2>Table of Contents</h2>
<ul>
  <li><a href="#intro">1. Introduction</a></li>
  <li><a href="#compare">2. Comparing Map/Reduce to Traditional Parallelism</a>
    <ul>
      <li><a href="#compare:trad">2.1. Traditional Parallel Applications</a></li>
      <li><a href="#compare:di">2.2. Data-intensive Applications</a></li>
    </ul>
  </li>
  <li><a href="#hadoop">3. Hadoop - A Map/Reduce Implementation</a>
    <ul>
      <li><a href="#hadoop:hdfs">3.1 The Magic of HDFS</a></li>
      <li><a href="#hadoop:mr">3.2 Map/Reduce Jobs</a>
        <ul>
          <li><a href="#hadoop:mr:map">3.2.1. The Map Step</a></li>
          <li><a href="#hadoop:mr:reduce">3.2.2. The Reduce Step</a></li>
        </ul>
      </li>
    </ul>
  </li>
  <li><a href="#summary">4. Summary</a></li>
</ul>

<h2 id="intro">1. Introduction</h2>
<p>This page serves as a 30,000-foot overview of the map/reduce programming
paradigm and the key features that make it useful for solving certain types of 
computing workloads that simply cannot be treated using traditional parallel 
computing methods.  It only covers the broad basics and is intended to 
provide you with the information you need to follow the subsequent pages I've 
written on:</p>
<ul>
  <li><a href="hadoop-streaming.php">Writing Hadoop Applications in Python using Hadoop Streaming</a></li>
  <li><a href="hadoop-vcfparse.php">Parsing VCF files with Hadoop Streaming</a></li>
  <li>Parallel R using Hadoop</li>
</ul>

<h2 id="compare">2. Comparing Map/Reduce to Traditional Parallelism</h2>
<p>In order to appreciate what map/reduce brings to the table, I think it is
most meaningful to contrast it to what I call <em>traditional</em> computing
problems.  I define "traditional" computing problems as those  which use 
libraries like MPI, OpenMP, CUDA, or pthreads to produce results by utilizing
multiple CPUs to perform some sort of numerical calculation concurrently.  
Problems that are well suited to being solved with these traditional methods 
typically share two common features:</p>
<ol>
  <li><strong>They are cpu-bound</strong>: the part of the problem that takes the most time is doing calculations involving floating point or integer arithmetic</li>
  <li><strong>Input data is gigabyte-scale</strong>: the data that is necessary to describe the conditions of the calculation are typically less than a hundred gigabytes, and very often only a few hundred megabytes at most</li>
</ol>
<p>Item #1 may seem trivial; after all, computers are meant to compute, so
wouldn't all of the problems that need to be parallelized be fundamentally
limited by how quickly the computer can do numerical calculations?</p>
<p>Traditionally, the answer to this question has been yes, but the 
technological landscape has been rapidly changing over the last decade.  
Sources of vast, unending data (e.g., social media, inexpensive genenome 
sequencing) have converged with inexpensive, high-capacity hard drives and the
advanced filesystems to support them, and now <em>data-intensive</em> computing
problems are emerging.  In contrast to the aforementioned traditional computing
problems, data-intensive problems demonstrate the following features:</p>
<ol>
  <li><strong>Input data is far beyond gigabyte-scale</strong>: datasets are commonly on the order of tens, hundreds, or thousands of terabytes</li>
  <li><strong>They are I/O-bound</strong>: it takes longer for the computer to get data from its permanent location to the CPU than it takes for the CPU to operate on that data</li>
</ol>

<h3 id="compare:trad">2.1. Traditional Parallel Applications</h3>
<p>To illustrate these differences, the following schematic depicts how your
typical traditionally parallel application works.</p>
<a href="parallelism-trad.png">
<img src="parallelism-trad.png" 
     alt="Program flow of a traditionally parallel problem" 
     style="display:block; margin:1em auto; width:600px; height:auto; border:0"/>
    </a>
<p>The input data is stored on some sort of remote storage device (a SAN, a 
file server serving files over NFS, a parallel Lustre or GPFS filesystem, etc; 
<span style="color:#777777;font-weight:bolder">grey cylinders</span>).  The
compute resources or elements (<span style="color:#6096C5;font-weight:bolder">blue 
boxes</span>) are abstract units that can represent MPI ranks, compute nodes,
or threads on a shared-memory system.</p>
<p>Upon launching a traditionally parallel application,</p>
<ol>
<li>A master parallel worker (MPI rank, thread, etc) reads the input data from disk 
(<span style="color:#00CC00;font-weight:bolder">green arrow</span>).  <span style="font-size:smaller"><br/>
NOTE: In some cases multiple ranks may use a parallel I/O API like MPI-IO to collectively read input data, but the filesystem on which the input data resides must be a high-performance filesystem that can sustain the required device- and network-read bandwidth.</span></li>
<li>The master worker then divides up the input data into chunks and sends parts to each of the other workers (<span style="color:#CC0000; font-weight:bolder">red arrows</span>).</li>
<li>All of the parallel workers compute their chunk of the input data</li>
<li>All of the parallel workers communicate their results with each other, then continue the next iteration of the calculation</li>
</ol>
<p>The fundamental limit to scalability here is step #1--the process of reading
the input data (<span style="color:#00CC00;font-weight:bolder">green 
arrow</span>) is performed serially.  Even if you can use MPI-IO to perform
the data ingestion in parallel, the data is separated from the compute 
resources (blue squares) by some pipe through which data can flow at 
some finite rate.  While it is possible to increase the speed of this connection
between your data and your compute resources by throwing more money at it 
(e.g., buying fast SSDs, faster storage networking, and/or more parallel 
storage servers), the cost of doing this does not scale linearly.</p>
<h3 id="compare:di">2.2. Data-intensive Applications</h3>
<p>The map/reduce paradigm is a completely different way of solving a certain 
subset of parallelizable problems that gets around the bottleneck of ingesting
input data from disk (that pesky green arrow).  Whereas traditional parallelism
brings <em>the data to the compute</em>, map/reduce does the opposite--it 
brings <em>the compute to the data</em>:</p>
<a href="parallelism-mr.png">
<img src="parallelism-mr.png" 
     alt="Program flow of a map/reduce parallel problem" 
     style="display:block; margin:1em auto; width:600px; height:auto; border:0"/>
    </a>
<p>In map/reduce, the input data is <em>not</em> stored on a separate, 
high-capacity storage system.  Rather, the data exists in little pieces and is 
permanently stored on the compute elements.  This allows our parallel 
procedure to follow these steps:</p>
<ol>
<li>We don't have to move any data since it is pre-divided and already exists on nodes capable of acting as computing elements</li>
<li>All of the parallel worker functions are sent to the nodes where their respective pieces of the input data already exist and do their calculations</li>
<li>All of the parallel workers communicate their results with each other, move data if necessary, then continue the next step of the calculation</li>
</ol>
<p>Thus, the only time data needs to be moved is when all of the parallel 
workers are communicating their results with each other in step #3.  There is
no more serial step where data is being loaded from a storage device before
being distributed to the computing resources because the data already exists
on the computing resources.</p>

<p>Of course, for the compute elements to be able to do their calculations on
these chunks of input data, the calculations and data must be all completely 
independent from the input data on other compute elements.  This is the 
principal constraint in map/reduce jobs: <em>map/reduce is ideally suited for 
trivially parallel calculations on large quantities of data</em>, but if each
worker's calculations depend on data that resides on other nodes, you will
begin to encounter rapidly diminishing returns.</p>

<h2 id="hadoop">3. Hadoop - A Map/Reduce Implementation</h2>
<p>Now that we've established a description of the map/reduce paradigm and the
concept of bringing compute to the data, we are equipped to look at Hadoop,
an actual implementation of map/reduce.</p>

<h3 id="hadoop:hdfs">3.1. The Magic of HDFS</h3>
<p>The idea underpinning map/reduce--bringing compute to the data instead of
the opposite--should sound like a very simple solution to the I/O bottleneck
inherent in traditional parallelism.  However, the devil is in the details, and
implementing a framework where a single large file is transparently diced up and 
distributed across multiple physical computing elements (all while appearing to
remain a single file to the user) is not trivial.</p>

<p>Hadoop, perhaps the most widely used map/reduce framework, accomplishes this
feat using HDFS, the Hadoop Distributed File System.  HDFS is fundamental to
Hadoop because it provides the data chunking and distribution across compute
elements necessary for map/reduce applications to be efficient.  Since we're now
talking about an actual map/reduce implementation and not an abstract concept,
let's refer to the abstract <em>compute elements</em> now as <em>compute 
nodes</em>.</p>

<p>HDFS exists as a filesystem into which you can copy files to and from in a
manner not unlike any other filesystem.  Many of the typical commands for 
manipulating files (<code>ls</code>, <code>mkdir</code>, <code>rm</code>,
<code>mv</code>, <code>cp</code>, <code>cat</code>, <code>tail</code>, and
<code>chmod</code>, to name a few) behave as you might expect in any other
standard filesystem (e.g., Linux's ext4).</p>

<p>The magical part of HDFS is what is going on just underneath the surface.
Although it appears to be a filesystem that contains files like any other, in
reality those files are distributed across multiple physical compute nodes:</p>

<a href="hdfs-magic.png">
<img src="hdfs-magic.png" 
     alt="Schematic depicting the magic of HDFS" 
     style="display:block; margin:1em auto; width:600px; height:auto; border:0"/>
    </a>

<p>When you copy a file into HDFS as depicted above, that file is transparently
sliced into 64 MB "chunks" and replicated three times for reliability.  Each of
these chunks are distributed to various compute nodes in the Hadoop cluster so 
that a given 64 MB chunk exists on three independent nodes.  Although 
physically chunked up and distributed in triplicate, all of your interactions 
with the file on HDFS still make it appear as the same single file you copied 
into HDFS initially.  Thus, HDFS handles all of the burden of slicing, 
distributing, and recombining your data for you.</p>

<table class="inset">
<tr><th>HDFS's chunk size and replication</th></tr>
<tr><td>
<p>The 64 MB chunk (block) size and the choice to replicate your data three 
times are only HDFS's default values.  These decisions can be changed:</p>
<ul>
  <li>the 64 MB block size can be modified by changing the 
    <code>dfs.block.size</code> property in <code>hdfs-site.xml</code>.  It
    is common to increase this to 128 MB in production environments.</li>
  <li>the replication factor can be modified by changing the
    <code>dfs.replication</code> property in <code>hdfs-site.xml</code>.  It
    can also be changed on a per-file basis by specifying <code>-D dfs.replication=1</code>
    on your <code>-put</code> command line, or using the <kbd>hadoop dfs 
    -setrep -w 1</kbd> command.</li>
</ul>
</td></tr></table>

<h3 id="hadoop:mr">3.2. Map/Reduce Jobs</h3>
<p>HDFS is an interesting technology in that it provides data distribution, 
replication, and automatic recovery in a user-space filesystem that is 
relatively easy to configure and, conceptually, easy to understand.  However, 
its true utility comes to light when map/reduce jobs are executed on data 
stored in HDFS.</p>
<p>As the name implies, map/reduce jobs are principally comprised of two steps:
the map step and the reduce step.  The overall workflow generally looks 
something like this:</p>
<a href="mapreduce-workflow.png">
<img src="mapreduce-workflow.png" 
     alt="Program flow of a map/reduce application" 
     style="display:block; margin:1em auto; width:600px; height:auto; border:0"/>
    </a>

<p>The left half of the diagram depicts the HDFS magic described in the previous
section, where the <kbd>hadoop dfs -copyFromLocal</kbd> command is used to move
a large data file into HDFS and it is automatically replicated and distributed 
across multiple physical compute nodes.  While this step of moving data into
HDFS is not strictly a part of a map/reduce job (i.e., your dataset may already 
have a permanent home on HDFS just like it would any other filesystem), 
a map/reduce job's input data must already exist on HDFS before the job can be
started.</p>

<h4 id="hadoop:mr:map">3.2.1. The Map Step</h4>
<p>Once a map/reduce job is initiated, the map step</p>
<ol>
  <li>Launches a number of parallel mappers across the compute nodes that
      contain chunks of your input data</li>
  <li>For each chunk, a mapper then "splits" the data into individual lines of
      text on newline characters (<code>\n</code>)</li>
  <li>Each split (line of text that was terminated by <code>\n</code>) is given
      to your mapper function</li>
  <li>Your mapper function is expected to turn each line into zero or more 
      key-value pairs and then "emit" these key-value pairs for the subsequent
      reduce step</li>
</ol>
<p>That is, <em>the map step's job is to transform your raw input data into a 
series of key-value pairs</em> with the expectation that these parsed 
key-value pairs can be analyzed meaningfully by the reduce step.  It's perfectly
fine for duplicate keys to be emitted by mappers.</p>

<table class="inset">
<tr><th>Input splitting</th></tr>
<tr><td>
<p>The decision to split your input data along newline characters is just the
default behavior, which assumes your input data is just an ascii text file.
You can change how input data is split before being passed to your mapper 
function using alternate <code>InputFormat</code>s.</p>
</td></tr></table>

<h4 id="hadoop:mr:reduce">3.2.2. The Reduce Step</h4>
<p>Once all of the mappers have finished digesting the input data and have 
emitted all of their key-value pairs, those key-value pairs are sorted according
to their keys and then passed on to the reducers.  The reducers are given 
key-value pairs in such a way that <em>all key-value pairs sharing the same 
key always go to the same reducer</em>.  The corollary is then that if one 
particular reducer has one specific key, it is guaranteed to have all other 
key-value pairs sharing that same key, and all those common keys will be in a 
continuous strip of key-value pairs that reducer received.</p>
<p>Your job's reducer function then does some sort of calculation based on
all of the values that share a common key.  For example, the reducer might
calculate the sum of all values for each key (e.g., <a 
href="hadoop-streaming.php">the word count example</a>).  The reducers then
emit key-value pairs back to HDFS where each key is unique, and each of these
unique keys' values are the result of the reducer function's calculation.</p>

<table class="inset">
<tr><th>The Sort and Shuffle</th></tr>
<tr><td>
<p>The process of sorting and distributing the mapper's output to the reducers
can be seen as a separate step often called the "shuffle".  What really happens
is that as mappers emit key-value pairs, the keys are passed through the 
<code>Partitioner</code> to determine which reducer they are sent to.</p>
<p>The default <code>Partitioner</code> is a function which hashes the key and 
then takes the modulus of this hash and the number of reducers to determine 
which reducer gets that key-value pair.  Since the hash of a given key will 
always be the same, all key-value pairs sharing the same key will get the same
output value from the <code>Partitioner</code> and therefore wind up on the
same reducer.</p>
<p>Once all key-value pairs are assigned to their reducers, the reducers all
sort their keys so that a single loop over all of a reducer's keys will examine
all the values of a single key before moving on to the next key.  As you will
see in my tutorial on <a href="hadoop-streaming.php">writing mappers and 
reducers in Python</a>, this is an essential feature of the Hadoop streaming
interface.</p>
</td></tr></table>

<p>This might sound a little complicated or abstract without an actual problem
or sample code to examine; it is far easier to demonstrate what the reducer 
does by <a href="hadoop-streaming.php">working through an example</a>.</p>

<h2 id="summary">4. Summary</h2>
<p>This conceptual overview of map/reduce and Hadoop is admittedly dry without
a meaningful example to accompany it, so here are the key points you should
take away:</p>
<ul>
<li>map/reduce brings <em>compute to the data</em> in contrast to traditional parallelism, which brings data to the compute resources</li>
<li>Hadoop accomplishes this by storing data in a replicated and distributed fashion on HDFS
  <ul>
    <li>HDFS stores files in chunks which are physically stored on multiple compute nodes</li>
    <li>HDFS still presents data to users and applications as single continuous files despite the above fact</li>
  </ul>
</li>
<li>map/reduce is ideal for operating on very large, flat (unstructured) datasets and perform trivially parallel operations on them</li>
<li>Hadoop jobs go through a map stage and a reduce stage where
  <ul>
    <li>the mapper transforms the raw input data into key-value pairs where multiple values for the same key may occur</li>
    <li>the reducer transforms all of the key-value pairs sharing a common key into a single key with a single value</li>
  </ul>
</li>
</ul>
<p>If you have any interest remaining after having read this, I strongly 
recommend looking through my tutorial on <a href="hadoop-streaming.php">Writing
Hadoop Applications in Python with Hadoop Streaming</a>.  That tutorial covers
much of the same material, but in the context of an actual problem (counting
the number of times each word appears in a text) with actual code written in
Python.</p>
