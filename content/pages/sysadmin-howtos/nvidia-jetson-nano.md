---
title: Getting started with the NVIDIA Jetson Nano
shortTitle: NVIDIA Jetson Nano
status: draft
---

This page is a work in progress and catalogs my thoughts in getting started
with the [NVIDIA Jetson Nano Developer Kit][].

[NVIDIA Jetson Nano Developer Kit]: https://developer.nvidia.com/embedded/jetson-nano-developer-kit

## User Environment

NVIDIA treats the Jetson Nano like a substrate for running containerized
environments which is a big departure from most Raspberry Pi-like single-board
computers and traditional HPC environments.  Logging into the Jetson Nano
itself gives you a pretty minimal environment--shells, text editors, and basic
Linux stuff are there, but no productivity software for the GPUs are.

Instead, you are meant to launch application containers that drop you in a
system that has all of the necessary bells and whistles required to develop and
execute applications in a well-defined environment.  This is much closer to
what one would expect in a cloud computing environment: you choose the entire
software ecosystem you need as an all-inclusive appliance, press go, and don't
fuss with any software dependencies, compilation, or environment-specific
configuration.

This containerized ecosystem is branded as [NVIDIA GPU-Accelerated Containers][]
or NGC, and anyone can browse their "App Store" equivalent, the [NGC Catalog][].
I set up the CLI client using the instructions in the [NGC Overview][] which
involved

1. Downloading the `ngc` binary for ARM64
2. Creating an NGC account using my Google account
3. Generating an NGC API key
4. Running `ngc config set` and punching in my API key
5. Running `ngc diag all` to make sure everything worked

Once you've got this set up, you can access NGC without having to click around
the NGC website.  For example, the NVIDIA DLI [Getting Started with AI on
Jetson Nano course][nvdli course] tells you to retrieve the latest tag for the
`dli-nano-ai` container from the website so you can fetch and run the course's
container.  Instead, you can do

    $ ngc registry image list 'nvidia/dli/dli-nano-ai:*'

to get all the available tags.

[NVIDIA GPU-Accelerated Containers]: https://www.nvidia.com/en-us/gpu-cloud/containers/
[NGC Catalog]: https://ngc.nvidia.com/
[NGC Overview]: https://docs.nvidia.com/ngc/ngc-overview/index.html

## System Setup

### Wifi

My wifi experience wasn't great.  I tried both of these USB dongles:

driver    | device
----------|--------------------------------------------------------------------
rtl8192cu | 7392:7811 Edimax Technology Co., Ltd EW-7811Un 802.11n Wireless Adapter [Realtek RTL8188CUS]
rt2800usb | 148f:5370 Ralink Technology, Corp. RT5370 Wireless Adapter

They work and can hold a connection, but the packet loss on both is > 15% and
the latency is quite variable.  These were both cheap dongles with no external
antenna, and the connection quality (loss and variability) did improve when the
Jetson was adjacent to my wifi router, but I do wonder if the Jetson's physical
design interferes with cheap USB dongles' small antennae.

### Capacity Management

NVIDIA recommends using an SD card with at least 32 GB, and that's no joke--the
reliance on container images to provide a software environment not only takes
up a lot of space, but imposes constraints on what sort of external storage you
can use since Docker apparently relies on extended attributes which NFS does
not support.

The big offender of capacity consumption is `/var/lib/docker`.  After installing
the NVIDIA Deep Learning Institute image for the [Getting Started with AI on
Jetson Nano course][nvdli course],

    root@jetson:/var/lib/docker# du -hs *
    20K     builder
    72K     buildkit
    4.0K    containers
    11M     image
    52K     network
    3.9G    overlay2
    20K     plugins
    4.0K    runtimes
    4.0K    swarm
    4.0K    tmp
    4.0K    trust
    28K     volumes

and the [`overlay2` directory cannot be relocated to NFS][1] due to its
dependence on xattr support.

It sounds like [relocating the entire docker data directory][2] to an external
SSD is perfectly possible by editing `/etc/docker/daemon.json`.

[1]: https://stackoverflow.com/questions/54214613/error-creating-overlay-mount-to-a-nfs-mount
[2]: https://forums.docker.com/t/store-images-in-non-default-locations/77882
[nvdli course]: https://courses.nvidia.com/courses/course-v1:DLI+S-RX-02+V2/about
