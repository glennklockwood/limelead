---
title: Installing Software Without Root
shortTitle: Installing Without Root
date: 2014-04-22T00:00:00-07:00
template: page.jade
parentDirs: [ hpc-howtos ]
---

## Contents

* [1. Introduction](#1-introduction)
* [2. Python Libraries](#2-python-modules)
* [3. Perl Modules](#3-perl-modules)
* [4. R Libraries](#4-r-libraries)

## 1. Introduction

A common request we get is to install some software package on either Gordon
or Trestles, sometimes with the implicit assumption that it should be a simple
matter of doing <kbd>sudo apt-get install somepackage</kbd>.  Unfortunately,
installing a new piece of software on a shared resource like Gordon or Trestles
is not that easy because

* we need to make sure the software will not break another library or program on the system
* we will typically have to install it on all of the compute nodes too, not just the login nodes
* we then have to support that software (and any/all users' questions about it) since we officially provide it
* our system engineers, who can actually deploy packages, are not the same applications experts who compile the packages

The net result is that installing a new software package system-wide can take
weeks or months to do.  When I get requests to install software, I invariably
respond that it would be easier and faster for the user (that's you) to just
install the package himself, and provide step-by-step instructions on exactly
how to do that.

For the sake of anyone who wants to know how to install his or her own 
software applications on SDSC Trestles or Gordon (or any other Linux or UNIX
machine, for that matter), here are some generic guidelines on how to do 
this.

## 2. Python Modules

There are several ways Python will let you manage your own set of libraries,
and I find the virtualenv package to be the easiest.  It creates what amounts to
an installation of Python that is local to your home directory, which means that
any libraries you install using that special personalized Python will also 
install into your home directory.

First, download virtualenv from [the project's website][virtualenv website], e.g.,

<pre>
$ <kbd>wget --no-check-certificate "https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.2.tar.gz"</kbd>
</pre>

Then _be sure to load the python module that you wish to clone_.  This
is important because the <code>python</code> that you will run if you don't
explicitly load a Python module is the system-wide default, Python 2.6.6.
I recommend using the Python 2.7.x module we provide on both machines, so load 
that module before trying to install virtualenv:

<pre>
$ <kbd>module load python</kbd>
</pre>

You must now decide the location of this custom Python you want to install
using virtualenv.  <code>~/python27-gordon</code> is a good choice, assuming you are
using Python 2.7 as previously discussed.  Then, unpacking and installing
virtualenv is a snap:

<pre>
$ <kbd>tar zxvf virtualenv-1.11.2.tar.gz</kbd>
virtualenv-1.11.2/
virtualenv-1.11.2/AUTHORS.txt
...
virtualenv-1.11.2/virtualenv_support/pip-1.5.2-py2.py3-none-any.whl
virtualenv-1.11.2/virtualenv_support/setuptools-2.1-py2.py3-none-any.whl

$ <kbd>python virtualenv-1.11.2/virtualenv.py ~/python27-gordon</kbd>
New python executable in /home/username/python27-gordon/bin/python
Installing setuptools, pip...done.
</pre>

And that's all you have to do.  Now whenever you want to use your custom
Python installation, you will have to issue this command:

<pre>
$ <kbd>source ~/python27-gordon/bin/activate</kbd>
(python27-gordon)$
</pre>

As you may notice, it modifies your prompt to show that you are in this
custom Python's "virtual environment."  If you always plan on using this custom
Python, you can go ahead and add the following lines to your 
<code>~/.bashrc</code>:

<pre>
module load python
VIRTUAL_ENV_DISABLE_PROMPT=1 source python27-gordon/bin/activate
</pre>

Note the <var>VIRTUAL_ENV_DISABLE_PROMPT=1</var> preceding the "source" 
command--this option prevents that annoying prompt prefix that virtualenv will
otherwise give you every time you log in.

Once you've got your virtualenv activated, installing new libraries is easy
using <code>pip</code>:

<pre>
(python27-gordon)$ <kbd>pip install cutadapt</kbd>
Downloading/unpacking cutadapt
  Downloading cutadapt-1.3.tar.gz (149kB): 149kB downloaded
  Running setup.py (path:/home/username/python27-gordon/build/cutadapt/setup.py) egg_info for package cutadapt
...
Successfully installed cutadapt
Cleaning up...

(python27-gordon)$ <kbd>pip install pyvcf</kbd>
Downloading/unpacking pyvcf
  Downloading PyVCF-0.6.4.tar.gz
...
Successfully installed pyvcf distribute setuptools
Cleaning up...
</pre>

As you can see, pip automatically downloads and installs dependencies for 
you, making the task of managing Python libraries under your own user account
on our supercomputers pretty easy.

## 3. Perl Modules

One of the standard ways of maintaining your own Perl libraries installed
into your home directory is using the <code>local::lib</code> module which, 
like Python's virtualenv, lets you emulate having Perl installed locally.

To get started with [local::lib][perl local lib website] you've first got to
download and unpack it:

<pre>
$ <kbd>wget http://search.cpan.org/CPAN/authors/id/E/ET/ETHER/local-lib-1.008010.tar.gz</kbd>
$ <kbd>tar zxvf local-lib-1.008010.tar.gz</kbd>
local-lib-1.008010/
local-lib-1.008010/Changes
local-lib-1.008010/inc/
...
$ <kbd>cd local-lib-1.008010</kbd>
</pre>

Unlike with Python, we do not have a separate Perl module that needs to be
loaded.  Once you're in that <code>local-lib-1.008010</code> directory, you can
initiate the _bootstrap_ process by which <code>local::lib</code> creates
your custom Perl installation and installs itself.  Let's assume that we want 
to install our custom Perl into <code>~/perl5-gordon</code> (note: use 
<var>$HOME</var> instead of <code>~</code>):

<pre>
$ <kbd>perl Makefile.PL --bootstrap=$HOME/perl5-gordon</kbd>
Attempting to create directory /home/username/perl5-gordon
...
</pre>

If you don't specify a path after the <code>--bootstrap</code> flag, your
<code>local::lib</code> installation will be in <code>~/perl5</code>.  This
bootstrapping process may take a very long time as <abbr title="Comprehensive Perl Archive Network">CPAN</abbr>
needs to first configure itself, then install all of the libraries that 
<code>local::lib</code> needs to work.  After a _lot_ of text scrolls by
(many of which look like errors--this isn't necessarily bad), hopefully you 
wind up at

<pre>
...
Checking if your kit is complete...
Looks good
Generating a GNU-style Makefile
Writing Makefile for local::lib
Writing MYMETA.yml and MYMETA.json
</pre>

Then test and install <code>local::lib</code>:

<pre>
$ <kbd>make test</kbd>
...
t/subroutine-in-inc.t .. ok
All tests successful.
Files=8, Tests=35,  0 wallclock secs ( 0.04 usr  0.03 sys +  0.23 cusr  0.07 csys =  0.37 CPU)
Result: PASS

$ <kbd>make install</kbd>
Installing /home/username/perl5-gordon/lib/perl5/POD2/PT_BR/local/lib.pod
...
Appending installation info to /home/username/perl5-gordon/lib/perl5/x86_64-linux-thread-multi/perllocal.pod
</pre>

Now we need to put a few new lines in our <code>~/.bashrc</code> to 
effectively do what that <code>activate</code> script does for Python's 
virtualenv.  Issue the following command, then append its output into your 
<code>~/.bashrc</code>:

<pre>
$ <kbd>perl -I$HOME/perl5-gordon/lib/perl5 -Mlocal::lib=$HOME/perl5-gordon | tee -a ~/.bashrc</kbd>
export PERL_LOCAL_LIB_ROOT="$PERL_LOCAL_LIB_ROOT:/home/username/perl5-gordon";
export PERL_MB_OPT="--install_base /home/username/perl5-gordon";
export PERL_MM_OPT="INSTALL_BASE=/home/username/perl5-gordon";
export PERL5LIB="/home/username/perl5-gordon/lib/perl5:$PERL5LIB";
export PATH="/home/username/perl5-gordon/bin:$PATH";
</pre>

You should then either log out and log back in, or paste those export lines
into your current terminal session to put them into effect.  Following that, you
should be able to install Perl libraries into your home directory:

<pre>
$ <kbd>perl -MCPAN -e 'install(Time::Piece)'</kbd>
Reading '/home/username/.cpan/Metadata'
  Database was generated on Mon, 16 Sep 2013 19:53:02 GMT
Running install for module 'Time::Piece'
...
  RJBS/Time-Piece-1.23.tar.gz
  /usr/bin/make install  -- OK
</pre>


## 4. R Libraries

Users cannot install R libraries globally on our machines, but R makes it 
very easy for users to install libraries in their home directories.  To do 
this, fire up R and when presented with the <code>&gt; </code> prompt, use the
<kbd>install.packages()</kbd> method to install things:

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

<pre>&gt; <kbd>install.packages(c('foreach','doMC'))</kbd></pre>

For most packages, this is all you will have to do.  However, sometimes
R packages depend on other _system_ libraries, and those system 
libraries might not be in the default search path for the R package installer.
When that happens, you might get an error that looks something like this:

<pre>
&gt; <kbd> install.packages('rjags');</kbd>
* installing *source* package 'rjags' ...
** package 'rjags' successfully unpacked and MD5 sums checked
checking for prefix by checking for jags... no
<span style="color:red">configure: error: "Location of JAGS headers not defined. Use configure arg '--with-jags-include' or environment variable 'JAGS_INCLUDE'"</span>
ERROR: configuration failed for package 'rjags'
* removing '/home/glock/R/x86_64-unknown-linux-gnu-library/3.0/rjags'

The downloaded source packages are in
    '/tmp/RtmpdE6UYF/downloaded_packages'
Warning message:
In install.packages("rjags") :
  installation of package â€˜rjagsâ€™ had non-zero exit status
</pre>

The relevant part of the error log is highlighted in red; the library could 
not install because it depends on a system library (as opposed to an R library)
that the <code>install.packages()</code> command could not find.

While fixing this error can be tricky since each R library can have a
different installation procedure, you can pass extra hints to the 
<code>install.packages()</code> command to suggest where it can find some of
these system libraries.  For example, the jags library is already installed on
Gordon and Trestles, and it can be loaded using <kbd>module load jags</kbd>.
After doing this, you can do something like

<pre>
&gt; <kbd>install.packages('rjags',
   <span style="color:green">configure.args=c(rjags='--with-jags-include=$JAGSHOME/include/JAGS
                           --with-jags-lib=$JAGSHOME/lib')</span>)</kbd>
* installing *source* package 'rjags' ...
** package 'rjags' successfully unpacked and MD5 sums checked
checking for prefix by checking for jags... /opt/jags/bin/jags
checking whether the C++ compiler works... yes
...
** testing if installed package can be loaded
* DONE (rjags)
</pre>

The green text highlights something that looks gnarly, but actually tells
R that

* the contents of <code>configure.args</code> should be passed to the 
  underlying library's installer.  <code>configure.args</code> is a named
  list containing special configuration parameters, where the name of each
  value corresponds to the package to which the special parameters apply.
* the <code>--with-jags-include</code> and <code>--with-jags-lib</code>
  signal the rjags installer where your JAGS library's <code>include</code>
  and <code>lib</code> directories are located
* <var>$JAGSHOME</var> is a variable that gets defined when you load the
  <code>jags</code> module on Gordon and Trestles.  On other systems, you
  would specify the full path to your jags installation directory instead.

Actually knowing what <code>configure.args</code> to use when generic package
installations fail requires some amount of intuition.  If all else fails, 
contact your help desk!

<!-- References -->
[virtualenv website]: https://pypi.python.org/pypi/virtualenv
[perl local lib website]: http://search.cpan.org/~ether/local-lib-1.008018/lib/local/lib.pm
