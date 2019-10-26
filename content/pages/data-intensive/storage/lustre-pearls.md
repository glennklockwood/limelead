---
title: Lustre Pearls of Wisdom
comment: |
  Should write a shortcode or something to just use the following:
  https://getbootstrap.com/docs/4.0/content/typography/#naming-a-source
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

> John, with newer Lustre clients it is possible for multiple threads to submit non-overlapping writes concurrently (also not conflicting within a single page), see LU-1669 for details.
> 
> Even so, `O_DIRECT` writes need to be synchronous to disk on the OSS, as Patrick reports, because if the OSS fails before the write is on disk there is no cached copy of the data on the client that can be used to resend the RPC.
> 
> The problem is that the ZFS OSD has very long transaction commit times for synchronous writes because it does not yet have support for the ZIL.  Using buffered writes, or having very large `O_DIRECT` writes (e.g. 40MB or larger) and large RPCs (4MB, or up to 16MB in 2.9.0) to amortize the sync overhead may be beneficial if you really want to use `O_DIRECT.`

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
