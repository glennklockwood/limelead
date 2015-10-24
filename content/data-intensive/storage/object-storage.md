---
date: "2015-10-21T20:45:00-07:00"
draft: false
title: "Principles of Object Storage"
shortTitle: "Object Storage"
last_mod: "October 21, 2015"
parentdirs: [ 'data-intensive', 'storage' ]
---

_Note: This page remains under construction, and I will build on it as time
permits.  It is currently missing (1) diagrams, (2) a complete Implementations
section, and (3) a reasonable technical review since I don't really know what
I'm talking about._

The term "object storage" has become quite buzzworthy in the enterprise world
as a result of Amazon S3's wild successes in being the backing store behind
data giants like [Instagram][Instagram] and [Dropbox][Dropbox].  Unfortunately,
the amount of marketing nonsense surrounding the term has really diluted what
is actually a very promising storage technology that has already begun to make
its way into [extreme-scale supercomputing][Trinity].  

Object storage offers substantially better scalability, resilience, and
durability than today's parallel file systems, and for certain workloads, it
can deliver staggering amounts of bandwidth to and from compute nodes as well.
It achieves these new heights of overall performance by abandoning the notion
of files and directories.  Object stores do not support the POSIX IO calls
(open, close, read, write, seek) that file systems support.  Instead, object
stores support only two fundamental operations: PUT and GET.

## Key Features of Object Storage

This simplicity gives way to a few extremely important restrictions on what you
can do with an object store:

* PUT creates a new object and fills it with data.  
  * There is no way to modify data within an existing object as a result, so
    all objects within an object store are said to be _immutable_.
  * When a new object is created, the object store returns its unique object
    id.  This is usually a UUID that has no intrinsic meaning like a filename
    would.
* GET retrieves the contents of an object based on its object ID

To a large degree, that's it.  Editing an object means creating a completely
new copy of it with the necessary changes, and it is up to the user of the
object store to keep track of which object IDs correspond to more meaningful
information like a file name.

This gross simplicity has a number of extremely valuable implications in the
context of high-performance computing:

1. Because data is write-once, there is no need for a node to obtain a lock an
   object before reading its contents.  There is no risk of another node writing
   to that object while its is being read.
2. Because the only reference to an object is its unique object ID, a simple
   hash of the object ID can be used to determine where an object will 
   physically reside (which disk of which storage node).  There is no need for
   a compute node to contact a metadata server to determine which storage server
   actually holds an object's contents.

This combination of lock-free data access and deterministic mapping of data to
physical locations makes I/O performance extremely scalable, as there are no
intrinsic bottleneck when many compute nodes are accessing data across object
storage servers.

## The Limitations of Object Storage

The simplicity of object storage semantics makes it extremely scalable, but it
also extremely limits its utility.  Consider:

1. Objects' immutability restricts them to write-once, read-many workloads.
   This means object stores cannot be used for scratch space or hot storage,
   and their applications are limited to data archival.
2. Objects are comprised of data and an object ID and nothing else.  Any 
   metadata for an object (such as a logical file name, creation time, owner,
   access permissions) must be managed outside of the object store.  This can
   be really annoying.

Both of these drawbacks are sufficiently prohibitive that virtually all object
stores come with an additional database layer that lives directly on top of
the database layer.  This database layer (called "[gateway][DDN gateways]" or 
"[proxy][Swift proxies]" services by different vendors) provides a much nicer
front-end interface to users and typically maintains the map of an object ID
to user-friendly metadata like an object name, access permissions, and so on.

<div class="shortcode">
{{< figure src="object-store-schematic.png" link="object-store-schematic.png" alt="schematic of object storage with gateway layer" caption="Model object storage system.  Gateway servers may have a variety of features.  For example, CIFS/NFS gateways may stage data to a local disk to facilitate file modifications, and S3 gateways are usually clustered for high-availability.  Some features (basic object metadata and ACLs) may also be integrated on each object storage node itself, and some advanced features may be layered on top of a gateway interface such as S3." >}}
</div>

This separation of the object store from the user-facing access interface brings
some powerful features with it.  For example, an object store may have a 
gateway that provides an S3-compatible interface with user accounting,
fine-grained access controls, and user-defined object tags for applications
that natively speak the S3 REST API.  At the same time, a different NFS gateway
can provide an easy way for users to archive their data to the same underlying
object store with a simple `cp` command.

Because object storage does not attempt to preserve POSIX compatibility, the
gateway implementations have become convenient places to store extremely rich
object metadata that surpasses what has been traditionally provided by POSIX
and NFSv4 ACLs.  For example, the S3 API provides a means to associate arbitrary
key-value pairs with objects as user-defined metadata, and [DDN's WOS][DDN WOS]
takes an even bigger step by allowing users to query the gateway's database of
object metadata to select all objects that match the query criteria.

Much more sophisticated interfaces can be build upon object stores as well;
in fact, most parallel file systems (including Lustre, Panasas, and BeeGFS)
are built on concepts arising from object stores.  They make various compromises
in the front- and back-end to balance scalability with performance and
usability, but this flexibility is afforded by building atop object-based
(rather than block-based) data representations.

## Object Storage Implementations

This section is not written yet, but I hope to illustrate some specific
engineering components of object storage implementations.

I will first illustrate the simplicity of a basic object store using [Ian
Kirker's ShellStore][shellstore], which is a remarkably concise (albeit
insane) implementation of an object store.

I would then like to discuss the practical implementation of several
interesting commercial object stores including 
[DDN WOS][DDN WOS],
[OpenStack Swift][OpenStack Swift], 
[NetApp's StorageGRID][NetApp StorageGRID], and
[RedHat/Inktank Ceph][RedHat Ceph].  

Finally, I would like to briefly discuss [iRODS][iRODS], which provides the
gateway layer of an object store without the object store underneath.

<!-- References -->
[Instagram]: http://instagram-engineering.tumblr.com/post/13649370142/what-powers-instagram-hundreds-of-instances
[Dropbox]: http://www.datacenterknowledge.com/archives/2013/10/23/how-dropbox-stores-stuff-for-200-million-users/
[Trinity]: http://permalink.lanl.gov/object/tr?what=info:lanl-repo/lareport/LA-UR-15-20907
[DDN gateways]: http://www.ddn.com/pdfs/WOS3_Access_datasheet.pdf
[Swift proxies]: http://docs.openstack.org/developer/swift/overview_architecture.html#proxy-server
[DDN WOS]: http://www.ddn.com/products/object-storage-web-object-scaler-wos/
[shellstore]: https://github.com/ikirker/shellstore
[OpenStack Swift]: http://docs.openstack.org/developer/swift/
[NetApp StorageGRID]: http://www.netapp.com/us/products/storage-software/storagegrid/
[RedHat Ceph]: https://www.redhat.com/en/technologies/storage/ceph
[iRODS]: http://irods.org/
