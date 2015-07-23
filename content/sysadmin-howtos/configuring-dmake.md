---
date: "2009-10-17T21:50:38-05:00"
draft: false
title: "Configuring dmake"
last_mod: "October 17, 2009"
parentdirs: [ 'sysadmin-howtos' ]
---

At one point I had set up my two Sun Blade 1000s to work together for
distributed compiling with Sun Studio's dmake. Doing this took a little bit of
work since dmake relies on rlogin, which is disabled by default in newer
versions of Solaris.  This is what I did.

`dmake.conf` doesn't usually exist after a fresh install of Sun Studio and must
be created in `/etc/opt/SPROdmake` on each compile server. Since my systems each
had dual processors, my `dmake.conf` files all only had one line and looked like
this:

    max_jobs: 2

Each user who will be compiling also needs a `.dmakerc` file in his or her home
directory which establishes which compile server groups should be used.  In my
case, I had two compile servers, _black_ and _white_ which both had Sun Studio
installed in `/opt/SUNWspro/bin`.  This is what my `.dmakerc` looked like:

    group "blades" {
       host black { jobs = 2, path="/opt/SUNWspro/bin" }
       host white { jobs = 2, path="/opt/SUNWspro/bin" }
    }

Provided the two servers, _black_  and _white_, are in good communication (have
synced up `/etc/host` files, `/etc/passwd`, `/etc/shadow`, NFS-mounted source
directories that can be seen on all compile servers (such as would be the case
on a properly set up NIS network), this will let dmake launch jobs on both black
and white at their maximum capacity (2 jobs). Also, I had Sun Studio installed
in identical locations on each machine, but these locations apparently do not
need to be the same.

One last catching point for me was getting rsh to work. At present, dmake
requires that you be able to rsh commands to all servers specified in `.dmakerc`;
I do not like this as I prefer ssh, and in fact it is possible to inject 
a symlink for `/usr/bin/rsh` to `/usr/bin/ssh` in dmake's path. 

To set up rsh, first set up <span class="filename">/etc/hosts.equiv</span>.
Mine contained:

    localhost
    white
    black

This has to be the same on all compile servers (in my case, _black_ and _white_).

The next step is to make sure the necessary services are working.  Check and
make sure rlogin and shell are running:

<pre># <kbd>svcs -a | grep rlogin</kbd>
online 17:02:14 svc:/network/login:rlogin

# <kbd>svcs -a | grep shell</kbd>
disabled 16:25:54 svc:/network/shell:default
disabled 16:25:54 svc:/network/shell:kshell</pre>

It took me a while to realize that network/shell was required to use rsh 
(rather than rlogin, which is what rsh calls if you do not specify a command).
To enable it,

<pre># <kbd>svcadm enable network/shell:default</kbd></pre>

Then dmake should work.

<!-- References -->
