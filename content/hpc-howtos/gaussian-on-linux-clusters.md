---
title: Using Gaussian on Linux Clusters
shortTitle: Gaussian on Linux
date: 2013-11-13T00:00:00-07:00
template: page.jade
parentDirs: [ hpc-howtos ]
---

## <a name="contents"></a>Contents

* [Introduction](#intro)
* [Logging In](#login)
* [Getting Permission and Loading Gaussian](#loading)
* [Job Setup](#setup)
    * [Creating a job directory](#setup:mkdir)
    * [Transferring files to Trestles](#setup:xfer)
    * [Setting up the queue script](#setup:qscript)
* [Running Gaussian](#run)

## <a name="intro"></a>Introduction

A lot of XSEDE users request allocations on SDSC Trestles and Gordon because
we are one of two XSEDE sites (the other being [PSC and Blacklight][gaussian on blacklight]
with a Gaussian license that permits XSEDE users to use the software.  I've 
found that many start-up allocations wanting to use Gaussian involve users who
have never used a batch system, a remote resource, or even a command line.  In
the interest of providing a very quick crash course for such users, here are
my notes on making the jump from Gaussian on a PC or workstation to Gaussian 
on an SDSC XSEDE resource.

This guide assumes the reader has never used a batch system, an XSEDE
resource, or the Linux command line.  Since Trestles gets most of the new
Gaussian users on XSEDE, I will assume the reader is using that system.
Instructions for using Gordon are quite similar.

## <a name="login"></a>Logging into SDSC Trestles

The XSEDE User Portal has a [guide to getting started][xsede getting started guide],
and it covers all the options about which most users will want to know.  All
those options can be confusing at first, so for the sake of keeping it as
simple as possible, I'll lay out every step.

1. Go to the [XSEDE User Portal][xsede user portal]
2. Log in with your XSEDE username and password.  If you do not have an XSEDE
   User Portal account, you will have to create one and then get your project PI
   (your supervisor) to add that account to your group's project
3. Under the "MY XSEDE" tab, click the "[Accounts][xsede portal accounts tab]"
   option
4. Scroll down to Trestles and click the link under the "Login Name" column.
   This will take you to the GSI-SSH Terminal Java applet which will take a 
   while to load, then dump you at a black screen with white text.

This black screen should look something like this:

<pre style="background:black;color:#CCC">Rocks 5.4 (Maverick)
Profile built 10:09 13-Jan-2012

Kickstarted 10:17 13-Jan-2012
trestles Login Node
---------------------------------------------------------------------------
Welcome to the SDSC Trestles Appro Cluster

Trestles User Guide: http://www.sdsc.edu/us/resources/trestles
Questions: email help@xsede.org 
---------------------------------------------------------------------------

[username@trestles-login2 ~]$ </pre>

This is the Linux terminal, and the last line is your prompt which lists
your username, your current machine (trestles-login1 or trestles-login2), your
current directory (<code>~</code> is an abbreviation for your home directory),
and a dollar sign (<code>$</code>) which means you are logged in as a regular
(not administrative) user.

Typographic conventions hold that commands you are supposed to type at the
command prompt (also called "the shell") be preceded by a $ to represent the
shell prompt.  So, if this guide says to issue the following command:

<pre>
$ <kbd>pwd</kbd>
</pre>

you don't actually type the dollar sign.  It's just there to tell you to
type the <kbd>pwd</kbd> command in the Linux shell.  I also will forego the
black background from my samples below.  You know what your terminal looks 
like.

## <a name="loading"></a>Getting Permission and Loading Gaussian

Because Gaussian requires a license to use, new login accounts must be given
permission to run Gaussian before they can actually use it.  Chances are you
will need to request this permission by sending an email to [help@xsede.org](mailto:help@xsede.org).
Once your request is processed, it may take a few hours for the changes to take
effect.  If you want to check to see if you can run Gaussian, you can use the
<kbd>groups</kbd> command:

<pre>
$ <kbd>groups</kbd>
rut100 gaussian
</pre>

If you do _not_ see <code>gaussian</code> listed in the output of this command,
you will not be able to run Gaussian!

Once your account has been enabled for Gaussian, you can load its associated
module with this command:

<pre>
$ <kbd>module load gaussian</kbd>
</pre>

This will give you access the Gaussian commands like <code>formchk</code>,
<code>unfchk</code>, and of course <code>g09</code>.  However, **do not
skip ahead and just start running g09**!  If you do, you will make a
 lot of other users upset and you will get a sternly worded e-mail from me or 
one of my colleagues.

## <a name="setup"></a>Gaussian Job Setup

At this point I assume you have a Gaussian job you want to run, and it 
consists of the following files on your personal computer:

* <code>input.com</code> - your Gaussian input file
* <code>molecule.chk</code> - a Gaussian checkpoint file containing the data for the molecule you want to simulate.  If you are starting from scratch, the coordinates of your nuclei will be in your .com file and you will not have this checkpoint file.

### <a name="setup:mkdir"></a>Creating a job directory

The first thing you want to do is create a directory in which you want all 
this simulation's data to reside.  Do

<pre>
$ <kbd>mkdir job1</kbd>
</pre>

to create a directory called <code>job1</code>.  To then go into that directory,

<pre>
$ <kbd>cd job1</kbd>
</pre>

### <a name="setup:xfer"></a>Transferring files to Trestles

Now you need to transfer your Gaussian input files from your computer to 
Trestles.  The easiest way to do that is using a program like [WinSCP](winscp website)
(Windows) or [FileZilla](filezilla website) (Windows or Mac) that allows you
to drag-and-drop files from your personal computer to any XSEDE resource.
Connecting to your cluster will show your local files in the left pane and your
<code>job1</code> directory on the cluster in the right pane.  Double click the
job1 folder, and drag-and-drop your Gaussian job files onto the cluster..

<p>Back in your terminal session, you should be able to type the <kbd>ls</kbd>
command and see the files you just uploaded.</p>

<pre>
$ <kbd>ls</kbd>
input.com &nbsp;molecule.chk
</pre>

### <a name="setup:qscript"></a>Setting up the queue script

Up until now, the steps have been very generic and can be used by any user
to get started on Trestles.  However to actually run jobs on Trestles, Gordon,
or any other XSEDE supercomputer, you will have to interact with the _batch
system_ which is really what distinguishes using a shared supercomputer from
using your personal computer.

At SDSC we use use the [Torque Resource Manager][torque website] which is
comprised of a number of commands (e.g., <code>qsub</code>, <code>qstat</code>,
<code>qdel</code>, and <code>qmod</code>), and running your simulation through 
the batch system requires a _queue script_ to "glue" together the inner 
workings of Torque and Gaussian.

You can name these queue scripts whatever you want, but I like to give them all
the extensions of <code>.qsub</code>.  So, you will have to create a file
called <code>g09job.qsub</code> using a command-line text editor.  The
<code>nano</code> editor is perhaps the easiest to use.  Issue this command:

<pre>
$ <kbd>nano g09job.qsub</kbd>
</pre>

to create and edit a file called <code>g09job.qsub</code>.  You will see a 
screen like this:

<pre style="background:black;color:#CCC"><span style="color:black;background:#CCC">  GNU nano 1.3.12             File: g09job.qsub                                 </span>







<span style="color:black;background:#CCC">^G</span> Get Help  <span style="color:black;background:#CCC">^O</span> WriteOut  <span style="color:black;background:#CCC">^R</span> Read File <span style="color:black;background:#CCC">^Y</span> Prev Page <span style="color:black;background:#CCC">^K</span> Cut Text  <span style="color:black;background:#CCC">^C</span> Cur Pos
<span style="color:black;background:#CCC">^X</span> Exit      <span style="color:black;background:#CCC">^J</span> Justify   <span style="color:black;background:#CCC">^W</span> Where Is  <span style="color:black;background:#CCC">^V</span> Next Page <span style="color:black;background:#CCC">^U</span> UnCut Text<span style="color:black;background:#CCC">^T</span> To Spell</pre>

Some common nano commands are shown at the bottom: <kbd>ctrl+x</kbd> exits,
<kbd>ctrl+w</kbd> to search, etc.  You will need to paste the following lines 
into this new <code>g09job.qsub</code> file:

<pre>
#!/bin/bash
#PBS -q shared
#PBS -l nodes=1:ppn=16
#PBS -l walltime=02:30:00

. /etc/profile.d/modules.sh
module load gaussian
&nbsp;
cd $PBS_O_WORKDIR
export GAUSS_SCRDIR=/scratch/${USER}/${PBS_JOBID}
g09 &lt; input.com &gt; output.txt
</pre>

Now exit nano (<kbd>ctrl+x</kbd>) and say <kbd>yes</kbd> to "<samp>Save 
modified buffer (ANSWERING "No" WILL DESTROY CHANGES) ?</samp>" to save your 
changes.  This is the absolute bare minimum queue script you will need to run 
a Gaussian job, and for now, there are only two important lines.  The first one
is

<pre>
#PBS -l nodes=1:ppn=16
</pre>

which tells Torque that your job will require one node and sixteen CPU cores
on that node.  You will then have to modify your Gaussian input file, 
<code>input.com</code>, to actually use these sixteen cores.  Open up that
<code>input.com</code> file in nano and make sure the following red 
[Link 0 commands][gaussian manual link0 commands] are present above the Route
section:

<pre>
%chk=molecule.chk
<span style="color:red">%nproc=16</span>
<span style="color:red">%mem=31GB</span>
#p m062x/6-31+g(d) td=(Root=1,NStates=1) Freq NoSymm
</pre>

The <var>%nproc</var> option tells Gaussian to use 16 cores, which must be
the same as what your queue script requests.  The <var>%mem</var> option
specifies how much memory Gaussian can use.  On Trestles, there is a max of 2
GB available per core, but it is good practice to not specify this absolute max
since the operating system and other system programs on the node will also need
some memory.

Everything else in our Gaussian input file can remain unchanged.

The second important line of our <code>g09job.qsub</code> queue script is

<pre>
#PBS -l walltime=48:00:00
</pre>

which says that your job needs 48 hours to complete.  If you know your job
takes less time you can change that to, say,

<pre>
#PBS -l walltime=00:15:00
</pre>

for fifteen minutes.

## <a name="run"></a>Running Gaussian

Once you have your input file set up, you still cannot run Gaussian yet.
Unlike a workstation where you can just use the <code>g09</code> command, 
Trestles (and all modern supercomputers) requires you to submit your job to
a batch system that schedules and launches everyone's job in a fair manner.

You will have to submit jobs to Trestles using the <kbd>qsub</kbd> command 
and a job submission script which contains more Linux terminal commands to be 
executed on one of the compute nodes.  We've created <code>g09job.qsub</code>
above, so first type `ls` to ensure that <code>input.com</code>,
<code>molecule.chk</code> (if you had a checkpoint file you transferred from
your personal computer), and <code>g09job.qsub</code> are in your job directory.

Once you've got all your files together, actually running your Gaussian 
simulation is the simple matter of using the qsub command:

<pre>
$ <kbd>qsub g09job.qsub</kbd>
</pre>

The job may sit in queue for a while, and you can check its status by 
typing <kbd>qsub -u username</kbd>.  The second-to-last column (labeled "S") is
the job state.  Q means it's in queue, R means it is running, and C means the 
job has finished.

Once your job finishes, you should have a new file called 
<code>output.txt</code> which you can view using <code>cat</code>, edit using 
<code>nano</code>, and download to your computer using the XSEDE File 
Manager.

You can find a few more Gaussian submit scripts in [the GitHub repository for Trestles][github repository for trestles]
or [the GitHub repository for Gordon][github repository for gordon].

<!-- References -->
[gaussian on blacklight]: http://www.psc.edu/index.php/computational-resources/157#gaussian
[xsede getting started guide]: https://www.xsede.org/web/xup/documentation-overview
[xsede user portal]: https://portal.xsede.org/
[xsede portal accounts tab]: https://portal.xsede.org/group/xup/accounts
[winscp website]: http://winscp.net/eng/index.php
[filezilla website]: https://filezilla-project.org/
[torque website]: http://www.adaptivecomputing.com/products/open-source/torque/
[gaussian manual link0 commands]: http://www.gaussian.com/g_tech/g_ur/k_link0.htm
[github repository for trestles]: https://github.com/sdsc/sdsc-user/tree/master/jobscripts/trestles
[github repository for gordon]: https://github.com/sdsc/sdsc-user/tree/master/jobscripts/gordon
