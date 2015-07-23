---
date: "2014-06-28T00:00:00-07:00"
draft: true
title: "Configuring a Solaris 10 Server"
last_mod: "June 28, 2014"
parentdirs: [ 'sysadmin-howtos' ]
---

I decided to document the process of configuring a Solaris 10 server or 
workstation over the course of the many times I've done it, and this document 
has become my standard HOWTO for the task.  A significant amount of inspiration
for this page stemmed from a wonderful guide written by the CTO at Rutgers University,
[Dr. Charles Hedrick][charles hedrick's website], on [setting up Solaris 10 at
Rutgers][charles hedrick's solaris page].  His guide was one of my starting
points for configuring Solaris 10 when I first started collecting Suns and is a
very good resource in general.  However, this guide diverges from it in detail
and preference.

My server setup is a bit different from the one outlined by Dr. Hedrick, and
I chose to start documenting the installation from an earlier stage due to the
fact that I always find myself having to install Solaris myself on secondhand
machines.  These notes were taken during the various reinstalls of `chrysalis`,
which I installed over a private network using another Solaris 10-based install
server (`herring`).  I'll start with the Solaris 10 (u9 in this case) DVD
downloaded to `herring` and `chrysalis` having a pair of blank disks.

## Outline

* [Setting up the install server](#)
* [Initiating the install](#)
* [Switching from serial to SSH](#)
* [Using stronger cryptography](#)
* [Configuring home directories](#)
    * [Without autofs](#)
    * [With autofs](#)
    * [Adding a non-root user](#)
* [Configuring some core system services](#)
    * [Configuring ipfilter](#)
    * [Managing logs](#)
    * [Configuring NTP](#)
    * [Setting up patching system](#)
* [Setting up system software](#)
* [User rc dotfiles](#)
    * [.bashrc](#)
    * [.vimrc](#)

## Setting up the install server

On the machine that will become the install server, the Solaris Express iso 
has to be mounted, and the install server must be set up.  As a bit of a side
note, I've heard that JumpStart Enterprise Toolkit (JET) is the preferred
way of doing network installations for many serious systems people, but I chose
not to use it in this case for simplicity.  Anyway,

<pre>
# <kbd>lofiadm -a /home/glock/sol-10-u9-ga-sparc-dvd.iso /dev/lofi/1</kbd>
# <kbd>mount -F hsfs /dev/lofi/1 /mnt</kbd>
# <kbd>mkdir -p /export/install</kbd>
</pre>

Sun provides a very handy and simple program to set up the install server.
It takes a while though, as the contents of the iso have to be copied to disk.
Grab a cup of coffee for this one.

<pre>
# <kbd>cd /mnt/Solaris_10/Tools</kbd>
# <kbd>./setup_install_server /export/install/media</kbd>
Verifying target directory...
Calculating the required disk space for the Solaris_10 product
Calculating space required for the installation boot image
Copying the CD image to disk...
Copying Install Boot Image hierarchy...
Copying /boot netboot hierarchy...
Install Server setup complete
</pre>

Of course, this install target has to be accessible via NFS, and NFS must be
enabled.  Also note the Solaris 10-specific <kbd>svcadm</kbd>:

<pre>
# <kbd>share -o ro,anon=0 /export/install/media</kbd>
# <kbd>svcadm enable network/nfs/server</kbd>
</pre>

Setting up the install client can be trickier because of how the networking
may be between your install server and the target client.  Both of my machines
were on the same subnet, so I did not have to specify much witchcraft.

<pre>
# <kbd>cd /export/install/media/Solaris_10/Tools</kbd>
# <kbd>./add_install_client -e 0:3:ba:6c:ad:28 -s 192.168.2.91:/export/install/media chrysalis sun4u</kbd>
</pre>

In the above case, `0:3:ba:6c:ad:28` is the install target's (`chrysalis`'s) MAC
and `192.168.2.91` is the install server's (`herring`'s) IP address.  Specifying
the IP is important, as I would not rely on the installation being able to
resolve hostnames when it needs to mount the NFS share.  The
<kbd>add_install_client</kbd> command automatically adds the specified MAC to
`/etc/ethers`, but it has appeared to be additionally important to add the
client hostname to `/etc/hosts` so that the install client can be identified by
the install server.

## Initiating the install

On the client machine, access the console via serial, LOM, or keyboard and mouse
and get to the OpenBoot prompt.  Drop to the ok prompt, cross your fingers, then
attempt to boot over the network.

<pre>
ok&gt; <kbd>boot net</kbd>
</pre>

If the install client won't boot off the network, first ensure that ipfilter
(or whatever firewall you are using on the install server) is not blocking
tftpd and NFS.  NFS is particularly difficult to pass through a firewall, so I
usually toss a rule in to allow all traffic from the install client (both TCP and 
UDP for NFS) through.  Alternatively, you can just <kbd>svcadm disable
network/ipfilter</kbd> temporarily on the install server; just don't forget to
turn it back on once the installation is complete!

There shouldn't be anything tricky about the install; I generally opt to use ZFS
and mirror two disks for redundancy.  I've encountered two problems with this
that may be worth mentioning.

1. I had a problem with disks not appearing in the installer despite being
   recognized and mountable from a shell opened during the install process.
   This wound up being because the installer only displays disks with SMI labels
   as install targets.  One of my disks was recycled from another zpool, and as
   a result it had an EFI label.  To rectify this, I had to <kbd>format -e</kbd>
   to get into expert mode, then issue <kbd>label</kbd> and choose the SMI label
   over the EFI.
2. For whatever reason, if you want to install with ZFS as your root partition's
   filesystem, you MUST use the text-mode installer.  Since `chrysalis` was a
   net install, this was not an issue; however, if you are installing via
   keyboard/mouse/monitor, you've got to issue <kbd>boot cdrom - text</kbd> to
   force the text mode install (the X installer is still loaded though), or just
   unplug the mouse and <kbd>boot cdrom</kbd> to prevent X from loading at all.

After the system was completely installed, I configured the system to get its IP
via DHCP as well, but it appears that the installer does not completely
configure the system properly for DHCP.  Thus, the first thing I had to do after
the installation completed was to

<pre>
# <kbd>touch /etc/dhcp.dmfe0</kbd>
# <kbd>init 6</kbd>
</pre>

The presence of this file will instruct the system to automatically launch
the DHCP client at boot and configure <code>dmfe0</code> with it on system boot.

## Switching from serial to SSH

I prefer to ditch using the serial console as soon as I can because of how
slow it is and vi's slight incompatibilities with it.  The alternative to this
serial console at this point is to use SSH, but there are no user accounts on
the new system yet.  Thus, I have to be able to ssh into the new machine as
root.  For security reasons, Solaris disables this by default though, so what I
do is enable ipfilter to cover for ssh while login-as-root is enabled.

The first step is to establish a very simple ipfilter ruleset while still logged
in through the serial line.  Edit `/etc/ipf/ipf.conf` and add these rules:

<pre>
pass out quick from any to any keep state
pass in quick proto tcp from 192.168.2.2/32 to any port = 22 keep state keep frags
block in quick all
</pre>

This will block everything incoming except ssh traffic coming from
`192.168.2.2`, which is the address of my workstation from which I will ssh.
Now enable ipfilter by issuing

<pre>
# <kbd>svcadm enable network/ipfilter</kbd>
</pre>

and confirm that ipfilter is working correctly by then issuing

<pre>
# <kbd>svcs -a | grep ipfilter</kbd>
</pre>

Then to allow the root user to log in over SSH, edit `/etc/ssh/sshd_config` and
replace the line which reads

<pre>PermitRootLogin no</pre>

to read

<pre>PermitRootLogin yes</pre>

and reload this configuration file so that root can SSH in by issuing
<kbd>svcadm refresh ssh</kbd>.

Now the serial console can be abandoned and the rest of this configuration
procedure can be carried out over SSH.  Of course, this is optional, and you can
often stick to the serial console just as easily if you would like.  Anyway, I
<kbd>ssh root@chrysalis</kbd> from my workstation and I'm back to where I was
but with a better terminal.

## Using stronger cryptography

A high priority for me is to change the default cryptographic algorithm Solaris
uses.  Although this probably does not affect enterprise deployments which use
LDAP or Kerberos, Solaris's choice to use the standard unix algorithm means all
user passwords (including root!) are strictly limited to only eight characters.
Eight-character passwords are too short for my preference, so I edit
`/etc/security/policy.conf` and change

<pre>CRYPT_DEFAULT=__unix__</pre>

to

<pre>CRYPT_DEFAULT=md5</pre>

For reference,

<table class="table table-striped table-condensed">
    <thead>
    <tr>
        <th>Identifier</th>
        <th>Algorithm</th>
        <th>Max Pass Length</th>
        <th>Compatibility</th>
        <th>man page</th>
    </tr>
    </thead>
    <tbody>
    <tr>
        <td>__unix__</td>
        <td>Unix</td>
        <td>8</td>
        <td>All</td>
        <td>crypt_unix(5)</td>
    </tr>
    <tr>
        <td>1</td>
        <td>BSD MD5</td>
        <td>255</td>
        <td>BSD, Linux</td>
        <td>crypt_bsdmd5(5)</td>
    </tr>
    <tr>
        <td>2a</td>
        <td>Blowfish</td>
        <td>255</td>
        <td>BSD</td>
        <td>crypt_bsdbf(5)</td>
    </tr>
    <tr>
        <td>md5</td>
        <td>Sun MD5</td>
        <td>255</td>
        <td>-</td>
        <td>crypt_sunmd5(5)</td>
    </tr>
    <tr>
        <td>5</td>
        <td>SHA-256</td>
        <td>255</td>
        <td>-</td>
        <td>crypt_sha256(5)</td>
    </tr>
    <tr>
        <td>6</td>
        <td>SHA-512</td>
        <td>255</td>
        <td>-</td>
        <td>crypt_sha512(5)</td>
    </tr>
  </tbody>
</table>

The man pages for these algorithms are also very informative, and I chose to
use Sun's MD5 implementation simply because <kbd>man crypt_unix</kbd> suggests
it.  After changing this, existing passwords need to be rehashed using the new
algorithm.  Since only the root account exists right now (this is why I do this
before making new user accounts!), this just means issuing

<pre># <kbd>passwd root</kbd></pre>

## Adding new users

Many first-time Solaris users find it confusing that new user home directories
cannot be made in `/home`.  This is due to autofs which is enabled by default in
Solaris.  The premise is that new home directories can physically be scattered
all over (i.e., in `/export/home`, on separate expansion volumes, on other
machines on the network, et cetera) but all be mounted to the unified `/home`
directory.

Disabling autofs (like in other operating systems) or keeping it enabled (like
in Solaris) are both options.

### No autofs

To simply disable autofs, issue

<pre># <kbd>svcadm disable autofs</kbd></pre>

and the `/home` directory should be released and modifiable.  In the case of ZFS
root, it may be a good idea to make `/home` its own ZFS dataset for ease of
management:

<pre>
# <kbd>rm -r /home</kbd>
# <kbd>zfs destroy rpool/export/home</kbd>
# <kbd>zfs create -o mountpoint=/home rpool/home</kbd>
</pre>

Of course, ZFS datasets occupy kernel memory and this may not be adviseable on
low-memory systems.

### With autofs

If the native autofs setup for Solaris is desired, setting it up is pretty easy.
The default `/etc/auto_master` should contain the necessary lines already out of
the box:

<pre>
+auto_master
/net            -hosts          -nosuid,nobrowse
/home           auto_home       -nobrowse
</pre>

The `+auto_master` defers to NIS maps if one exists; it can be removed if this
server will not be using NIS.  The `/home` line is the one to keep, as it places the 
`/home` directory under autofs control and defers configuration options to the
`/etc/auto_home` file.  That file is also pretty simple, and needs the following
line added:

<pre>
*       chrysalis:/export/home/&amp;
</pre>

<p>The first column (a <code>&ast;</code>) indicates that any directory under
the <code>/home</code> directory, when queried, should be mapped under autofs.
The second column (which is blank in this case) would be where the NFS flags
(e.g., <code>-intr,nosuid,hard</code>) would be, and the third column is the
device to mount.  The <code>&</code> symbol corresponds to the
<code>&ast;</code> in the first line and essentially gets replaced with whatever
value that <code>*</code> takes.  For example, you could more explicitly rewrite
the above line as a bunch of lines, each for an individual user:</p>

<pre>
glock   chrysalis:/export/home/glock
frank   chrysalis:/export/home/frank
mary    chrysalis:/export/home/mary
</pre>

Using the wildcard spares you the hassle of having to edit this file every
time a new user is added; however, this also puts the entire `/home/*` under the
control of this server.  If you want the ability to mount users whose home
directories are on other devices or machines all into the same `/home`
directory, you would (to the best of my knowledge) have to add each user
individually, so at the very least your `auto_home` would look like:

<pre>
glock   chrysalis:/export/home/&amp;
frank   chrysalis:/export/home/&amp;
mary    chrysalis:/export/home/&amp;
</pre>

Anyway, configuring autofs and `/etc/auto_home` correctly tells the automounter
to NFS mount `/export/home/whoever` on the server chrysalis to the local
`/home/whoever` directory whenever it is accessed.

Once the autofs config files are as they should be, reloading autofs lets
us assign users' home directories to, say, `/home/glock` rather than `/export/home/glock`:

<pre># <kbd>svcadm restart autofs</kbd></pre>

Although this refresh isn't strictly necessary, it doesn't hurt to make sure
you haven't entered any syntax errors by ensuring that autofs will start up
correctly.

As a side note, if you are using autofs to mount homes from another Solaris
host, don't forget to share the home directories with this new machine!  The
way of doing this in ZFS is something like

<pre>
# <kbd>zfs set sharenfs=rw=@128.6.18.165/26:@192.168.2.0/24 rpool/export</kbd>
</pre>

Or if you want to do it the old-fashioned way, edit `/etc/dfs/dfstab` and add a
similar line.  For mounting local volumes via autofs though, enabling NFS isn't
necessary.

### Adding a Non-Root User

Now to add the first user:

<pre>
# <kbd>zfs create rpool/home/glock</kbd>
# <kbd>useradd -d /home/glock -s /bin/bash -P 'Primary Administrator' glock</kbd>
# <kbd>passwd glock</kbd>
...
# <kbd>chown -R glock:other /home/glock</kbd>
</pre>

The above procedure can probably be wrapped into a script (a la
<kbd>adduser</kbd> in Linux) for ease of use.

In recent versions of Solaris 10 (update 8 or 9), I've found that the "Primary
Administrator" profile doesn't always exist.  I'm not sure if this is due to a
missing package or what, but adding the profile manually isn't very hard.  First
edit `/etc/security/exec_attr` and add this line:

<pre>
Primary Administrator:suser:cmd:::*:uid=0;gid=0
</pre>

Then add this line to `/etc/security/prof_attr`:

<pre>
Primary Administrator:::Can perform all administrative tasks:auths=solaris.*,solaris.grant;help=RtPriAdmin.html
</pre>

For completeness, install the `RtPriAdmin.html` file (I used to link this file
here, but no longer have it) specified in `/usr/lib/help/profiles/locale/C`.
Then either add users as specified above, or add this profile to existing users
with <kbd>usermod(1M)</kbd>:

<pre># <kbd>usermod -P 'Primary Administrator' glock</kbd></pre>

Now that a non-root user exists, root logins over ssh can be disabled again.  In
`/etc/ssh/sshd_config`, change the <code>PermitRootLogin</code> parameter back
to <code>no</code> and reload the sshd configuration using <kbd>svcadm refresh
ssh</kbd>.  At this point I logged out and logged back in under my newly created
user account, then did <kbd>pfexec su -</kbd> to get back to where I was.

## Configuring some core system services

Now that SSH has been locked up again, it's time to configure a proper ruleset
for IPFilter, set up system logging, and get everything up and running.

### Configuring IPfilter

There are a lot of good guides on general network security and configuring
ipfilter, the firewall provided in Solaris 10, so I will not get into the gory
details here.  However, there are a few important things to note which are
unique to Solaris:

* If you didn't select the "`minimal network daemons`" group during
  installation, a bunch of daemons (notably telnet) will be running by default.
  To disable most of the unnecessary ones post-install, issue 
  <kbd>/usr/sbin/netservices limited</kbd> as root.  This will have the same
  effect as if you chose the minimal network daemons install option.
* To quickly see what is still running, issue <kbd>netstat -an|grep LISTEN</kbd>
* Cross-referencing the open ports with `/etc/services` should give you a quick
  idea of what you've got running.  If there are some mysterious services
  listening to ports of questionable necessity, you can usually find a more
  human-readable description of SMF services by issuing <kbd>svcs -o
  FMRI,DESC</kbd>

Knowing this, you can craft a reasonably effective ruleset such as this 
one in `/etc/ipf/ipf.conf`:

<div class="shortcode">{{< highlight bash >}}
#
# ipf.conf
#
# IP Filter rules to be loaded during startup
#
# See ipf(4) manpage for more information on
# IP Filter rules syntax.

# General policies
pass out quick from any to any keep state
block in quick proto tcp with short

### Handle connections over the external interface (bge0) ######################
pass in quick on bge0 from chrysalis to any keep state

### Handle SSH coming in from the outside -- only allow connections from Rutgers
block in quick on bge0 from any to any port = 22 head 1
  pass in quick on bge0 proto tcp from 128.6.0.0/16 to any port = 22 \
    keep state group 1
  block return-rst in log quick on bge0 proto tcp all group 1

### Apache2 from outside; let apache do the logging
pass in quick on bge0 proto tcp from any to any port = 80 keep state

### Block ICMP except ping
block in log quick on bge0 proto icmp from any to any head 2
  pass in quick on bge0 proto icmp from any to any icmp-type echo \
    keep state group 2
  pass in quick on bge0 proto icmp from any to any icmp-type echorep \
    keep state group 2

### Bounce and log any other connection attempts from outside of Rutgers
block return-rst in log quick on bge0 proto tcp from !128.6.0.0/16 to chrysalis
block return-rst in quick on bge0 proto tcp all
block in quick on bge0 all
{{</highlight>}}</div>


This ruleset really only acts on the `bge0` interface and leaves traffic on all
others (i.e., internal-facing interfaces and the loopback interface) unfiltered.
The only exception is the second line, which blocks malformed packets on all
interfaces.  On the `bge0` interface, this ruleset does these things:

1. Allow any connections from the server to itself on the external interface
2. Allow SSH connections only from the Rutgers network (`128.6.0.0/24`) and drop+log all others
3. Allow all httpd traffic (port 80) in
4. Allow only ping-related ICMP packets in
5. Block everything else, and if the traffic is TCP and isn't from the Rutgers network (`!128.6.0.0/24`), log it

I should also probably mention that, unlike iptables in Linux, ipfilter obeys
the last-matching rule instead of the first-matching one UNLESS the "quick"
keyword is thrown in there (as I have done above).  It would seem to me that
using quick-styled rules would make packet filtering more efficient since each
packet wouldn't have to go down the entire stack of rules, but the examples and
tutorials I've found online seem to be split 50/50 in terms of whether to write
quick rules or non-quick rules.  It must be a matter of personal preference.

### Managing logs

Several rules defined for IPFilter are logged, but the log handling has to be
configured properly for this to actually work.  The system logging facility's
configuration needs to be updated accordingly.  I edited `/etc/syslog.conf` and
added two lines:

<pre>
auth.info                       ifdef(`LOGHOST', /var/log/authlog, @loghost)
local0.debug                    ifdef(`LOGHOST', /var/log/ipflog, @loghost)
</pre>

I should point out that I think there is already an auth.notice line that comes
with Solaris in `/etc/syslog.conf`.  Either comment out that line or replace it
with the auth line above.  This will enable logging of login attempts,
successful or otherwise.  The local0 line specifies where ipfilter should drop
its logged output to.  Just to make sure that the log files do exist,

<pre>
# touch /var/log/ipflog &amp;&amp; chmod 600 /var/log/ipflog
# touch /var/log/authlog &amp;&amp; chmod 600 /var/log/authlog
</pre>

Because the ipfilter and authorization logs can get large and unwieldy, it is
also a good idea to let logadm rotate them as necessary.  To do this, issue the
following two commands: 

<pre>
# <kbd>logadm -w /var/log/ipflog -C 4 -P 'Fri Jun 19 07:10:00 2009' -a 'kill -HUP `cat /var/run/syslog.pid`'</kbd>
# <kbd>logadm -w /var/log/authlog -C 4 -P 'Fri Jun 19 07:10:00 2009' -a 'kill -HUP `cat /var/run/syslog.pid`'</kbd>
</pre>

The <code>-P 'Fri Jun 19 07:10:00 2009'</code> option in these lines is just
a placeholder for the date that the logs were last rotated in and can be any
arbitrary date you want to place, as long as the format is acceptable.  The 
<code>-C 4</code> portion specifies that logadm should juggle four files for 
each log (e.g., `authlog`, `authlog.0`, `authlog.1`, and `authlog.2`), and the
`-a` option indicates that SIGHUP should be sent to logadm's PID when the
log file is rotated to restart the daemon.  Alternatively, you can simply edit
`/etc/logadm.conf` and add everything after the `-w` above, but using the
<kbd>logadm</kbd> command offers syntax checking and other safeguards (or so
says the Sun docs).

Now that this is all done, you should be able to

<pre>
# <kbd>svcadm refresh system-log<br/></kbd>
# <kbd>kill -HUP `cat /var/run/syslog.pid`</kbd>
</pre>

to reload these configuration changes.  I just did <kbd>init 6</kbd> to be safe.

### Configuring the NTP client

Synchronizing the clock has a number of advantages, and Rutgers maintains
NTP servers to establish a university-wide time.  To sync against the Rutgers
servers, create `/etc/inet/ntp.conf` (or copy one
of the templates in that directory) and add these lines:

<pre>
server ntp-busch.rutgers.edu    version 3
server ntp-lcsr.rutgers.edu     version 3
driftfile /var/ntp/ntp.drift
</pre>

Then

<pre># <kbd>echo "0.0" &gt; /var/ntp/ntp.drift</kbd></pre>

to establish the drift file.  Alternatively, it is possible
to sync against the [U.S. ntp.org pool][ntp.org pool] list or [NIST's time
servers][nist ntp pool].  Once configured, enable NTP with <kbd>svcadm enable
ntp</kbd> and, after a few seconds, verify that all is well using 
<kbd>ntpq -p</kbd>.

### Setting up patching system

<div class="shortcode">{{% alertbox "danger" %}}
As of December 2010, I've been having trouble using the command-line setup for
`sconadm`.  According to Oracle, the following process should work with a valid,
supported Sun hardware serial number and an Oracle Single Sign-On.  Even with my
entitlement to download patches through [Oracle Support](http://support.oracle.com/),
I could not get <kbd>sconadm</kbd> to register correctly.  Strangely enough, my
_old_ Sun contract number and SunSolve sign-on still work when registering
through the <kbd>updatemanager</kbd> Java-based GUI, so I don't know what's
supposed to work here.
{{% /alertbox %}}</div>

If you've got a valid Sun support contract and a production machine is being
configured here, it'd probably be a good idea to register the system for easy
patching.  Although this method may change in the months or years following the
Oracle acquisition, as of August 2010, establishing patch authentication 
involves first creating a temporary configuration file (like `/root/regprof`)
and putting the following text in it:

<pre>
userName=jim@company.com
password=somepassword
hostName=chrysalis
subscriptionKey=ABC123
portalEnabled=false
</pre>

Of course, you've got to already have a valid SunSolve account 
(jim@company.com) and its password (somepassword), and you have to have a Sun
support contract number (ABC123).  Since this file contains a plaintext password
and contract number, the <kbd>sconadm</kbd> command requires that it have strict
permissions before it'll accept it.  Thus, to register the system for updates, 
do

<pre>
# <kbd>chmod 400 /root/regprof</kbd>
# <kbd>sconadm register -a -r regprof</kbd>
sconadm is running
Authenticating user ...
finish registration!
# <kbd>rm /root/regprof</kbd>
</pre>

At this point you can issue

<pre>
# <kbd>smpatch analyze</kbd>

You have new messages. To retrieve: smpatch messages [-a]

121118-17 SunOS 5.10: Update Connection System Client 1.0.17
125555-07 SunOS 5.10: patch behavior patch
141588-04 SunOS 5.10: ksh,sh,pfksh,rksh,xargs patch
119254-75 SunOS 5.10: Install and Patch Utilities Patch
119788-10 SunOS 5.10: Sun Update Connection Proxy 1.0.9
...
</pre>

At some point you should then actually download and apply these patches
using <kbd>smpatch update</kbd>, but this process can take a very long time and
I tend to patch overnight.

## Setting up system software

Solaris now comes with a large wealth of software, but it lacks a good compiler
out of the box.  GCC comes on the DVD now, but I prefer to keep stock GCC off of
my system and support only Sun Studio's compilers.  Should I ever come across
code that requires GCC to compile correctly (e.g., the wealth of GNU garbage
that, despite claiming portability, only compiles nicely on Linux+GCC), I
install [GCC for Sun Systems][gcc for sun].  

Anyway, at the time of writing, [Oracle Solaris Studio 12.2][solaris studio download]
was the most recent version of Sun Studio (or Oracle Solaris Studio now), so I
opted to download the package installer version for Solaris SPARC.
Unfortunately it relies on a GUI installer which is a bit silly considering most
servers run headless.  It also requires a huge amount of RAM to install since it
decompresses to `/tmp`, so I had to specify a few extra parameters during
installation.  Provided I downloaded the installer to `/root`

<pre>
# <kbd>mkdir /root/tmp</kbd>
# <kbd>bunzip2 SolarisStudio12.2-solaris-sparc-pkg-ML.tar.bz2</kbd>
# <kbd>tar -xvf SolarisStudio12.2-solaris-sparc-pkg-ML.tar</kbd>
# <kbd>cd SolarisStudio12.2-solaris-sparc-pkg-ML</kbd>
# <kbd>./SolarisStudio12.2-solaris-sparc-pkg-ML.sh --non-interactive --create-symlinks --tempdir /root/tmp</kbd>
</pre>

The <kbd>--non-interactive</kbd> flag skips the GUI (and in fact all user 
input) and just does what it needs to do to install, including adding the 
optional language packs.

It is worth mentioning that, in the x86 version of Solaris 10 9/10 and 
Solaris Studio 12.2, I had additional issues where the installer would abort,
saying I needed to install patch 119961-07, but using the included 
<kbd>./install_patches.sh</kbd> would abort because, as it turns out, I didn't
have the `SUNWsprot` package installed (because it is not included in
the End-User Distribution install).  Upon installing SUNWsprot and trying to
then install 119961-07, it gave me another error about not being able to find
the <kbd>check-install</kbd> script.  A cursory glance made it appear that the 
<kbd>install-patches.sh</kbd> script included with Solaris Studio 12.2 is 
broken; I simply got fed up and installed 119961-07 by hand.

In addition to SUNWsprot being required pre-install (on x86 at least), there
are a few important packages that may or may not be necessary to install after 
the system is up to establish a suitable build environment.  These are a few
that I've found myself needing:

* `SUNWhea` - Headers necessary to compile anything
* `SUNWtoo` (and `SUNWtoox` in Solaris 9)
* `SUNWarc` (and `SUNWarcx` in Solaris 9)
* `SUNWbtool` (and `SUNWBtoox` in Solaris 9) - Includes the non-GNU version of make
* `SUNWsprot` (and `SUNWsprox` in Solaris 9) - Otherwise you get errors about `libmakestate.so.1` not being found

`SUNWlibm` and `SUNWlibmr` were missing in a Solaris 10 x86 install I did,
which produced compile errors like

<pre>
"/opt/solstudio12.2/prod/include/CC/Cstd/rw/math.h", line 60: Error: Could not open include file &lt;math.h&gt;.
</pre>

I'm not sure why I've never had that problem in the SPARC installs I've done.
Also, In my notes I also have SUNWastdev (new to Solaris 10) but I don't recall
why I needed it.  Also, installing Sun Studio from a core install requires the
SUNWadm* packages.

## User PATHs

Solaris has a lot of toolchains included with it due to its long history as a
standards-compliant POSIX and UNIX OS.  Because of this, I suspect that it 
leaves the task of deciding appropriate PATHs to the user and provides a very
minimal PATH by default.  To address this issue and provide users with a more
useful default PATH, I use a file I create called `/etc/defaultpath` which
contains the following:

<script src="https://gist.github.com/glennklockwood/95ff0137dcc6a2326e53.js"></script>

Then I add the following line to `/etc/profile`:

<pre>
. /etc/defaultpath
</pre>

right above the <code>export PATH</code>.  This gives all Bourne shell users
a pretty useful path as soon as they log in.  A description of the various paths
and the toolchains within them can be found via <kbd>man -s5 filesystem</kbd>.

## User rc dotfiles

### .bashrc

Setting up a proper bash login environment is one of the last necessary 
steps for me.  My `.bashrc` looks something like this:

<script src="https://gist.github.com/glennklockwood/f5ec6831f4c7028cf004.js"></script>

Then, as per the [Bash Reference Manual][bash reference manual], "typically,
your `~/.bash_profile` contains the line"

<div class="shortcode">{{< highlight bash >}}
if &#91; -f ~/.bashrc &#93;; then . ~/.bashrc; fi
{{</highlight>}}</div>

And that's all mine contains.

### .vimrc

I use vim as my editor of choice due to its flexibility over the standard
UNIX vi.  However, that flexibility really only comes about with a good `.vimrc`
file.  Mine is pretty basic, but here it is:

<div class="shortcode">{{< highlight vim >}}
syntax on
set background=dark
set hlsearch
set expandtab
set ruler
set autoindent
set backspace=indent,eol,start

" Uncomment the following on sufficiently fast systems
"let loaded_matchparen = 1

" Uncomment the following to have Vim jump to the last position when
" reopening a file
if has("autocmd")
  au BufReadPost * if line("'\"") &gt; 0 &amp;&amp; line("'\"") &lt;= line("$")
    \| exe "normal! g'\"" | endif
endif
{{</highlight>}}</div>


<!-- References -->
[charles hedrick's website]: http://toolbox.rutgers.edu/~hedrick/
[charles hedrick's solaris page]: http://techdir.rutgers.edu/sol10.html
[ntp.org pool]: http://www.pool.ntp.org/zone/us
[nist ntp pool]: http://tf.nist.gov/tf-cgi/servers.cgi
[gcc for sun]: http://cooltools.sunsource.net/gcc/
[solaris studio download]: http://www.oracle.com/technetwork/server-storage/solarisstudio/downloads/index.html
[bash reference manual]: http://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html#Bash-Startup-Files
