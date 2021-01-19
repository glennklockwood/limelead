---
title: Getting started with the NVIDIA Jetson Nano
shortTitle: NVIDIA Jetson Nano
---

This page is a work in progress and catalogs my thoughts in getting started
with the [NVIDIA Jetson Nano Developer Kit][].

For system setup stuff, I am maintaining [an Ansible playbook for configuring
Jetson Nano post-install](https://github.com/glennklockwood/rpi-ansible/blob/jetson-nano/jetson.yml)
too.

[NVIDIA Jetson Nano Developer Kit]: https://developer.nvidia.com/embedded/jetson-nano-developer-kit

## User Environment

I set up the NVIDIA Jetson Nano with the official [Jetson Nano Developer Kit
SD Card Image][sd-image] according to the [Getting Started docs][].  NVIDIA's
nomenclature is a little confusing; I think this image is called "JetPack" and
it includes:

1. An Ubuntu-based OS with all the NVIDIA drivers called "L4T"
2. CUDA (although you wouldn't know without digging)
3. Docker and support for containerized applications from [NVIDIA GPU
   Cloud][ngc] (NGC)

NVIDIA doesn't seem to provide strong support Jetson with a lot of its
high-profile software suites outside of learning and machine vision.  For
example,

- [DIGITS][] is a collection of Python tools for deep learning, but there is [no
  supported easy install for it on Jetson](https://forums.developer.nvidia.com/t/can-i-install-digits-on-jetson/40872).
- [RAPIDS][] is a collection of Python libraries for data science, but again,
  there's [no supported easy install for it on Jetson](https://github.com/rapidsai/cusignal/issues/8).
- [DALI][] is a collection of tools for data loading.  Again, [no support for it
  on Jetson yet](https://forums.developer.nvidia.com/t/dali-python-library-on-jetson-nano/142651).
- OpenACC offers a programming model and runtime for pragma-based GPU
  acceleration of C and Fortran apps.  [No easy support for Jetson yet](https://forums.developer.nvidia.com/t/jetson-nano-and-hpc-sdk/160750).

I also found that many analytics tools only support Pascal-generation or
newer GPUs.  There may be ways to get all of this running by building and
installing things by hand, but I was expecting a friendlier experience from a
single-board computer.

It looks to me like Jetson is really geared towards machine vision and robotics;
it is not as a general platform for learning the NVIDIA software ecosystem for
other things like high-performance computing and data analytics.

[sd-image]: https://developer.nvidia.com/jetson-nano-sd-card-image
[Getting Started docs]: https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit
[DIGITS]: https://developer.nvidia.com/DIGITS
[RAPIDS]: https://developer.nvidia.com/rapids
[DALI]: https://developer.nvidia.com/dali

### CUDA Support

The Jetson Nano SD image comes with CUDA preinstalled, but trying to use it on
a fresh install throws an error:

    glock@jetson:~$ nvcc
    -bash: nvcc: command not found

Turns out you have to manually edit your `.bashrc` and [add CUDA paths to your
environment](https://forums.developer.nvidia.com/t/cuda-nvcc-not-found/118068/2):

    export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
    export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

This struck me as a big oversight in creating a flawless out-of-box experience,
but it's easy enough to fix.  I made the following script and stuck it in
`/etc/profile.d/cuda.sh` for my Ansible setter-upper:

```bash
if [ -n "${BASH_VERSION-}" ]; then
    if [[ $PATH != */usr/local/cuda/bin* ]]; then
        export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
    fi
    if [[ $LD_LIBRARY_PATH != */usr/local/cuda/lib64* ]]; then
        export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
    fi
fi
```

### NVIDIA GPU Cloud - Containerized Applications

You can Jetson Nano's OS environment like a substrate for running containerized
environments which is a big departure from most Raspberry Pi-like single-board
computers and traditional HPC environments.  Logging into the Jetson Nano itself
gives you a lean environment--shells, text editors, and basic Linux stuff are
there, but there are no precreated Python environments, TensorFlow, etc.

Instead of installing all your own libraries and tools though, you can launch
application _containers_ that drop you in a system that has all of the necessary
bells and whistles required to develop and execute applications in a
well-defined environment.  This is closer to what one would expect in a cloud
computing environment: you choose the entire software stack you need as an
all-inclusive appliance, press go, and don't fuss with any software
dependencies, compilation, or environment-specific configuration.  It's quite
nice.

This containerized ecosystem is branded as [NVIDIA GPU-Accelerated Cloud][]
or NGC, and anyone can browse their "App Store" equivalent, the [NGC
Catalog][ngc].  I set up the CLI client using the instructions in the
[NGC Overview][] which involved

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

#### Installing Images

You can then retrieve images.  

    $ sudo ~glock/bin/ngc registry image pull nvidia/l4t-ml:r32.4.4-py3
    Logging in to https://nvcr.io... login successful.
    r32.4.4-py3: Pulling from nvidia/l4t-ml

You have to do this as root because the `ngc` command talks to Docker, and
Docker in JetPack has to be run as root.

It's not clear to me what the advantage of using the `ngc` command to pull
images is versus just calling `docker` directly.  It doesn't look like `ngc`
keeps any local information about what images have already been pulled.
See below.

#### Running Images

Once you've pulled an image from NGC,

```bash
sudo docker run \
    --runtime nvidia \
    -it \
    --rm \
    --network host \
    --volume "$HOME/nvdli-data:/nvdli-nano/data" \
    --device /dev/video0 \
    "nvcr.io/nvidia/l4t-ml:r32.4.4-py3"
```

where

- `-it` means run the container interactively
- `--rm` means delete the container when it is complete
- `--network host` means the container will open ports on host itself
- `--volume` establishes a bind mount between the local host and the container
- `--device` passes the USB camera into container for image capture

The exact image name (`nvcr.io/nvidia/l4t-ml:...`) is just the image name from
the previous step (`ngc registry image pull ...`) with `nvcr.io/` prepended.

For what it's worth, the `sudo docker run ...` command will work even if you
don't `ngc registry image pull` beforehand.  So again, I'm not sure what value
the NGC pull command does.

#### Caveats

You may have to explicitly name a tag or else you get an error like this:

    $ sudo ~glock/bin/ngc registry image pull nvidia/l4t-ml
    Logging in to https://nvcr.io... login successful.
    Error: manifest for nvcr.io/nvidia/l4t-ml:latest not found: manifest unknown: manifest unknown

I think this is because specific containers only work with specific versions of
JetPack.  It would be nice if `ngc` could detect this automatically.

#### Finding Containers

NGC seems to be quite new though, and most of the containers hosted on it are
not compatible with ARM or Jetson Nano.  I could only find a couple containers
that will actually work on Jetson:

1. [DLI Getting Started with AI on Jetson Nano][] - the container used for the
   course that is copackaged with the Nano
2. [CUDA for Arm64][] - CUDA, which also ships with Jetson Nano's OS image

NGC has a label system you could use to search for containers matching a
certain criteria (like "supports ARM64..."), but they aren't used consistently
so you kind of have to wade through a combination of labels and container names
to figure out what NGC offerings may work.  In addition, you have to read each
container's README because many only work with Pascal or newer GPUs.

I've had success looking for the following labels:

- [L4T](https://ngc.nvidia.com/catalog/containers?orderBy=modifiedDESC&pageNumber=0&query=%20label%3A%22ARM%22&quickFilter=containers&filters=)
- [ARM](https://ngc.nvidia.com/catalog/containers?orderBy=modifiedDESC&pageNumber=0&query=%20label%3A%22Arm64%22&quickFilter=containers&filters=)
- [ARM64](https://ngc.nvidia.com/catalog/containers?orderBy=modifiedDESC&pageNumber=0&query=%20label%3A%22L4T%22&quickFilter=containers&filters=) - this has a lot of containers that seem to be meant for non-Jetson systems though

[NVIDIA GPU-Accelerated Cloud]: https://www.nvidia.com/en-us/gpu-cloud/containers/
[ngc]: https://ngc.nvidia.com/
[NGC Overview]: https://docs.nvidia.com/ngc/ngc-overview/index.html
[DLI Getting Started with AI on Jetson Nano]: https://ngc.nvidia.com/catalog/containers/nvidia:dli:dli-nano-ai
[CUDA for Arm64]: https://ngc.nvidia.com/catalog/containers/nvidia:cuda-arm64

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
Jetson was adjacent to my wifi router.  I do wonder if the Jetson's physical
design interferes with cheap USB dongles' small antennae though, as both of these
dongles are rock-solid on Raspberry Pi.

### Capacity Management

NVIDIA recommends using an SD card with at least 32 GB, and that's no joke--the
reliance on container images to provide a software environment not only takes
up a lot of space, but imposes constraints on what sort of external storage you
can use.  This is because Docker relies on extended attributes which NFS does
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

[Relocating the entire docker data directory][2] to an external SSD should be
perfectly possible by editing `/etc/docker/daemon.json`.

[1]: https://stackoverflow.com/questions/54214613/error-creating-overlay-mount-to-a-nfs-mount
[2]: https://forums.docker.com/t/store-images-in-non-default-locations/77882
[nvdli course]: https://courses.nvidia.com/courses/course-v1:DLI+S-RX-02+V2/about
