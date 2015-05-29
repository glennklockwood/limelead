---
title: Common Problems on Supercomputers
shortTitle: Common Problems
date: 2015-05-27T19:15:00-07:00
template: page.jade
parentDirs: [ hpc-howtos ]
---

There are a few errors messages that frequently get sent in by XSEDE users 
on Gordon and Trestles here at SDSC, and they're often unintuitive or cryptic 
to a point where I cannot fault users for not having a clue as to what they 
mean.  In the interests of making these sorts of problems googleable, this page
consists of common error messages (the symptoms), what these error messages
actually mean (the diagnosis), and what needs to happen to solve the problem
(the cure).

This page is a work in progress, and I try to add problems to it as I notice
repeat questions coming in over and over.  The last time I updated these 
questions was on December 2, 2013.

<hr>

## Content

* [Encrypted SSH Keys](#sshkey)
    * [Symptom](#sshkey:symp)
    * [Diagnosis: Your SSH key is encrypted](#sshkey:diag)
    * [Cure: Generate new, unecrypted SSH keys](#sshkey:cure)

<ul>
<li><a href="#deadnode">Node Failure</a>
  <ul>
    <li><a href="#deadnode:symp">Symptom</a></li>
    <li><a href="#deadnode:diag">Diagnosis: Your job's node is dead</a></li>
    <li><a href="#deadnode:cure">Cure: Contact User Services and wait</a></li>
  </ul>
</li>

<li><a href="#mpideath">MPI Dies</a>
  <ul>
    <li><a href="#mpideath:symp">Symptom</a></li>
    <li><a href="#mpideath:diag">Diagnosis: Your job broke</a></li>
    <li><a href="#mpideath:cure">Cure: Contact User Services</a></li>
  </ul>
</li>

<li><a href="#mpd">Wrong MPI Process Manager</a>
  <ul>
    <li><a href="#mpd:symp">Symptom</a></li>
    <li><a href="#mpd:diag">Diagnosis: You are using the wrong mpirun command</a></li>
    <li><a href="#mpd:cure">Cure: Fix your submit script</a></li>
  </ul>
</li>

<li><a href="#javaheap">Java Won't Start Due to Heap Error</a>
  <ul>
    <li><a href="#javaheap:symp">Symptom</a></li>
    <li><a href="#javaheap:diag">Diagnosis: You are hitting memory limitations on the login nodes</a></li>
    <li><a href="#javaheap:cure">Cure: Explicitly set your Java heap size</a></li>
  </ul>
</li>

<li><a href="#error12">MVAPICH2 job fails with <code>completion with error 12, vendor code=0x81</code></a>
  <ul>
    <li><a href="#error12:symp">Symptom</a></li>
    <li><a href="#error12:diag">Diagnosis: MVAPICH2 could not communicate over InfiniBand</a></li>
    <li><a href="#error12:cure">Cure: Increase timeouts in MVAPICH2</a></li>
  </ul>
</li>

</ul>

<!-- sshkey -->

## <a name="sshkey">Encrypted SSH Keys</a>

### <a name="sshkey:symp">Symptom:</a>

Your job status, either reported to you via e-mail or contained in your job's
error log, ends with errors that say

<pre>
Error in init phase...wait for cleanup!
</pre>

or

<pre>
Unable to copy file /opt/torque/spool/1234567.trestles-fe1.sdsc.edu.OU to glock@trestles-login1.sdsc.edu:/oasis/projects/nsf/sds129/glock/job_output.txt
&ast;&ast;&ast; error from copy
Permission denied (publickey,gssapi-keyex,gssapi-with-mic,password).
lost connection
&ast;&ast;&ast; end error output
Output retained on that host in:
/opt/torque/undelivered/1234567.trestles-fe1.sdsc.edu.OU

Unable to copy file /opt/torque/spool/1234567.trestles-fe1.sdsc.edu.ER to glock@trestles-login1.sdsc.edu:/oasis/projects/nsf/sds129/glock/job_errors.txt
&ast;&ast;&ast; error from copy
Permission denied (publickey,gssapi-keyex,gssapi-with-mic,password).
lost connection
&ast;&ast;&ast; end error output
Output retained on that host in: 
/opt/torque/undelivered/1234567.trestles-fe1.sdsc.edu.ER
</pre>

or

<pre>
(gnome-ssh-askpass:762): Gtk-WARNING &ast;&ast;: cannot open display:
The application 'gnome-ssh-askpass' lost its connection to the display trestles-login2.sdsc.edu:5.0;
most likely the X server was shut down or you killed/destroyed the application.
</pre>

### <a name="sshkey:diag">Diagnosis: Your SSH key is encrypted</a>

The MPI setup on SDSC Gordon and Trestles requires that users be able to
ssh within the cluster without being prompted for a passphrase.  This is 
accomplished using public-key authentication, which is configured the very first
time you log into Trestles or Gordon.  That very first time you logged in, you
should have been given a prompt like this:

<pre>
It doesn't appear that you have set up your ssh key.
This process will make the files:
    /home/glock/.ssh/id_rsa.pub
    /home/glock/.ssh/id_rsa
    /home/glock/.ssh/authorized_keys

Generating public/private rsa key pair.
Enter file in which to save the key (/home/glock/.ssh/id_rsa): 
Enter passphrase (empty for no passphrase):
</pre>

If you entered anything as your passphrase, you will encounter the above
errors.  If you want to verify that this is in fact your problem, you can do

<pre>
$ <kbd>grep -c '^Proc-Type: 4,ENCRYPTED$' ~/.ssh/id_rsa</kbd>
</pre>

If you see anything other than "0", this is the issue.

### <a name="sshkey:cure">Cure: Generate new, unecrypted SSH keys</a>

Provide the following two commands:

<pre>
$ <kbd>rm ~/.ssh/id_rsa.pub</kbd>
$ <kbd>bash /etc/profile.d/ssh-key.sh</kbd>
</pre>

You will see the message mentioned above:

    It doesn't appear that you have set up your ssh key.
    This process will make the files:
        /home/glock/.ssh/id_rsa.pub
        /home/glock/.ssh/id_rsa
        /home/glock/.ssh/authorized_keys

    Generating public/private rsa key pair.
    Enter file in which to save the key (/home/glock/.ssh/id_rsa):

Accept the default location by just pressing return.  Then you'll get a 
message like this:

    /home/glock/.ssh/id_rsa already exists.
    Overwrite (y/n)?

Say "y" here.  Then it will ask you to enter a passphrase.  Be sure to 
leave this blank (again, just hit return):

    Enter passphrase (empty for no passphrase): 
    Enter same passphrase again:

And then the problem should be resolved.

<!-- deadnode -->

## <a name="deadnode">Node Failure</a>

### <a name="deadnode:symp">Symptom:</a>

Your job stopped producing output but is still in the '<code>R</code>'
(running) state according to <code>qstat</code>.  When trying to 
<code>qdel</code>, you get this error:

<pre>
qdel: Server could not connect to MOM 1234567.trestles-fe1.sdsc.edu
</pre>

### <a name="deadnode:diag">Diagnosis: Your job's node is dead</a>

"MOM" is the program that runs on each compute node and receives jobs from
the queue to be executed.  All of the q&ast; commands (<code>qsub</code>, 
<code>qdel</code>, etc.) communicate with MOM and allow you to interact with
compute nodes from the login nodes.  When MOM cannot be contacted, the node is
effectively (or literally) unavailable so none of the regular q&ast; commands should
be expected to work.  In addition to <code>qdel</code> not working since MOM 
is not responding, MOM stops sending job updates to the queue manager so your
job's last known running state, <code>R</code>, gets frozen in time until the
queue manager is told differently.

Nodes don't often break to a point where MOM cannot be contacted, but the
most common cause is running the node out of memory.  If your application 
consumes more RAM than is available on the node, the whole node can crash and
need to be rebooted.  To get a better idea of if your job ran the node out of
memory, you can first find out which nodes the job was using (copy and paste
is helpful here):

<pre>
$ <kbd>qstat <span style="color:#FF0000">1234567</span> -f -x | grep -o '&lt;exec_host&gt;.&ast;&lt;/exec_host&gt;' | grep -Eo '(gcn|trestles)-[^-]&ast;-[^/]&ast;' | uniq</kbd>
trestles-10-32
</pre>

where <samp style="color:#FF0000">1234567</samp> is your job number and the
output (<samp>trestles-10-32</samp> in the example above) is your job's node(s).
Knowing this job node, then issue a command like this:

<pre>
$ <kbd>pbsnodes <span style="color:#FF0000">trestles-10-32</span> | grep -o 'availmem=[^ ,]&ast;'</kbd>
availmem=82256kb
</pre>

Bearing in mind that each node has 64 GB (that's 67,108,864kb) of RAM, if the
node has less than a gigabyte of RAM left (&lt; 1,048,576kb), it is likely that
your job did, in fact, run out of memory.  The above example, where only ~80 MB
of RAM was left, came from such a node.

### <a name="deadnode:cure">Cure: Contact User Services and wait</a>

There is nothing you can do about a downed node as a user.  Fortunately, 
the node's MOM will send an update to the queue manager right after the downed
node reboots, and your stuck job will clear the queue automatically.  For what 
it's worth, jobs that are terminated this way do <em>not</em> get charged SUs 
for the time they legitimately used before the node failure or the time spent 
frozen in that <code>R</code> state.

If your job remains stuck for longer than you'd like, you should send an
e-mail to the <a href="mailto:help@xsede.org">XSEDE helpdesk</a> so the 
administrators can purge the job for you.  This may be necessary in the rare 
case where the primary node for a job (the <em>mother superior</em> node) goes
down but the remaining compute nodes (<em>sister</em> nodes) remain up and
running your stuck, half-dead job.

<!-- mpideath -->

## <a name="mpideath">MPI Dies</a>

### <a name="mpideath:symp">Symptom:</a>

Your job died and the obvious error message e-mailed to you says something like this:
<pre>
[gcn-14-82.sdsc.edu:mpispawn_0][readline] Unexpected End-Of-File on file descriptor 6. MPI process died?
[gcn-14-82.sdsc.edu:mpispawn_0][mtpmi_processops] Error while reading PMI socket. MPI process died?
[gcn-14-82.sdsc.edu:mpispawn_0][child_handler] MPI process (rank: 0, pid: 15024) exited with status 252
</pre>

### <a name="mpideath:diag">Diagnosis: Your job broke</a>

This is a generic error message displayed whenever MPI terminates without 
calling <code>MPI_Finalize()</code>, and unfortunately it is not very helpful.
Your job should have generated an error file in the directory from which you 
submitted it, and it should contain the more specific error messages that
would make diagnosing the issue easier.

<em>This section is not yet complete</em>

### <a name="mpideath:cure">Cure: Contact User Services</a>

Contact the <a href="mailto:help@xsede.org">XSEDE helpdesk</a> if your error 
file does not contain anything that helps you figure out why your job broke. 
<em>This section is not yet complete</em>

<!-- mpd -->

## <a name="mpd">Wrong MPI Process Manager</a>

### <a name="mpd:symp">Symptom:</a>

Upon submission, your job promptly fails with this error message:

<pre>
mpiexec_trestles-9-11.local: cannot connect to local mpd (/tmp/mpd2.console_case); possible causes:
 1. no mpd is running on this host
 2. an mpd is running but was started without a "console" (-n option)
In case 1, you can start an mpd on this host with:
  mpd 
and you will be able to run jobs just on this host.
For more details on starting mpds on a set of hosts, see
the MVAPICH2 User Guide.
</pre>

### <a name="mpd:diag">Diagnosis: You are using the wrong mpirun command</a>

There are two common causes of this error.

#### 1. If you are trying to use OpenMPI...

<em>This section is not yet complete.</em> In brief, OpenMPI needs to be 
explicitly loaded from within the submit script when running OpenMPI jobs.

#### 2. If you are NOT trying to use OpenMPI or aren't sure...

You aren't following directions.  If you use the <code>mpirun</code> command 
on Trestles, you will probably see this behavior because Trestles does not 
support <code>mpirun</code>.  According to the <a href="http://www.sdsc.edu/us/resources/trestles/trestles_jobs.html">Trestles
User Guide</a>, you need to launch your MPI jobs using <kbd>mpirun_rsh</kbd>
when using mvapich2.

### <a name="mpd:cure">Cure: Fix your submit script</a>

<em>This section is not yet complete</em>

<!-- java heap problem -->

## <a name="javaheap">Java Won't Start Due to Heap Error</a>

### <a name="javaheap:symp">Symptom:</a>

You try to do something involving Java on either Gordon's or Trestles' 
login nodes (<code>java</code>, <code>javac</code>, <code>ant</code>, etc) but 
it won't run because of this error:

<pre>
$ <kbd>ant</kbd>
Error occurred during initialization of VM
Could not reserve enough space for object heap
Could not create the Java virtual machine.
</pre>

### <a name="javaheap:diag">Diagnosis: You are hitting memory limitations on the login nodes</a>

Because the login nodes for Gordon and Trestles are shared across all users,
there are limitations on how much memory any single user can consume (e.g., see
the output of <kbd>ulimit -m -v</kbd>).  Java manages memory is somewhat of a 
peculiar way, and it is not uncommon for certain Java applications to try to 
allocate more memory than we allow and throw these strange errors about the
object heap.

### <a name="javaheap:cure">Cure: Explicitly set your Java heap size</a>

Most of the time, you can tell Java to not be so greedy when it starts by
passing it the <code>-Xmx256m</code> option to force it to allocate only
256 MB of object heap when it starts.  This might get annoying and doesn't
always work for Java-derived applications, so a more universal fix is to add
the following environment variable definition to your <code>.bashrc</code>
file:

<pre>
export _JAVA_OPTIONS=-Xmx256m
</pre>

You may find that 256 MB is not enough, so you can similarly try to use
<code>-Xmx512m</code> if you continue to experience difficulties.

If you still need more heap, you will probably have to run your Java
application on a compute node.  Compute nodes have no limitation on the
amount of memory you can use, so start an interactive job:

<pre>
# For Trestles:
$ <kbd>qsub -I -l nodes=1:ppn=32,walltime=1:00:00 -q normal</kbd>
&nbsp;
# Or for Gordon:
$ <kbd>qsub -I -l nodes=1:ppn=16:native,walltime=1:00:00 -q normal</kbd>
</pre>

and then run your Java task there.

<!--  [0->17] send desc error, wc_opcode=0
[0->17] wc.status=12, wc.wr_id=0x18cc840, wc.opcode=0, vbuf->phead->type=55 = MPIDI_CH3_PKT_CLOSE
[gcn-4-11.sdsc.edu:mpi_rank_10][MPIDI_CH3I_MRAILI_Cq_poll] src/mpid/ch3/channels/mrail/src/gen2/ibv_channel_manager.c:586: [] Got completion with error 12, vendor code=0x81, dest rank=17
-->

## <a name="error12">MVAPICH2 job fails with completion with error 12, vendor code=0x81</a>

### <a name="error12:symp">Symptom:</a>

Your job ran for a minute or two, produced little or no output, then died 
with a bunch of errors that look something like this:

<pre>
[0-&gt;17] send desc error, wc_opcode=0
[0-&gt;17] wc.status=12, wc.wr_id=0x18cc840, wc.opcode=0, vbuf-&gt;phead-&gt;type=55 = MPIDI_CH3_PKT_CLOSE
[gcn-4-11.sdsc.edu:mpi_rank_10][MPIDI_CH3I_MRAILI_Cq_poll] src/mpid/ch3/channels/mrail/src/gen2/ibv_channel_manager.c:586: [] Got completion with error 12, vendor code=0x81, dest rank=17
</pre>

### <a name="error12:diag">Diagnosis: MVAPICH2 could not communicate over InfiniBand</a>

Unfortunately this error is pretty generic and only tells you that your job 
failed when an MPI call to a remote host over the InfiniBand fabric could not
complete and timed out.  This could be a problem with

1. your code's communication patterns and algorithms
2. the MVAPICH2 settings being used
3. the InfiniBand fabric itself
4. a combination of all of these

The majority of the time this error comes up, the culprit is #4: a 
combination of InfiniBand congestion caused by other users and your code 
cause timeouts that can be fixed with a little bit of tweaking of the
MVAPICH2 parameters.

### <a name="error12:cure">Cure: Increase timeouts in MVAPICH2</a>

#### Check your MVAPICH2 multi-rail settings

If you encounter this problem on Gordon (or any other system with a 
multi-rail InfiniBand fabric), first rule out that the problem is with your 
MVAPICH2 environment.  Log into a compute node (this will <em>NOT</em> work
on a login node) and issue the following command:

<pre>
$ <kbd>env|grep MV2</kbd>
MV2_IBA_HCA=mlx4_0
MV2_NUM_HCAS=1
</pre>

If this <kbd>env|grep MV2</kbd> does <em>not</em> return the above two
environment variables, there is a problem with your environment which will
always cause MVAPICH2 to hang.  The remedy is to add the following two lines
to your <code>~/.bashrc</code> file:

<pre>
export MV2_IBA_HCA=mlx4_0
export MV2_NUM_HCAS=1
</pre>

#### Increase your MVAPICH2 timeout thresholds

If your <code>MV2_IBA_HCA</code> and <code>MV2_NUM_HCAS</code> are set
correctly on your job's compute nodes, your code may just be running into
very high latencies.  This can happen on very large jobs and when doing
global communications, and the solution is to try increasing your timeout
settings for MVAPICH2 via the <code>MV2_DEFAULT_TIME_OUT</code> environment
variable:

<pre>
$ <kbd>mpirun_rsh -np 2048 -hostfile $PBS_NODEFILE MV2_DEFAULT_TIME_OUT=23 ./mycode.x</kbd>
</pre>

or if you are using mpiexec.hydra,

<pre>
$ <kbd>MV2_DEFAULT_TIME_OUT=23 /home/diag/opt/hydra/bin/mpiexec.hydra ./mycode.x</kbd>
</pre>

If you still persistently get these <code>Got completion with error 12, 
vendor code=0x81</code> errors, contact <a href="mailto:help@xsede.org">help@xsede.org</a>
and provide the error log for your job as well as its submit script and the directory
containing the job's input files.
