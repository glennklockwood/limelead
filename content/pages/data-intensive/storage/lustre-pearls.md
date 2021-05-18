---
title: Lustre Pearls of Wisdom
---

## Introduction

This page is a hand-curated list of interesting and useful explanations of how
Lustre works under the hood that I've gleaned from Lustre mailing lists.  I
keep this for my own reference, but it may be useful to others who are trying to
learn more about why Lustre behaves the way that it does.

## Threading and Serialization

From [Patrick Farrell, June 2016](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2016-June/013665.html):

> Also, in the more recent versions of Lustre (2.8 and newer), one client can
> have more than one modifying metadata request in flight at the same time.
> (that means some sort of metadata write, like a file create or permissions
> change).  That means several threads on a client can create files in
> parallel.  Prior versions were limited to one modifying metadata request
> at a time.  (For each client)

From [Andreas Dilger, October 2016](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2016-June/013666.html):

> One caveat - the Linux VFS still serializes file creates/unlinks in a single
> directory, even though the server allows them in parallel (it doesn't use
> the VFS).  Even lookups within a single directory are serialized on the
> client by the VFS except with the very latest kernels, and Lustre hasn't
> been modified yet to take advantage of this.  That said, at least progress
> is being made on that front.

Regarding the dangers of using of `O_DIRECT` from [Andreas Dilger, October 2016](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2016-October/013976.html):

> John, with newer Lustre clients it is possible for multiple threads to submit
> non-overlapping writes concurrently (also not conflicting within a single
> page), see LU-1669 for details.
> 
> Even so, `O_DIRECT` writes need to be synchronous to disk on the OSS, as
> Patrick reports, because if the OSS fails before the write is on disk there is
> no cached copy of the data on the client that can be used to resend the RPC.
> 
> The problem is that the ZFS OSD has very long transaction commit times for
> synchronous writes because it does not yet have support for the ZIL.  Using
> buffered writes, or having very large `O_DIRECT` writes (e.g. 40MB or larger)
> and large RPCs (4MB, or up to 16MB in 2.9.0) to amortize the sync overhead may
> be beneficial if you really want to use `O_DIRECT.`

Regarding sizing the MDS from [Andreas, September 2017](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2017-September/014856.html):

> There is a good presentation showing CPU speed vs. cores vs. MDS performance:
> 
> <https://www.eofs.eu/_media/events/lad14/03_shuichi_ihara_lustre_metadata_lad14.pdf>
> 
> Normally, higher GHz is good for the MDS, but if it reduces the number of
> cores by half, it may not be worthwhile.  It also depends on whether your
> workloads are mostly parallel (in which case more cores * GHz is better), or
> more serial (in which case a higher GHz is better).
> 
> In this case, cores * GHz is 3.2GHz * 8 = 25.6GHz, and 2.6GHz * 16 = 41.6GHz,
> so you would probably get better aggregate performance from the E5-2697A as
> long as you have sufficient client parallelism to drive the system heavily.

## Resource Consumption

Regarding severe memory contention when colocating Lustre clients and servers on the same memory space from [Chris Morrone, July 2016](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2016-July/013714.html):

> Lustre still has too many of its own caches with fixed, or nearly fixed caches
> size, and places where it does not play well with the kernel memory reclaim
> mechanisms.  There are too many places where lustre ignores the kernels
> requests for memory reclaim, and often goes on to use even more memory. 
> That significantly impedes the kernel's ability to keep things responsive
> when memory contention arises.
> 
> Whether there are problems with a large number of OSS and/or MDS nodes
> depends on whether you are using TCP or IB networking.

Regarding the maximum number of OSSes from [Andreas Dilger, October 2019](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2019-October/016727.html):

> With socklnd there are 3 TCP connections per client-server pair (bulk read,
> bulk write, and small message) so the maximum you could have would be around
> (65536 - 1024)/3 = 21500 (or likely fewer) clients or servers, unless you
> also configured LNet routers in between (which would allow more clients, but
> not more servers).  That isn't a limitation for most deployments, but at
> least one known limitation.  For IB there is no such connection limit that
> I'm aware of.

## Striping Mechanics

From [Andreas Dilger, March 2016](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2016-March/013370.html):

> Just to clarify, the stripe size for Lustre is not a property of the OST, but
> rather a property of each file.  The OST itself allocates space internally as
> it sees fit.  For ldiskfs space allocation is done in units of 4KB blocks
> managed in extents, while ZFS has variable block sizes (512 bytes up to 1MB or
> more, but only one block size per file) managed in a tree.  In both cases, if
> a file is sparse then no blocks are allocated for the holes in the file.
>
> As for the minimum stripe size, this is 64KB, since it isn't possible to have
> a stripe size below the `PAGE_SIZE` on the client, and some architectures
> (e.g. IA64, PowerPC, Alpha) allowed 64KB `PAGE_SIZE`.
>
> For small files, the `stripe_size` parameter is virtually meaningless, since
> the data will never exceed a single stripe in size.  What is much more
> important is to use a `stripe_count=1`, so that the client doesn't have to
> query multiple OSTs to determine the file size, timestamps, and other
> attributes.

## Lustre on Flash

From [Andreas Dilger, June 2017](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2017-June/014556.html):

> We've done a bunch of testing with the P3600 and P3700 and have seen good
> performance (mostly as OSTs, but also as MDTs, see <https://www.eofs.eu/_media/events/lad16/17_dne_analysis_roe_2_.pdf>).
> It is likely that the ZFS metadata performance is limited by ZFS itself as
> is shown in the above tests, though that will be improved significantly with
> ZFS 0.7.0 and Lustre 2.9/2.10.

From [Andreas Dilger, July 2017](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2017-July/014602.html):

> We have seen performance improvements with multiple zpools/OSTs per OSS. However, with only 5x NVMe devices per OSS you don't have many choices in terms of redundancy...

From [Patrick Farrel, Lustre Administrator and Developer Workshop (LAD) 2017, July 2017](https://www.eofs.eu/_media/events/lad17/09_patrick_farrell_lad_17_lustre_on_flash.pdf):

> Minimal overhead [on flash]: Ldiskfs + LVM gets > 95% of raw performance
>
> ...
>
> Lustre is poor at exposing [low latency for small I/O]: 4k read latency of 500
> microseconds on Cray hardware, 80 microseconds is flash (network latency ~1-5
> microseconds)

From [Andreas Dilger, May 2018](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2018-April/015507.html):

> While using an all-SSD filesystem is appealing, you might find better
> performance with some kind of hybrid storage, like ZFS + L2ARC + Metadata
> Allocation Class (this feature is in development, target 2018-09, depending on
> your timeframe).
> 
> You definitely want your MDT(s) to be SSDs, especially if you use the new
> Data-on-MDT feature to store small files tehre. The OSTs can be HDDs to give
> you a lot more capacity for the same price.

## ZFS vs. ldiskfs

From [Andreas Dilger, February 2017](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2018-February/015354.html):

> It is worthwhile to mention that using DoM is going to be a lot easier with
> ZFS in a "fluid" usage environment than it will be with ldiskfs. The ZFS
> MDTs do not have pre-allocated inode/data separation, so enabling DoM will
> just mean you can put fewer inodes on the MDT if you put more data there.
> With ldiskfs you have to decide this ratio at format time. The drawback is
> that ZFS is somewhat slower for metadata than ldiskfs, though it has
> improved in 2.10 significantly.

From [Andreas Dilger, April 2017](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2018-April/015427.html):

> Note that if you are using DoM and FLR, you probably want to format your MDT
> with non-default parameters (e.g. 256KB/inode, "-i 262144", if using
> ldiskfs), or it will normally 50% filled with inodes by default and only has
> a limited amount of space for data (< 1.5KB/inode), directories, logs, etc.

From <cite>ZFS Metadata Performance</cite> by [Alexey Zhuravlev at Lustre Administrator and Developer Workshop (LAD) 2016](https://www.eofs.eu/_media/events/lad16/02_zfs_md_performance_improvements_zhuravlev.pdf):

- Major improvements with Lustre 2.9, Lustre 2.10, ZFS 0.7
- "ZFS 0.7 and Lustre 2.10 should bring ZFS in line (or even ahead) of ldiskfs"

## Data Migration

From [Andreas Dilger, March 2017](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2017-March/014298.html):

> The underlying "`lfs migrate`" command (not the "`lfs_migrate`" script) in
> newer Lustre versions (2.9) is capable of migrating files that are in use by
> using the "`--block`" option, which prevents other processes from accessing
> or modifying the file during migration.
> 
> Unfortunately, "`lfs_migrate`" doesn't pass that argument on, though it
> wouldn't be hard to change the script. Ideally, the "`lfs_migrate`" script
> would pass all unknown options to "`lfs migrate`".
> 
> The other item of note is that setting the OST inactive on the MDS will
> prevent the MDS from deleting objects on the OST (see <https://jira.hpdd.intel.com/browse/LU-4825>
> for details).  In Lustre 2.9 and later it is possible to set on the MDS:
> 
> `mds# lctl set_param osp.<OST>.create_count=0`
> 
> to stop MDS allocation of new objects on that OST. On older versions it is
> possible to set on the OSS:
> 
> `oss# lctl set_param obdfilter.<OST>.degraded=1`
> 
> so that it tells the MDS to avoid it if possible, but this isn't a hard
> exclusion.
> 
> It is also possible to use a testing hack to mark an OST as out of inodes,
> but that only works for one OST per OSS and it sounds like that won't be
> useful in this case. 

Regarding decomissioning old OSTs, it requires some finger crossing (see
[Stephane Thiell, August 2016](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2016-August/013811.html):

> To remove your old and empty OSTs during a maintenance: stop your filesystem,
> do the writeconf on all targets and remount your MGS/MDS and then all OSTs
> minus the old ones.
> 
> With shine, stop your filesystem, comment out the old OST lines in the fs
> model file and type "`shine update`".
> 
> Doing so is _almost_ permanent, indeed care should be taken when reusing
> indexes of removed OSTs.

Regarding Lustre pools for data migration from [Andreas Dilger, July 2017](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2017-July/014627.html):

> Currently, the best way to manage different storage tiers in Lustre is via
> OST pools.  As of Lustre 2.9 it is possible to set a default OST pool on the
> whole filesystem (via "`lfs setstripe`" on the root directory) that is
> inherited for new files/directories that are created in directories that do
> not already have a default directory layout.  Also, some issues with OST
> pools were fixed in 2.9 related to inheriting the pool from a
> parent/filesystem default if other striping parameters are specified on the
> command line (e.g. set pool on parent dir, then use "`lfs setstripe -c 3`"
> to create a new file).  Together, these make it much easier to manage
> different classes of storage within a single filesystem.
> 
> Secondly, "`lfs migrate`" (and the helper script `lfs_migrate`) allow
> migration (movement) of files between OSTs (relatively) transparently to the
> applications.  The "`lfs migrate`" functionality (added in Lustre 2.5 I
> think) keeps the same inode, while moving the data from one set of OSTs to
> another set of OSTs, using the same options as "`lfs setstripe`" to specify
> the new file layout.  It is possible to migrate files opened for read, but
> it isn't possible currently to migrate files that are being modified (either
> this will cause migration to fail, or alternately it is possible to block
> user access to the file while it is being migrated).
> 
> The File Level Redundancy (FLR) feature currently under development (target
> 2.11) will improve tiered storage with Lustre, by allowing the file to be
> mirrored on multiple OSTs, rather than having to be migrated to have a copy
> exclusively on a single set of OSTs.  With FLR it would be possible to
> mirror input files into e.g. flash-based OST pool before a job starts, and
> drop the flash mirror after the job has completed, without affecting the
> original files on the disk-based OSTs.  It would also be possible to write
> new files onto the flash OST pool, and then mirror the files to the disk OST
> pool after they finish writing, and remove the flash mirror of the output
> files once the job is finished.

## procfs Counters

Regarding /proc/fs/lustre/mds/MDS/mdt/stats, from [Andreas Dilger, September 2016](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2016-September/013866.html):

> "samples" is the number of times this event was measured, and it happens that
> these request stats are all measured together.  The values to the right of the
> units are min/max/sum/[sumsq] in units of microseconds, or seconds, or
> requests.  To work out the average request waittime is:
> 
>        (sum / samples) = 1257652419050 / 611801704 = 2055usec

## Data Path

From [Andreas Dilger, August 2010](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2010-August/008296.html):

> Lustre doesn't buffer dirty pages on the OSS, only on the client.  The
> clients are granted a "reserve" of space in each OST filesystem to ensure
> there is enough free space for any cached writes that they do.
> 
> ...
> 
> The OSS layer does not aggregate writes itself.  This is done on the client
> before the writes RPCs are generated, or in the block device (elevator and
> or cache for h/w RAID devices) at the bottom end.

From [Andreas Dilger, June 2020](http://lists.lustre.org/pipermail/lustre-discuss-lustre.org/2020-June/017111.html)

> > we use TBF policy to limit rpcrate coming from clients; but I do not know
> > how to mapping of rpcrate to bandwidth or iops.
> > For example:
> > if I set a client's `rpcrate=10`，how much bandwith or iops the client can
> > get in theory?
> 
> Currently, the TBF policies only deal with RPCs.  For most systems today, you
> are probably using 4MB RPC size (`osc.*.max_pages_per_rpc=1024`), so if you
> set `rpcrate=10` the clients will be able to get at most 40MB/s (assuming
> applications do relatively linear IO).  If applications have small random
> IOPS then `rpcrate=10` may get up to 256 4KB writes per RPC, or about 2560
> IOPS = 10MB/s.

From [Andreas, May 2021](https://vi4io.slack.com/archives/CBJFGMHMK/p1621356549009200)

> ldiskfs OSTs won't do writeback caching, but may do writethrough caching,
> depending on settings (and IO size, depending on version)
>
> ZFS can only do writeback caching, but can be tuned to aggressively discard
> cache after the write completes.

## Architectural Design Decisions

From [Andreas, February 2021](http://lists.lustre.org/pipermail/lustre-devel-lustre.org/2021-February/010217.html):

> > I am curious to find the reason behind 'pre-create object' for a new file/directory creation.
>
> Yes, precreating OST objects avoids latency, but it is as much for network latency as it is for disk latency.  For ldiskfs the inode allocation is in memory and journaled, so does not depend on seek latency at all. 
> 
> Another reason to precreate objects is to ensure that the OST does not run out of inodes for files that the MDS already created.  For ldiskfs this is an issue because the number of OST inodes is fixed at format time. For ZFS it is an issue because regular file IO can consume all the space and prevent inode allocation. 
> 
> Finally, object precreation simplifies recovery because we have a good idea whether/which objects should exist or not after a server restart. 
