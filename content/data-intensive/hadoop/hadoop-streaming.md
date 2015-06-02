---
date: "2014-06-28T00:00:00-07:00"
draft: false
title: "Writing Hadoop Applications in Python with Hadoop Streaming"
shortTitle: "Hadoop Streaming with Python"
parentdirs: [ 'data-intensive', 'hadoop' ]
---

## Contents

* [1. Introduction](#intro)
* [2. Review of Hadoop on HPC](#recap)
* [3. The Canonical Wordcount Ex](#wordcount)
    * [3.1. The Mapper](#wordcount:mapper)
    * [3.2. The Shuffle](#wordcount:shuffle)
    * [3.3. The Reducer](#wordcount:reducer)
    * [3.4. Running the Hadoop Job](#wordcount:run)
    * [3.5. Adjusting Parallelism](#wordcount:tweaks)
* [Next: Parsing VCF Files][parsing vcfs]

## <a name="intro"></a>1. Introduction

One of the unappetizing aspects of Hadoop to users of traditional HPC is that
it is written in Java.  Java is not designed to be a high-performance language
and, although I can only definitively speak for myself, I suspect that learning
it is not a high priority for domain scientists.  As it turns out though, 
Hadoop allows you to write map/reduce code in any language you want using the 
[Hadoop Streaming][hadoop streaming docs] interface.  This is a key feature in
making Hadoop more palatable for the scientific community, as it means turning
an existing Python or Perl script into a Hadoop job does not require learning
Java or derived Hadoop-centric languages like Pig.  The following guide
illustrates how you can run Hadoop jobs, written entirely in Python, without
ever having to mess with any other languages on [XSEDE][xsede website]'s 
[Gordon resource][gordon website] at SDSC.

Once the basics of running Python-based Hadoop jobs are covered, I will
illustrate a more practical example: 
[using Hadoop to parse a variant call format (VCF) file][parsing vcfs] using a
VCF parsing library you would install without root privileges on your
supercomputing account.

The wordcount example here is on [my GitHub account][glennklockwood/hpchadoop repo].
I've also got implementations of this in Perl and R posted there.

## <a name="recap"></a>2. Review of Hadoop on HPC

This guide assumes you are familiar with Hadoop and map/reduce at a 
conceptual level.  You should be in good shape after reading the 
[Conceptual Overview of Map/Reduce and Hadoop page][hadoop overview] I have.

This guide also assumes you understand the basics of running a Hadoop 
cluster on an HPC resource (supercomputer).  This can mean

* using a _non-interactive_, all-encapsulated job that does the Hadoop cluster
setup, job run, and Hadoop cluster teardown all in one job script, as described
by the [Gordon User Guide's page on Hadoop][gordon hadoop tutorial]
* creating a _semi-persistent_ Hadoop cluster using a job script and submitting
map/reduce jobs to it by hand, as described by my page on 
[Running Hadoop Clusters on Traditional Supercomputers][running hadoop on hpc]

For the purposes of keeping the process of specifically running Hadoop 
Streaming clear, I will assume we have a Hadoop cluster already spun up
on Gordon using my 
[semi-persistent Hadoop cluster script][semi-persistent hadoop cluster script]
and only provide the relevant <code>hadoop</code> commands involved in
submitting the Hadoop job to this Hadoop cluster.  If you want to go the
_non-interactive_ route, I have 
[a submit script on GitHub][non-interactive hadoop word count script]
that wraps this example problem into a single non-interactive Gordon job.

## <a name="wordcount"></a>3. The Canonical Wordcount Example

Counting the number of words in a large document is the "hello world" of 
map/reduce, and it is among the simplest of full map+reduce Hadoop jobs you 
can run.  Recalling that the **map step** transforms the raw input data into
key/value pairs and the **reduce step** transforms the key/value pairs into
your desired output, we can conceptually describe the act of counting words as

* the **map step** will take the raw text of our document (I will use 
[Herman Melville's classic, Moby Dick][moby dick fulltext]) and convert it to
key/value pairs.  Each key is a word, and all keys (words) will have a value of
1.
* the **reduce step** will combine all duplicate keys by adding
up their values.  Since every key (word) has a value of 1, this will reduce
our output to a list of unique keys, each with a value corresponding to that
key's (word's) count.

{{< figure src="wordcount-schematic.png" link="wordcount-schematic.png" alt="schematic of wordcount in the context of map-reduce" >}}

With Hadoop Streaming, we need to write a program that acts as the mapper
and a program that acts as the reducer.  These applications must interface with
input/output streams in such a way equivalent to the following series of 
pipes:

<pre>
$ <kbd>cat input.txt | ./mapper.py | sort | ./reducer.py > output.txt</kbd>
</pre>

That is, Hadoop Streaming sends raw data to the mapper via stdin, then sends 
the mapped key/value pairs to the reducer via stdin.

### <a name="wordcount:mapper"></a>3.1. The Mapper

The mapper, as described above, is quite simple to implement in Python.  It
will look something like this:

{{< highlight python  >}}
#!/usr/bin/env python

import sys

for line in sys.stdin:
    line = line.strip()
    keys = line.split()
    for key in keys:
        value = 1
        print( "%s\t%d" % (key, value) )
{{< /highlight >}}

where

<ol>
<li>Hadoop sends a line of text from the input file ("line" being defined by a string of text terminated by a linefeed character, <code>\n</code>)</li>
<li>Python strips all leading/trailing whitespace (<code>line.strip()</code></li>
<li>Python splits that line into a list of individual words along whitespace (<code>line.split()</code>)</li>
<li>For each word (which will become a key), we assign a value of 1 and then print the key-value pair on a single line, separated by a tab (<code>\t</code>)</li>
</ol>
<p>A more detailed explanation of this process can be found in <a 
href="http://developer.yahoo.com/hadoop/tutorial/module4.html">Yahoo's 
excellent Hadoop Tutorial</a>.</p>
### <a name="wordcount:shuffle"></a>3.2. The Shuffle
<p>A lot happens between the map and reduce steps that is largely transparent 
to the developer.  In brief, the output of the mappers is transformed and 
distributed to the reducers (termed <em>the shuffle</em> step) in such a way 
that</p>
<ol>
<li>All key/value pairs are sorted before being presented to the reducer function</li>
<li>All key/value pairs sharing the same key are sent to the same reducer</li>
</ol>
<p>These two points are important because</p>
<ol>
<li>As you read in key/value pairs, if you encounter a key that is different from the last key you processed, you know that that previous key will never appear again</li>
<li>If your keys are <em>all</em> the same, you will only use one reducer and gain <em>no parallelization</em>.  You should come up with a more unique key if this happens!</li>
</ol>
### <a name="wordcount:reducer">3.3. The Reducer
<p>The output from our mapper step will go to the reducer step sorted.  Thus,
we can loop over all input key/pairs and apply the following logic:</p>
<blockquote>
<div>If this key is the same as the previous key,</div>
<div> &nbsp; &nbsp;add this key's value to our running total.</div>
<div>Otherwise,</div>
<div> &nbsp; &nbsp;print out the previous key's name and the running total,</div>
<div> &nbsp; &nbsp;reset our running total to 0,</div>
<div> &nbsp; &nbsp;add this key's value to the running total, and</div>
<div> &nbsp; &nbsp;"this key" is now considered the "previous key"</div>
</blockquote>
<p>Translating this into Python and adding a little extra code to tighten up
the logic, we get</p>
<blockquote>
<div>#!/usr/bin/env python</div>
<div>&nbsp;</div>
<div>import sys</div>
<div>&nbsp;</div>
<div>last_key = None</div>
<div>running_total = 0</div>
<div>&nbsp;</div>
<div>for input_line in sys.stdin:</div>
<div> &nbsp; &nbsp;input_line = input_line.strip()</div>
<div> &nbsp; &nbsp;this_key, value = input_line.split("\t", 1)</div>
<div> &nbsp; &nbsp;value = int(value)</div>
<div>&nbsp;</div>
<div> &nbsp; &nbsp;if last_key == this_key:</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;running_total += value </div>
<div> &nbsp; &nbsp;else:</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;if last_key:</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;print( "%s\t%d" % (last_key, running_total) )</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;running_total = value</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;last_key = this_key </div>
<div>&nbsp;</div>
<div>if last_key == this_key:</div>
<div> &nbsp; &nbsp;print( "%s\t%d" % (last_key, running_total) )</div>
</blockquote>
### <a name="wordcount:run"></a>3.4. Running the Hadoop Job
<p>If we name the mapper script <code>mapper.py</code> and the reducing script
<code>reducer.py</code>, we would first want to download the input data (Moby
Dick) and load it into HDFS.  I purposely am renaming the copy stored in HDFS
to <code>mobydick.txt</code> instead of the original <code>pg2701.txt</code> to
highlight the location of the file:</p>
<blockquote>
<div>$ <kbd>wget http://www.gutenberg.org/cache/epub/2701/pg2701.txt</kbd></div>
<div>$ <kbd>hadoop dfs -mkdir wordcount</kbd></div>
<div>$ <kbd>hadoop dfs -copyFromLocal ./pg2701.txt wordcount/mobydick.txt</kbd></div>
</blockquote>
<p>You can verify that the file was loaded properly:</p>
<blockquote>
<div>$ <kbd>hadoop dfs -ls wordcount/mobydick.txt</kbd></div>
<div>Found 1 items</div>
<div>-rw-r--r-- &nbsp; 2 glock supergroup &nbsp; &nbsp;1257260 2013-07-17 13:24 /user/glock/wordcount/mobydick.txt</div>
</blockquote>
<p><strong>Before submitting the Hadoop job, you should make sure your mapper
and reducer scripts actually work.</strong>  This is just a matter of running
them through pipes on a little bit of sample data (e.g., the first 1000 lines of
Moby Dick):</p>
<blockquote>
<div>$ <kbd>head -n1000 pg2701.txt | ./mapper.py | sort | ./reducer.py</kbd></div>
<div>...</div>
<div>young &nbsp; 4</div>
<div>your &nbsp; &nbsp;16</div>
<div>yourself &nbsp; &nbsp;3</div>
<div>zephyr &nbsp;1</div>
</blockquote>
<p>Once you know the mapper/reducer scripts work without errors, we can plug
them into Hadoop.  We accomplish this by running the Hadoop Streaming jar file 
as our Hadoop job.  This <code>hadoop-streaming-X.Y.Z.jar</code> file comes 
with the standard Apache Hadoop distribution and should be in 
<code><var>$HADOOP_HOME</var>/contrib/streaming</code>
where <var>$HADOOP_HOME</var> is the base directory of your Hadoop installation
and <code>X.Y.Z</code> is the version of Hadoop you are running.  On Gordon 
the location is <code>/opt/hadoop/contrib/streaming/hadoop-streaming-1.0.3.jar</code>,
so our actual job launch command would look like</p>

<blockquote>
<div>$ <kbd>hadoop \</kbd></div>
<div><kbd> &nbsp; &nbsp;jar /opt/hadoop/contrib/streaming/hadoop-streaming-1.0.3.jar \</kbd></div>
<div><kbd> &nbsp; &nbsp;-mapper "<span style="color:green">python $PWD/mapper.py</span>" \</kbd></div>
<div><kbd> &nbsp; &nbsp;-reducer "<span style="color:green">python $PWD/reducer.py</span>" \</kbd></div>
<div><kbd> &nbsp; &nbsp;-input "wordcount/mobydick.txt" &nbsp; \</kbd></div>
<div><kbd> &nbsp; &nbsp;-output "wordcount/output"</kbd></div>
<div>&nbsp;</div>
<div>packageJobJar: [/scratch/glock/819550.gordon-fe2.local/hadoop-glock/data/hadoop-unjar4721749961014550860/] [] /tmp/streamjob7385577774459124859.jar tmpDir=null</div>
<div>13/07/17 19:26:16 INFO util.NativeCodeLoader: Loaded the native-hadoop library</div>
<div>13/07/17 19:26:16 WARN snappy.LoadSnappy: Snappy native library not loaded</div>
<div>13/07/17 19:26:16 INFO mapred.FileInputFormat: Total input paths to process : 1</div>
<div>13/07/17 19:26:16 INFO streaming.StreamJob: getLocalDirs(): [/scratch/glock/819550.gordon-fe2.local/hadoop-glock/data/mapred/local]</div>
<div>13/07/17 19:26:16 INFO streaming.StreamJob: Running job: <span style="color:red">job_201307171926_0001</span></div>
<div>13/07/17 19:26:16 INFO streaming.StreamJob: To kill this job, run:</div>
<div>13/07/17 19:26:16 INFO streaming.StreamJob: /opt/hadoop/libexec/../bin/hadoop job &nbsp;-Dmapred.job.tracker=gcn-13-34.ibnet0:54311 -kill job_201307171926_0001</div>
<div>13/07/17 19:26:16 INFO streaming.StreamJob: Tracking URL: http://gcn-13-34.ibnet0:50030/jobdetails.jsp?jobid=job_201307171926_0001</div>
</blockquote>

<p>And at this point, the job is running.  That "tracking URL" is a bit 
deceptive in that you probably won't be able to access it.  This is a really 
good example of how different of a world Hadoop cluster computing is from 
traditional HPC.  Fortunately, there is a command-line interface for monitoring
Hadoop jobs that is somewhat similar to <code>qstat</code>.  Noting the Hadoop 
jobid (highlighted in <span style="color:red">red</span> above), you can do:</p>

<blockquote>
<div>$ <kbd>hadoop -status job_201307171926_0001</kbd></div>
<div>Job: job_201307171926_0001</div>
<div>file: hdfs://gcn-13-34.ibnet0:54310/scratch/glock/819550.gordon-fe2.local/hadoop-glock/data/mapred/staging/glock/.staging/job_201307171926_0001/job.xml</div>
<div>tracking URL: http://gcn-13-34.ibnet0:50030/jobdetails.jsp?jobid=job_201307171926_0001</div>
<div>map() completion: 1.0 </div>
<div>reduce() completion: 1.0</div>
<div>&nbsp;</div>
<div>Counters: 30</div>
<div> &nbsp; &nbsp;Job Counters</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;<span style="color:red">Launched reduce tasks=1</span></div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;SLOTS_MILLIS_MAPS=16037</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;Total time spent by all reduces waiting after reserving slots (ms)=0</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;Total time spent by all maps waiting after reserving slots (ms)=0</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;<span style="color:red">Launched map tasks=2</span></div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;Data-local map tasks=2</div>
<div>...</div>
</blockquote>
<p>Since the hadoop streaming job runs in the foreground, you will have to
use another terminal (with <var>HADOOP_CONF_DIR</var> properly exported) to
check on the job while it runs.  However, you can also review the job metrics
after the job has finished.  In the example highlighted above, we can see that
the job only used one reduce task and two map tasks despite the cluster having
more than two nodes.</p>

## <a name="wordcount:tweaks"></a>3.5. Adjusting Parallelism

<p>Unlike with a traditional HPC job, the level of parallelism a Hadoop job
is not necessarily the full size of your compute resource.  The number of map
tasks is ultimately determined by the nature of your input data due to how
HDFS distributes chunks of data to your mappers.  You can "suggest" a number
of mappers when you submit the job though.  Doing so is a matter of applying
the change highlighted in <span style="color:green">green</span>:</p>
<blockquote>
<div>$ <kbd>hadoop jar /opt/hadoop/contrib/streaming/hadoop-streaming-1.0.3.jar \</kbd></div>
<div><kbd style="color:green"> &nbsp; &nbsp;-D mapred.map.tasks=4 \</kbd></div>
<div><kbd> &nbsp; &nbsp;-mapper "python $PWD/mapper.py" \</kbd></div>
<div><kbd> &nbsp; &nbsp;-reducer "python $PWD/reducer.py" \</kbd></div>
<div><kbd> &nbsp; &nbsp;-input wordcount/mobydick.txt \</kbd></div>
<div><kbd> &nbsp; &nbsp;-output wordcount/output</kbd></div>
<div>...</div>
<div>$ <kbd>hadoop -status job_201307172000_0001</kbd></div>
<div>...</div>
<div> &nbsp; &nbsp;Job Counters</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;<span style="color:red">Launched reduce tasks=1</span></div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;SLOTS_MILLIS_MAPS=24049 </div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;Total time spent by all reduces waiting after reserving slots (ms)=0</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;Total time spent by all maps waiting after reserving slots (ms)=0</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;Rack-local map tasks=1</div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;<span style="color:red">Launched map tasks=4</span></div>
<div> &nbsp; &nbsp; &nbsp; &nbsp;Data-local map tasks=3</div>
</blockquote>
<p>Similarly, you can add <code>-D mapred.reduce.tasks=4</code> to suggest the
number of reducers.  The reducer count is a little more flexible, and you can
set it to zero if you just want to apply a mapper to a large file.</p>

<p>With all this being said, the fact that Hadoop defaults to only two mappers
says something about the problem we're trying to solve--<strong>that is, this 
entire example is actually very stupid</strong>.  While it illustrates the
concepts quite neatly, counting words in a 1.2 MB file is a waste of time if
done through Hadoop because, by default, Hadoop assigns chunks to mappers in
increments of 64 MB.  Hadoop is meant to handle multi-gigabyte files, and
actually getting Hadoop streaming to do something useful for your research
often requires a bit more knowledge than what I've presented above.</p>

<p>To fill in these gaps, the next part of this tutorial, <a 
href="hadoop-vcfparse.php">Parsing VCF Files with Hadoop Streaming</a>, 
shows how I applied Hadoop to solve a real-world problem involving Python, 
some exotic Python libraries, and some not-completely-uniform files.</p>


<hr/>
<p style="padding-top:2em;font-size:x-small">This document was developed with 
support from the National Science Foundation (NSF) under Grant No. 0910812 to 
Indiana University for "FutureGrid: An Experimental, High-Performance Grid 
Test-bed." Any opinions, findings, and conclusions or recommendations 
expressed in this material are those of the author(s) and do not necessarily 
reflect the views of the NSF.  This work was made possible by the resources
afforded to me through a project entitled <a 
href="https://portal.futuregrid.org/projects/344">Exploring map/reduce 
frameworks for users of traditional HPC</a> on FutureGrid Hotel and Sierra.</p>

<!-- references -->

[parsing vcfs]: parsing-vcfs.html
[hadoop streaming docs]: http://hadoop.apache.org/docs/stable/streaming.html
[xsede website]: http://www.xsede.org/
[gordon website]: http://www.sdsc.edu/supercomputing/gordon/
[glennklockwood/hpchadoop repo]: https://github.com/glennklockwood/hpchadoop
[hadoop overview]: overview.html
[gordon hadoop tutorial]: http://www.sdsc.edu/support/user_guides/tutorials/hadoop.html
[running hadoop on hpc]: running-hadoop-on-hpc.html
[semi-persistent hadoop cluster script]: https://github.com/glennklockwood/hpchadoop/blob/master/hadoopcluster.xsede-gordon.qsub
[non-interactive hadoop word count script]: https://github.com/glennklockwood/hpchadoop/blob/master/wordcount.py/streaming-wordcount-py.xsede-gordon.qsub
[moby dick fulltext]: http://www.gutenberg.org/cache/epub/2701/pg2701.txt
