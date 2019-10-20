---
title: Using R on HPC Clusters
shortTitle: R on HPC
order: 0
---

## 1. Introduction

This page covers the gnarly system-specific overhead required to run R in
parallel on shared computing resources such as clusters and supercomputers.
It does _not_ cover the conceptual or practical details of specific parallel
libraries available to R programmers; this information can be found in my page
on [Parallel Options for R][parallel options].  Rather, it covers what you
need to know about installing libraries and running R on someone else's
supercomputer rather than your personal laptop or desktop.

## 2. Installing Libraries

### 2.1. Most Libraries

Users are typically not allowed to install R libraries globally on most
clusters, but R makes it very easy for users to install libraries in their home
directories.  To do this, fire up R and when presented with the 
<code>&gt; </code> prompt, use the <kbd>install.packages()</kbd> method to
install things:

<pre>
&gt; <kbd>install.packages('doSNOW')</kbd>
Installing package(s) into '/opt/R/local/lib'
(as 'lib' is unspecified)
Warning in install.packages("doSNOW") :
  'lib = "/opt/R/local/lib"' is not writable
Would you like to use a personal library instead?  (y/n)
</pre>

This error comes up because you can't install libraries system-wide as a 
non-root user.  Say <kbd>y</kbd> and accept the default which should be 
something similar to <samp>~/R/x86_64-unknown-linux-gnu-library/3.0</samp>.  
Pick a mirror and let her rip.  If you want to install multiple packages at 
once, you can just do something like

<pre>&gt; <kbd>install.packages(c('multicore','doMC'))</kbd></pre>

Some libraries are more complicated than others, and you may eventually get
an error like this:

<pre>
&gt; <kbd> install.packages('lmtest');</kbd>
Installing package(s) into '/home/glock/R/x86_64-unknown-linux-gnu-library/2.15'
(as 'lib' is unspecified)
trying URL 'http://cran.stat.ucla.edu/src/contrib/lmtest_0.9-30.tar.gz'
Content type 'application/x-tar' length 176106 bytes (171 Kb)
opened URL
==================================================
downloaded 171 Kb
&nbsp; 
* installing *source* package 'lmtest' ...
** package 'lmtest' successfully unpacked and MD5 sums checked
** libs
gfortran   -fpic  -g -O2  -c pan.f -o pan.o
gcc -std=gnu99 -shared -L/usr/local/lib64 -o lmtest.so pan.o -lgfortran -lm -lquadmath
<span style="font-weight:bold;color:red">/usr/bin/ld: cannot find -lquadmath</span>
make: *** [lmtest.so] Error 2
ERROR: compilation failed for package 'lmtest'
* removing '/home/glock/R/x86_64-unknown-linux-gnu-library/2.15/lmtest'

The downloaded source packages are in
    '/tmp/RtmpDTJxhk/downloaded_packages'
Warning message:
In install.packages("lmtest") :
  installation of package 'lmtest' had non-zero exit status
</pre>

The relevant part is the failure to compile the portion of the module written
in Fortran due to <samp>/usr/bin/ld: cannot find -lquadmath</samp>.  This 
missing quadmath library first appeared in GNU GCC 4.6, so if this error comes
up, it means your default gcc is not the same one used to compile R.  On SDSC's
systems, this is remedied by doing <kbd>module load gnubase</kbd>.

Alternatively, you might see an error like this:

<pre>
Error: in routine alloca() there is a
stack overflow: thread 0, max 137437318994KB, used 0KB, request 48B
</pre>

Again, this is caused by <code>gnu/4.8.2</code> not being loaded.  The 
following commands will remedy the issue on Trestles:

<pre>
$ <kbd>module unload pgi</kbd>
$ <kbd>module load gnu/4.8.2 openmpi_ib R</kbd>
</pre>

### 2.2. Rmpi

In order to use distributed memory parallelism (i.e., multi-node jobs) 
within R, you will need to use <code>Rmpi</code> in some form or another.
Under the hood, the <code>ClusterApply</code> and related functions provided in
the <code>parallel</code> library use <code>Rmpi</code> as the most efficient
way to utilize the high-performance interconnect available on 
supercomputers.

It's a lot harder to install <code>Rmpi</code> using <code>install.packages()</code> 
because you have to feed the library installation process some system-specific
library locations before it will work correctly.  So, exit R and return to 
the Linux prompt.  Download the Rmpi source distribution:

<pre>
$ <kbd>wget http://cran.r-project.org/src/contrib/Rmpi_0.6-3.tar.gz</kbd>
</pre>

<code>Rmpi 0.6-3</code> was the most recent version at the time I wrote this,
 but you can get the most recent version's download URL from the [Rmpi page at
CRAN][rmpi website].  Once you have downloaded the file, make sure you have
the proper _compiler_ and _MPI library_ modules loaded (<code>gnu</code> and
<code>openmpi_ib</code> on SDSC's systems), then issue the install command with
the paths to your MPI library: 

<pre>
$ <kbd>mkdir -p <span style="color:green">~/R/x86_64-unknown-linux-gnu-library/3.0</span></kbd>
$ <kbd>R CMD INSTALL \</kbd>
<kbd>    --configure-vars="CPPFLAGS=-I<span style="color:green">$MPIHOME</span>/include LDFLAGS='-L<span style="color:green">$MPIHOME</span>/lib'" \</kbd>
<kbd>    --configure-args="--with-Rmpi-include=<span style="color:green">$MPIHOME</span>/include \</kbd>
<kbd>                      --with-Rmpi-libpath=<span style="color:green">$MPIHOME</span>/lib \</kbd>
<kbd>                      --with-Rmpi-type=OPENMPI" \</kbd>
<kbd>    -l <span style="color:green">~/R/x86_64-unknown-linux-gnu-library/3.0 Rmpi_0.6-3.tar.gz</span></kbd>
</pre>

Be sure to double-check the text in green!  In particular, your R library
directory's version (<samp>3.0</samp> in the example above) is the same as the
version of R you're using, and be sure to fill in <var>$MPIHOME</var> with the
path to your MPI library (<kbd>which mpicc</kbd> might give you a hint).  If
all goes well, you should see a lot of garbage that ends with

<pre>
gcc -std=gnu99 -shared -L/usr/local/lib64 ...
installing to /home/glock/R/x86_64-unknown-linux-gnu-library/3.0/Rmpi/libs
** R
** demo
** inst
** preparing package for lazy loading
** help
*** installing help indices
** building package indices
** testing if installed package can be loaded
--------------------------------------------------------------------------
The OpenFabrics (openib) BTL failed to initialize while trying to
allocate some locked memory.  This typically can indicate that the
memlock limits are set too low.  For most HPC installations, the
memlock limits should be set to "unlimited".  The failure occured
here:
&nbsp; 
  Local host:    trestles-login2.sdsc.edu
  OMPI source:   btl_openib_component.c:1216
  Function:      ompi_free_list_init_ex_new()
  Device:        mlx4_0
  Memlock limit: 65536
&nbsp; 
You may need to consult with your system administrator to get this
problem fixed.  This FAQ entry on the Open MPI web site may also be
helpful:
&nbsp; 
    http://www.open-mpi.org/faq/?category=openfabrics#ib-locked-pages
--------------------------------------------------------------------------
--------------------------------------------------------------------------
WARNING: There was an error initializing an OpenFabrics device.
 
  Local host:   trestles-login2.sdsc.edu
  Local device: mlx4_0
--------------------------------------------------------------------------
* DONE (Rmpi)
</pre>

That error about the OpenFabrics device is nothing to worry about; it happens
because the test is running on one of the cluster's login nodes (where you are
doing all of this) and cannot access the MPI execution environment that real
jobs on compute nodes use.

At this point you should have <code>Rmpi</code> installed, and this allows 
the <code>snow</code>  package to use MPI for distributed computing.  If you 
run into an error that looks like this:

<pre>
...
** preparing package for lazy loading
** help
*** installing help indices
** building package indices
** testing if installed package can be loaded
Error: in routine alloca() there is a
stack overflow: thread 0, max 10228KB, used 0KB, request 48B
ERROR: loading failed
* removing '/home/glock/R/x86_64-unknown-linux-gnu-library/2.15/Rmpi'
</pre>

You probably forgot to load the prerequisite modules correctly.  Purge all of
your currently loaded modules, then re-load the ones necessary to build R
libraries

<pre>
$ <kbd>module purge</kbd>
$ <kbd>module load gnu/4.6.1 openmpi R</kbd>
$ <kbd>R CMD INSTALL</kbd> --configure-vars=...
</pre>

{% call inset("Note about MVAPICH2", "info") %}
If you log into Gordon, start an interactive job (do not run R on the login
nodes!), and try run a snow-based script which calls <code>ClusterApply</code>,
you may find that it just segfaults:

<pre>
$ <kbd>mpirun_rsh -np 1 -hostfile $PBS_NODEFILE $(which R) CMD BATCH ./snowapp.R</kbd>
[gcn-14-17.sdsc.edu:mpispawn_0][readline] Unexpected End-Of-File on file descriptor 5. MPI process died?
[gcn-14-17.sdsc.edu:mpispawn_0][mtpmi_processops] Error while reading PMI socket. MPI process died?
/opt/R/lib64/R/bin/BATCH: line 60: 130758 Segmentation fault      ${R_HOME}/bin/R -f ${in} ${opts} ${R_BATCH_OPTIONS} > ${out} 2>&amp;1
[gcn-14-17.sdsc.edu:mpispawn_0][child_handler] MPI process (rank: 0, pid: 130753) exited with status 139
</pre>

If you instead try to use mpiexec (which is mpiexec.hydra) you will instead
get this error:

<pre>
*** caught segfault ***
address 0x5ddcbc7, cause 'memory not mapped'
&nbsp; 
Traceback:
 1: .Call("mpi_comm_spawn", as.character(slave), as.character(slavearg),     as.integer(nslaves), as.integer(info), as.integer(root),     as.integer(intercomm), as.integer(quiet), PACKAGE = "Rmpi")
 2: mpi.comm.spawn(slave = mpitask, slavearg = args, nslaves = count,     intercomm = intercomm)
 3: snow::makeMPIcluster(spec, ...)
 4: makeCluster(10, type = "MPI")
aborting ...
</pre>

Alternatively, your application may produce this error instead of 
segfaulting:

<pre>
Error in mpi.universe.size() : 
  This function is not supported under MPI 1.2
Calls: mpi.spawn.Rslaves -> mpi.comm.spawn -> mpi.universe.size
Execution halted
</pre>

These errors all indicate a major bug in the Rmpi package which remains 
fixed.  I take this to mean that **Rmpi simply does not work with 
MVAPICH2.  Use OpenMPI when using Rmpi or its derivatives.**  You can
do this by loading the <code>openmpi_ib</code> module before loading the 
<code>R</code> module.

{% endcall %}

## 3. Submitting R Jobs to a Cluster

On personal workstations, R is often used by running the R shell in an
interactive fashion and either typing in commands or doing something like 
<kbd>source('script.R')</kbd>.  Supercomputers generally operate through batch
schedulers though, so you will want to get your R script running 
non-interactively.  There are a few ways of doing this:

1. Add <samp>#!/usr/bin/env Rscript</samp> to the very top of your R script and
   make it executable (<kbd>chmod +x script.R</kbd>), then just run the script
   as you would a bash script or any program (<kbd>./script.R</kbd>)
2. Call Rscript with the script's name as a command line parameter: 
   <kbd>Rscript script.R</kbd>.  I've seen this break an otherwise working
   R script though, and I never got to the bottom of it.
3. Call <kbd>R CMD BATCH script.R</kbd>

I am going to use #3 in the following examples because it is the most proper
way.  The sample job submit scripts that follow are for Torque, which is the 
batch manager we run on SDSC Gordon and Trestles.  These scripts can be 
trivially adapted to SGE/Grid Engine, Slurm, LSF, Load Leveler, or whatever 
other batch system your system may have.

### 3.1. Running Serial R Jobs

Running an R script in serial is quite straightforward.  On XSEDE's Gordon
resource at SDSC, your queue script should look something like this:

<pre>
#!/bin/sh
#PBS -q normal
#PBS -l nodes=1:ppn=16:native
#PBS -l walltime=0:05:00
&nbsp; 
module load R
&nbsp; 
cd $PBS_O_WORKDIR
&nbsp; 
export OMP_NUM_THREADS=1 
R CMD BATCH test.serial.R
</pre>

The peculiar bit to note here is our use of <code>export OMP_NUM_THREADS=1</code>.
If you don't specify this, R will use as many threads as it can grab if your
script uses a library that supports multithreading.  This isn't bad per se, but
explicitly specifying <var>OMP_NUM_THREADS</var> is good practice--that way you
always know exactly how many cores your script will use.

### 3.2. Running Shared-Memory R Jobs

Running shared-memory parallel R on a single node is also quite simple.  Here
is a sample queue script that uses all 16 cores on a dedicated (non-shared)
node.

<pre>
#!/bin/sh
#PBS -q normal
#PBS -l nodes=1:ppn=16:native
#PBS -l walltime=0:05:00
&nbsp; 
module load R
&nbsp; 
cd $PBS_O_WORKDIR
&nbsp; 
export OMP_NUM_THREADS=1
R CMD BATCH test.doMC.R
</pre>

It is actually the same script as the serial version.  Bear in mind that the
<var>OMP_NUM_THREADS</var> <em>only</em> controls the number of cores used by
libraries which support OpenMP.  By comparison, the <code>multicore</code> (and
<code>parallel</code>) libraries do <em>not</em> use OpenMP; they let you 
control the number of cores from within R.

### 3.3. Running Parallel Jobs with snow/doSNOW

Snow (and its derived libraries) does its own process managements, so you
_must_ run it as if it were a one-way MPI job.  For example,

<pre>
#!/bin/sh
#PBS -q normal
#PBS -l nodes=2:ppn=16:native
#PBS -l walltime=0:05:00
&nbsp; 
module swap mvapich2_ib openmpi_ib
module load R
&nbsp; 
cd $PBS_O_WORKDIR
&nbsp; 
export OMP_NUM_THREADS=1
mpirun <span style="color:#CC0000">-np 1</span> -hostfile $PBS_NODEFILE R CMD BATCH test.doSNOW.R
</pre>

If you forget to request only one core, your job will fail and you will get
a lot of horrific errors:

<pre>
CMA: unable to open RDMA device
CMA: unable to open RDMA device
[[59223,26],16][btl_openib_component.c:1493:init_one_device] error obtaining device context for mlx4_0 errno says No such device
[[59223,27],23][btl_openib_component.c:1493:init_one_device] error obtaining device context for mlx4_0 errno says No such device
[[59223,31],5][btl_openib_component.c:1493:init_one_device] error obtaining device context for mlx4_0 errno says No such device
</pre>

This is because the R script winds up running in duplicate, and each 
duplicate tries to spawn a full complement of its own MPI ranks.  Thus, instead
of getting 2&#215;16 ranks, you get (2&#215;16)&#215;(2&#215;16).

## 4. Trivial sample code

I've created some [trivial Hello World samples that can be found on my GitHub
account][parallel hello world in r].  They illustrate the very minimum needed
to use the parallel backends for the <code>foreach</code> package and are a
good way to verify that your parallel libraries and R environment are set up
correctly.  The idea here is that you can replace the 
<samp>hello.world()</samp> function with something useful and be off to a good
start.

However, these samples do _not_ illustrate how data, libraries, and 
subfunctions may have to be transferred to other nodes when using MPI.  For more
details on how to approach those more realistic problems, see the next part in
this series:  [Parallel Options for R][parallel options]

<!-- references -->
[parallel options]: parallel-options.html
[rmpi website]: http://cran.r-project.org/web/packages/Rmpi/index.html
[parallel hello world in r]: https://github.com/glennklockwood/paraR/tree/master/hello
