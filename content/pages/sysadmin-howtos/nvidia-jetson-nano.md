---
title: Getting started with the NVIDIA Jetson Nano
shortTitle: NVIDIA Jetson Nano
status: draft
---

This page is a work in progress and catalogs my thoughts in getting started
with the [NVIDIA Jetson Nano Developer Kit][].

## Setup

### Wifi

Wifi seemed to be super flaky.  Tried both

driver    | device
----------|--------------------------------------------------------------------
rtl8192cu | 7392:7811 Edimax Technology Co., Ltd EW-7811Un 802.11n Wireless Adapter [Realtek RTL8188CUS]
rt2800usb | 148f:5370 Ralink Technology, Corp. RT5370 Wireless Adapter

They work and can hold a connection, but the packet loss on both is > 15% and
the latency is highly variable.  These were both cheap dongles with no external
antenna so the signal may have been justifiably bad, but the radios reported
reasonable strength and other wifi devices in the same room work fine.

### Software

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

[NVIDIA Jetson Nano Developer Kit]: https://developer.nvidia.com/embedded/jetson-nano-developer-kit
[NVIDIA GPU-Accelerated Containers]: https://www.nvidia.com/en-us/gpu-cloud/containers/
[NGC Catalog]: https://ngc.nvidia.com/
