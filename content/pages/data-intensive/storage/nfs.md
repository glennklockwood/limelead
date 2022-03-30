---
title: How NFS works
shortTitle: How NFS works
status: published
---

These are random notes I've taken while playing with NFS as I work through a
good (though dated) [miniature book on NFS][1] by [Professor Erez Zadok][2].

Although NFS itself has not been a high-performance interface for networked
file systems, many concepts that it employs are in use by HPC parallel file
systems.  Knowing how NFS works helps understand how these other file systems
work, and knowing why NFS is slow helps understand the design decisions that
have guided HPC-optimized file systems.

There are also a few recent extensions to NFS that _can_ make it a
high-performance parallel client.  VAST is perhaps the most interesting of such
implementations since it employs [NFS over RDMA][3], [nconnect][4], and an
[enhanced NFS multipathing][5] to enable parallel, scale-out I/O performance.

## NFS version 2

This isn't really worth discussing here since it's archaic.

## NFS version 3

NFS version 3 is famously stateless; the NFS server does not keep track of who
has the file system mounted or what files are open.  It even goes so far as to
not implement `open` or `close` commands, making it kind of like an object store
in its low-level semantics.  Instead, all NFS clients rely on the NFS server to
provide _file handles_ which are magical tokens that uniquely identify files or
directories.

As a result, 

* **mounting** an NFS export actually involves asking a special service on the
  NFS server for the _root file handle_.
* **opening** a file on an NFS export involves performing recursive `LOOKUP`
  commands given the _file handle_ of a parent directory and the name of a
  file or directory in that parent.  This starts with the _root file handle_.
* **reading** from a file involves `READ`ing data from a _file handle_ given a
  byte offset and number of bytes
* **writing** to a file involves `WRITE`ing data to a _file handle_ at a given byte
  offset
* **closing** a file, well, doesn't happen because you never opened the file.
  If you want, you can `COMMIT` and force both client and server to flush any
  cached writes down to persistent media.

Because NFSv3 is stateless but POSIX file I/O is inherently stateful, there's
a bunch of wonky bolt-on services required by NFS servers in practice to make
stateless NFSv3 operate like a stateful file system.  For example,

* allowing clients to statefully mount the NFS export (`mount -t nfs`) is
  enabled by `mountd`
* allowing clients to hold locks on files (e.g., `flock`) is enabled by 
  `lockd`

In practice, NFSv3 is like a good idea in principle that forgot to include a lot
of important features used in practice.

### Lock Manager (lockd) and Status Monitor (statd)

The state of all outstanding NFS locks is persisted by the NFS statd on a local
file system on the NFS server.  These outstanding locks can be viewed in
`/var/lib/nfs/sm`.  For example, taking a file lock on a file named `hello` on
an NFS mount on a client named _cloverdale_:

    glock@cloverdale:/mnt/nfs$ flock hello sleep 30

results in the following appearing on the server:

    root@synology:/var/lib/nfs/sm# ls -lrt
    total 4
    -rw------- 1 root root 92 Mar 29 19:54 cloverdale
    root@synology:/var/lib/nfs/sm# cat cloverdale
    0100007f 000186b5 00000003 00000010 66a89ab53b650b00804d729c00000000 192.168.50.27 synology

Note that merely opening a file for writes does not lock it; this is why casual
file editing from multiple NFS clients can result in file corruption.

## NFS version 4

NFSv4 is a massive improvement over NFSv3 that

1. rolls up the core NFSv3 service and all the required add-ons into a single
   standard
2. adds a bunch of new features that enhance performance and functionality that
   were completely missing from NFSv3

[1]: https://www.fsl.cs.sunysb.edu/~ezk/cse506-s19/handouts/ch1+6.pdf
[2]: https://www.fsl.cs.sunysb.edu/~ezk
[3]: https://www.usenix.org/legacy/events/fast02/wips.html#callaghan
[4]: https://lkml.iu.edu/hypermail/linux/kernel/1907.2/02845.html
[5]: https://vastdata.com/blog/meet-your-need-for-speed-with-nfs/
