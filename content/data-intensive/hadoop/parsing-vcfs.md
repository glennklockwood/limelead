---
date: "2014-06-28T00:00:00-07:00"
draft: false
title: "Parsing VCF Files with Hadoop Streaming"
shortTitle: "Parsing VCFs with Hadoop"
parentdirs: [ 'data-intensive', 'hadoop' ]
---

## Table of Contents

* [1. Introduction](#1-introduction)
* [2. Conceptual Overview](#2-conceptual-overview)
* [3. Install Python Library as Non-Root](#3-install-python-library-as-non-root)
* [4. The Mapper](#4-the-mapper)
* [5. The Reducer](#5-the-reducer)
* [6. Job Launch](#6-job-launch)
* [7. Scaling Behavior](#7-scaling-behavior)

## 1. Introduction

[Variant Call Format (VCF) files][vcf format] are a standard type of file used
to represent information about variations within a genome.  As with just about
anything genomic, these files can get very large very quickly (e.g., 
[dozens of gigabytes compressed][vcf repository]), and the process of
parsing them and converting them into any particular format can be conceptually
simple yet very data-intensive.

This example illustrates the following points that were missing in the
[simple wordcount example][hadoop streaming tutorial]:

* it uses a Python library specifically designed to parse VCF files that must be installed
* this Python library must be installed by a non-root user using a non-default version of Python
* this Python library is _not designed to be parallel in any way_

This guide builds upon my guide to [the basics of using Hadoop streaming][hadoop streaming tutorial],
so I recommend against trying to understand this guide without first going
through my simple wordcount example.  As with that guides, this guide comes
with supporting material on GitHub which is meant to work on SDSC Gordon.  I've
also used [semi-persistent Hadoop clusters][hadoop on hpc clusters] on
FutureGrid for much of the testing and development here, and this process should
work on a wide range of clusters with minimal modification.

## 2. Conceptual Overview

Files don't always come in a format that is a perfect for map/reduce, and the
output of your analysis doesn't always take the form of key/value pairs.  Thus,
I propose a few extra steps in the map/reduce pipeline highlighted in red:

* <span style="color:red">Proprocessing of data</span>
* Mapping
* Shuffling
* Reducing
* <span style="color:red">Postprocessing of data</span>

Within the context of the VCF files, preprocessing is necessary because the
VCF file contains a header which describes the format of the rest of the file.
Our mappers (or reducers) will all need to have this header information in order
for our VCF reader library to make sense of the actual data that gets fed to it
by Hadoop.  Thus, the preprocessing step here involves reading the _top_
of the input file and printing the header lines to stdout _until the first
non-header line is reached_:

<div class="shortcode">
{{< figure src="vcf.png" link="vcf.png" alt="schematic of VCF file preprocessing" >}}
</div>

We copy this printed header information to a separate file that exists 
outside of HDFS and don't bother messing with the actual VCF file's contents.
This obviates the need to actually read the entire VCF file since the act of
reading (or writing) that entire file is too big to do outside of HDFS.  Thus,
the proprocessing step leaves us with a header file (<code>header.txt</code>) 
and the original, untouched VCF input file.

The postprocessing step is dependent upon what we want to do with our VCF
data; when I was first getting into this application area, we were actually
using this process to transform the VCF data into a structured file that could
be <code>COPY FROM</code>ed to a PostgreSQL database.  This process of taking
the output from HDFS, connecting to the Postgres database, and <code>COPY 
FROM</code>ing that data was handled in the postprocessing step.

## 3. Install Python Library as Non-Root

Python makes it quite easy to [install libraries within having root privileges][install python without root]
on a machine.  I recommend using [VirtualEnv][virtualenv] to this end; it
essentially gives you a python installation that behaves as if you have
administrative privileges, and it sets up a very easy one-line script
to enable (or disable) its use.

The first step to setting up virtualenv is, of course, to download and
unpack it:

<pre>
$ <kbd>wget http://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.7.1.2.tar.gz</kbd>
$ <kbd>tar xzf virtualenv-1.7.1.2.tar.gz</kbd>
</pre>

You then have to decide the prefix for your personal python installation.  I
will pick <code>~/mypython</code>, but this is arbitrary.  You may decide you
want to have a separate Python virtualenv for each project.  Either way, execute
the <code>virtualenv.py</code> script you just unpacked and tell it where you
want to set up camp.  **However, don't forget to load the 
<code>python/2.7.3</code> module first if you want this virtualenv to use 
python2.7 instead of the system-default python2.4!**

<pre>
$ <kbd>module load python/2.7.3</kbd>
$ <kbd>python virtualenv-1.7.1.2/virtualenv.py ~/mypython</kbd>
</pre>

This will create a bunch of files including

* <code><var>$HOME</var>/mypython/bin</code>
* <code><var>$HOME</var>/mypython/bin/python</code> - your personal python executable that knows where to find the libraries you will be installing
* <code><var>$HOME</var>/mypython/bin/pip</code> - the application you will use to install Python libraries
* <code><var>$HOME</var>/mypython/bin/activate</code> - the script you'll source to activate this virtual environment
* <code><var>$HOME</var>/mypython/lib - where your python libraries will be installed</code>

Then you can "enable" this virutal environment by sourcing the 
<code>activate</code> script.  The next time you log in and want to use this
virtual environment though, remember to <kbd>module load python/2.7.3</kbd>
first!

<pre>
$ <kbd>source ~/mypython/bin/activate</kbd>
</pre>

Your prompt will change to indicate to indicate that you're operating with
the Python virtualenv active.  Then install all the Python libraries you want
using the <code>pip</code> command.  This tutorial will require the <code>pyvcf</code>
library:

<pre>
(mypython)$ <kbd>pip install pyvcf</kbd>
Downloading/unpacking pyvcf
  Downloading PyVCF-0.6.4.tar.gz
  Running setup.py egg_info for package pyvcf
...
Successfully installed pyvcf
Cleaning up...
</pre>

Now you can confirm that the library is accessible from within this 
virtualenv'ed python:

<pre>
(mypython)$ <kbd>python</kbd>
Python 2.7.3 (default, Feb  7 2013, 21:11:53) 
[GCC 4.1.2 20080704 (Red Hat 4.1.2-50)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
&gt;&gt;&gt;<kbd>import vcf</kbd>
&gt;&gt;&gt;
</pre>

## 4. The Mapper

This section is not done yet.  You can see the entire [mapper+reducer code
in my github][vcfparser code].

## 5. The Reducer

This section is not done yet.  You can see the entire [mapper+reducer code
in my github][vcfparser code].

## 6. Job Launch

There are a number of additions that must be made to our <a href="http://users.sdsc.edu/~glockwood/comp/hadoopstreaming.php#wordcount:run">previous wordcount example</a>
to run this VCF parsing map job.  Changes are highlighted in red below:

<pre>
$ <span style="color:red">module load python/2.7.3</span>
$ <span style="color:red">$HOME/mypython/bin/python $PWD/parsevcf.py -b patientData.vcf > header.txt</span>
$ hadoop dfs -mkdir data
$ hadoop dfs -copyFromLocal ./patientData.vcf data/
$ hadoop \
   jar /opt/hadoop/contrib/streaming/hadoop-streaming-1.0.3.jar \
   <span style="color:red">-D mapred.map.tasks=4 \</span>
   <span style="color:red">-D mapred.reduce.tasks=0 \</span>
   -mapper "<span style="color:red">$HOME/mypython/bin/python $PWD/parsevcf.py -m header.txt,0.30</span>" \
   <span style="color:#CCCCCC; text-decoration:line-through">-reducer ">python $PWD/parsevcf.py -r" \</span>
   -input "data/patientData.vcf"   \
   -output "data/output" \
   <span style="color:red">-cmdenv LD_LIBRARY_PATH=$LD_LIBRARY_PATH</span>
</pre>

The changes highlighted do the following:

1. <kbd>module load python/2.7.3</kbd> is necessary since our vcf library was
   installed for the python version provided by this module (2.7.x), not the 
   version provided by the system (2.4.x)
2. <kbd>python $PWD/parsevcf.py -b ...</kbd> is the preprocessing step we added
   to extract the VCF header into a separate file
3. <kbd>-D mapred.map.tasks=4</kbd> is really optional; it tells Hadoop that
   we would like (but won't necessarily get) four mappers
4. <kbd>-D mapred.reduce.tasks=0</kbd> is what disables the shuffle and reduce
   steps, since our example doesn't need to reduce anything
5. We explicitly specify the path to our custom Python (<kbd>$HOME/mypython/bin/python ...</kbd>) when
   calling our mapper/reducer scripts to ensure that Hadoop uses our custom 
   Python that has the PyVCF library installed.  The 
   <kbd>-m header.txt,0.30</kbd> is passed because our mapper function expects
   a comma-separated list containing
    1. the file containing just the VCF's header section (<code>header.txt</code>)
    2. the allele frequency above which a record gets printed (<code>0.30</code>)
6. We don't need to specify a <kbd>-reducer</kbd> since we set <code>mapred.reduce.tasks=0</code>
7. <kbd>-cmdenv LD_LIBRARY_PATH=$LD_LIBRARY_PATH</kbd> is <em>critical</em>
   and passes the contents of our environment's <var>$LD_LIBRARY_PATH</var>
   variable to the Hadoop streaming execution environment.  We modified the
   contents of this <var>$LD_LIBRARY_PATH</var> when we issued <kbd>module load
   python/2.7.3</kbd>, so this <code>-cmdenv</code> option ensures that the
   changes made when we loaded that module are propagated out to Hadoop.  You
   can specify multiple <code>-cmdenv</code> options if you need to propagate
   other environment variables that your mappers/reducers may need.

## 7. Scaling Behavior

This section is not done yet.

<hr style="margin-bottom:0">

<p style="font-size:x-small">This document was developed with support from the National Science Foundation
(NSF) under Grant No. 0910812 to Indiana University for "FutureGrid: An
Experimental, High-Performance Grid Test-bed." Any opinions, findings, and
conclusions or recommendations expressed in this material are those of the
author(s) and do not necessarily reflect the views of the NSF.</p>

<!-- references -->
[vcf format]: http://www.1000genomes.org/node/101
[vcf repository]: ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20110521/
[hadoop streaming tutorial]: streaming.md
[hadoop on hpc clusters]: on-hpc.html
[virtualenv]: http://www.virtualenv.org/en/latest/
[install python without root]: ../../hpc-howtos/installing-without-root.html#pylib
[vcfparser code]: https://github.com/glennklockwood/hpchadoop/tree/master/vcfparser.py
