---
date: "2010-05-01T18:36:25-05:00"
title: "Converting Disk Block Size on Solaris"
last_mod: "May 1, 2010"
parentdirs: [ 'sysadmin-howtos' ]
---

One strange problem that I've come upon in buying secondhand enterprise hardware
are fiber channel disks (such as those that my Sun Blade 1000 takes) sometimes
come formatted in a 520-byte block size.  Apparently these 520-byte blocks are
used by a number of high-end RAID arrays that are the source for bulk
quantitites of fiber channel disks, but the 520-byte block size renders them
unformattable to Solaris.  Reformatting such a disk to 512-byte blocks is not
hard, but it is not an immediately intuitive process.

Here is what I did to convert one 520-byte block fiber channel disk (that came
out of an EMC CLARiiON array) to a 512-byte block size:

**Step 1.** Get <kbd>scu</kbd>, the SCSI command utility.  I think the original
website for this tool no longer exists, and I initially got it from [this
page][original scu website].  In case that page disappears, I also maintain a
local [copy of scu for Solaris](../files/SolarisSparc-scu.tar.gz) that you can
download.

**Step 2.** Unzip and untar the package, and <kbd>chmod a+x scu</kbd> to make
the binary executable.

**Step 3.** Run the Solaris <kbd>format</kbd> utility to identify the raw disk
to be fixed.  In my case, it was 

<pre>1. c1t2d0 &lt;SEAGATE-ST373405CLAR72-4A3C cyl 8737 alt 2 hd 255 sec 63&gt;</pre>

**Step 4.** Launch scu on that device (e.g., <kbd>./scu -f /dev/rdsk/c1t2d0s0</kbd>)

**Step 5.** Issue the following commands from within scu:

<pre>
&gt; <kbd>set bypass on</kbd>
&gt; <kbd>set device block-length 512</kbd>
&gt; <kbd>format</kbd>
</pre>

After a really long time (55 minutes in my case), it'll finish.  Then simply
issue <kbd>stop</kbd> to spin down the disk and then <kbd>exit</kbd> to clean
up.

**Step 6.** Enter <kbd>format</kbd> again, select the disk, then enter
<kbd>verify</kbd>.  It should indicate `bytes/sector = 512` or that the block
size has been changed correctly.

At this point the disk still isn't usable though.  Enter <kbd>type</kbd>, then
select `0. Auto configure`.  This may or may not require another very long (like
eighteen hours) deep format; I did this deep format prior to this step so it
didn't ask me for anything.

After this, issue a <kbd>label</kbd> command and it should succeed.

A <kbd>touch /reconfigure</kbd> followed by a reboot is necessary to make the
disk completely usable I think.

After this, this disk should be a valid target for a command like 
<kbd>newfs</kbd>.  I had some amount of trouble being able to add the fixed
disk to a zpool immediately after following the above procedure; I wound up
trying <kbd>newfs /dev/rdsk/c1t2d0</kbd> followed by <kbd>zpool create -f
newpool c1t2d0</kbd> to get the disk completely usable.

For the source of some of this procedure, [here's the link][converting blocksize in linux].
It also explains how to do it in Linux.

<!-- References -->
[original scu website]: http://home.comcast.net/~SCSIguy/SCSI_FAQ/RMiller_Tools/scu.html
[converting blocksize in linux]: http://www.doki-doki.net/~lamune/computers/blocksize/
