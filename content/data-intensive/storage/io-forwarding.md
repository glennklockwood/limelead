---
date: "2016-03-21T10:39:00-07:00"
draft: false
title: "I/O Forwarding for Extreme-Scale Systems"
shortTitle: "I/O Forwarding"
last_mod: "May 6, 2016"
parentdirs: [ 'data-intensive', 'storage' ]
---

## Introduction

File system I/O is a major challenge at extreme scale for two reasons:

1. a coherent and consistent view of the data must be maintained for data that
   is typically distributed across hundreds or thousands of storage servers
2. tens or hundreds of thousands of clients (compute nodes) may all be modifying
   and reading the data at the same time

That is, a lot of parallel reads and writes from a distributed _computing_
system need to be coordinated across a separate distributed _storage_ system
in a way that delivers high performance and doesn't corrupt data.

I/O forwarding, perhaps first popularized at extreme scales on IBM's Blue Gene
platform, is becoming an important tool in addressing the need to scale to
increasingly large compute and storage platforms.  The premise of I/O forwarding
is to insert a layer between the _computing_ subsystem (the compute nodes) and
the _storage_ subystem (Lustre, GPFS, etc) that shields the storage subsystem
from the full force of the parallel I/O that may be coming from the computing
subsystem.  It does this by multiplexing the I/O requests from many compute
nodes into a smaller stream of requests to the parallel file system.

## Implementations

This page is under construction and currently serves as a dumping ground for
interesting notes on emerging I/O forwarding technologies.  Some of the most
successful, promising, and interesting I/O forwarding systems include

- Blue Gene's I/O forwarder - My understanding is that the compute node kernel
  forwards all I/O-related syscalls to the I/O node where they are executed by
  the Console I/O Daemon (CIOD).  This is used on BG/L, BG/P, and BG/Q.  A good
  [paper describing the Blue Gene I/O forwarder][bgp ciod paper] was presented
  at SC'10.
- [IOFSL][iofsl site] - An implementation developed by the I/O wizards at
  Argonne whose genesis (as I understand it) is in ZOID, which was an 
  open-source reimplementation of Blue Gene's CIOD.  Currently more of an
  experimental/research platform.
- [Cray Data Virtualization Service (DVS)][cray dvs] - a Linux VFS driver that
  provides a POSIX-like mount point on the client.  Client I/O to this DVS file
  system is forwarded to one (or more, in the case of _cluster parallel mode_)
  DVS servers who act as clients for an underlying file system.
- [v9fs/9P][v9fs kdoc] is the Plan 9 remote file system and its protocol.
  Several features including its support re-exporting mounts and support for
  transport via RDMA have given it traction as a mechanism for I/O forwarding.
  - [NFS-Ganesha includes a 9P server implementation][nfs-ganesha 9p site] and
    has been used to [perform I/O forwarding][nfs-ganesha io forwarding] of
    Lustre.
  - [diod][diod site] is an implementation of a v9fs/9p server that includes
    extensions to [facilitate I/O forwarding][llnl tr-609233].

## Relevant Transport Protocols

I/O forwarding ultimately relies on an underlying network transport layer 
to move I/O requests from client nodes to the back-end storage servers, and the
routing that may be enabled by these network transport layers may themselves
behave like I/O forwarders.

- Lustre LNET is the transport layer used by Lustre, and LNET routers typically
  forward I/O requests from many Lustre clients to a much smaller group of
  Lustre object storage servers (OSSes).  Incidentally, Cray DVS (see above)
  uses LNET for its transport, but does not use LNET's routing capabilities.
- [Mercury][mercury] is an emerging transport protocol for high-performance
  computing that competes with (or plans to supercede) LNET and DVS.
  - Mercury actually replaces Lustre's RPC protocol, where Lustre RPCs are what
    are actually carried by LNET.  However Mercury includes its own network
    abstraction layer which can be used instead of LNET.
  - Mercury itself does not include an I/O forwarding system, but I/O forwarding
    can be built on top of Mercury.  For example, 
    - IOFSL (see above) can use Mercury instead of its original BMI protocol
    - [Mercury POSIX] is a project built on top of Mercury that performs POSIX
      I/O function shipping
- [BMI][bmi] is the network transport layer used in PVFS2.

## Additional Information

Other interesting links:

- [NFS-Ganesha: Why is it a better NFS server for Enterprise NAS?][nfs-ganesha ibm slides] - touches on the benefits (and limitations) of implementing file systems in user-space
- [Grave Robbers from Outer Space: Using 9P2000 Under Linux][9p2000.L paper] - the paper that describes the 9P protocol's implementation within Linux, 9P2000.L 
- [I/O Forwarding for Linux Clusters][diod io forwarding slides] - an early slide deck from LLNL describing diod as an I/O forwarder 
- [I/O Forwarding on Livermore Computing Commodity Linux Clusters][llnl tr-609233] - a really nice review of I/O forwarding principles and design goals.  Unfortunately incomplete, but still very useful.
- [v9fs: Plan 9 Resource Sharing for Linux][candid v9fs kdoc] - a more candid version of the v9fs man page for Linux that discusses its history and benefits over NFS and CIFS
- [Mercury paper in IEEE Cluster (2013)][mercury ieee paper] - the paper presenting Mercury and its design

[bgp ciod paper]: http://dx.doi.org/10.1109/SC.2010.8
[iofsl site]: http://www.mcs.anl.gov/research/projects/iofsl/
[nfs-ganesha 9p site]: https://github.com/nfs-ganesha/nfs-ganesha/wiki/9p
[nfs-ganesha ibm slides]: http://events.linuxfoundation.org/sites/events/files/slides/Collab14_nfsGanesha.pdf
[nfs-ganesha io forwarding]: https://eofs.gsi.de/fileadmin/lad2014/slides/18_Gregoire_Pichon_LAD2014_IOProxies_over_Lustre.pdf
[cray dvs]: http://docs.cray.com/books/S-0005-22/
[llnl tr-609233]: https://e-reports-ext.llnl.gov/pdf/709892.pdf
[v9fs kdoc]: http://landley.net/kdocs/Documentation/filesystems/9p.txt
[candid v9fs kdoc]: http://landley.net/kdocs/Documentation/filesystems/9p.txt
[9p2000.L paper]: https://www.usenix.org/legacy/events/usenix05/tech/freenix/hensbergen.html
[diod site]: https://github.com/chaos/diod
[diod io forwarding slides]: diod.googlecode.com/svn/wiki/garlick-iscr-2011-aug.pdf
[mercury]: https://mercury-hpc.github.io
[mercury ieee paper]: http://dx.doi.org/10.1109/CLUSTER.2013.6702617
[Mercury POSIX]: https://wiki.hpdd.intel.com/display/PUB/Fast+Forward+Storage+and+IO+Program+Documents?preview=/12127153/16843337/M6.1_PosixFunctionShipping-Demo-v3.pdf
[BMI]: http://dx.doi.org/10.1109/IPDPS.2005.128
