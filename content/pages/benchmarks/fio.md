---
title: Getting Started with fio
shortTitle: fio
---

[fio][] is an I/O benchmarking tool maintained by Jens Axboe designed to test
the Linux kernel I/O interfaces.  It has a huge number of plugins ("engines")
for different APIs (standard POSIX, libaio, uring, etc) and is widely used to
test single-node performance for storage devices and appliances. Just about
every SSD spec sheet and enterprise storage appliance has performance numbers
derived from fio tests.

It's not an HPC I/O test as such, but it's very useful for testing the
performance of a single compute node or the drives underneath a parallel file
system. If you are looking for something fio-like that works across multiple
nodes, check out [elbencho]({filename}elbencho.md).

{% call alert(type="info") %}
This page is a work in progress and contains notes I've shared with others about
basic fio usage.
{% endcall %}

[fio]: https://github.com/axboe/fio

## Choice of engine

Everyone uses the libaio engine to get the highest performance out of their
storage systems. When people talk about fio queue depths, they're usually
talking about the queues that the libaio library exposes. Be mindful that few
(if any) HPC applications actually use libaio, so if you are trying to measure
the performance an application might experience, don't use libaio. It's not
realistic.

## Basic measurements

### Read IOPS

```
[global]
name=fio-rand-read
filename=fio-rand-read
rw=randread
bs=4K
direct=1
numjobs=8
time_based
runtime=300
group_reporting

[file1]
size=512G
ioengine=libaio
iodepth=64
```

### Random Writes

```
[global]
name=fio-rand-write
filename=fio-rand-write
rw=randwrite
bs=4K
direct=1
numjobs=8
time_based
runtime=300
group_reporting

[file1]
size=512G
ioengine=libaio
iodepth=64
```
