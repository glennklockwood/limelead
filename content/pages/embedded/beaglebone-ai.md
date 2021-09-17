---
title: Getting started with the BeagleBone AI
shortTitle: BeagleBone AI
order: 30
---

## Out of box

As of the 2020-04-06 Debian image, the only network interface that works out of
the box is the wifi access point (AP).

1. The USB-C network bridge for appears up on the BeagleBone, but the host
   (MacOS) sees no link activity
2. The USB serial (`/dev/tty.usbmodem1234BBBK56786` on MacOS) appears, but the
   tty doesn't appear to be configured on the BeagleBone side - perhaps because
   BeagleBone AI has a dedicated set of serial output pins that are configured
   instead?

So get into the BeagleBone AI through the AP then ssh into it:

```
imac$ ssh 192.168.8.1 -l debian
...
debian@192.168.8.1's password:
```

[Upgrading the boot scripts](#upgrading-boot-scripts) and rebooting gets the
USB network interface up and running, but you can't upgrade without first
getting into the BeagleBone AI.

### Connecting to wifi

Wifi is configured using connman.  To connect to your local wifi network:

```
debian@beaglebone:~$ sudo connmanctl
[sudo] password for debian:

connmanctl> agent on
Agent registered

connmanctl> services
...

connmanctl> connect wifi_8091334a2a5d_316e31_managed_psk
Agent RequestInput wifi_8091334a2a5d_316e31_managed_psk
  Passphrase = [ Type=psk, Requirement=mandatory ]
  Passphrase?
```

This will drop the AP connection temporarily, but it should put the BeagleBone
on your WiFi network as "beaglebone.local".

```
imac$ ssh beaglebone.local -l debian
```

### Disable the wifi AP

Disable the AP to prevent your neighbors from being able to root your new
BeagleBone.  Unlike the BeagleBone Black Wireless, the BeagleBone AI doesn't
honor the `TETHER_ENABLED` variable in `/etc/default/bb-wl18xx`; in fact, it
doesn't look like the AP setup service (`/usr/bin/bb-bbai-tether`) provides a
way to disable tethering.  Instead, you have to disable the service outright:

```
debian@beaglebone:~$ sudo systemctl disable bb-bbai-tether.service
```

## Upgrading

The OS image version you get on your BeagleBone AI depends on how long it's been
sitting in a warehouse since manufacture.  My AI came with two-year-old
firmware.

### OS image upgrade

I recommend installing the latest Debian image on the eMMC as early into the
process as possible.  My BeagleBone AI shipped with `BeagleBoard.org Debian
Image 2019-08-03` which I suspected was riddled with problems.  Here's what I
did on MacOS to upgrade:

Step 1: Download the latest image from [BeagleBoard.org Latest Firmware Images][]

    imac$ curl -O 'https://debian.beagleboard.org/images/am57xx-debian-10.3-iot-tidl-armhf-2020-04-06-6gb.img.xz'

[BeagleBoard.org Latest Firmware Images]: https://beagleboard.org/latest-images

**Step 2**: Unzip the image

    imac$ xz -d am57xx-debian-10.3-iot-tidl-armhf-2020-04-06-6gb.img.xz

**Step 3**: Write image to SD card

Plugging the SD card into my iMac resulted it coming up as `/dev/disk4`
according to Disk Utility.  So,

    imac$ sudo gdd if=am57xx-debian-10.3-iot-tidl-armhf-2020-04-06-6gb.img of=/dev/disk4 bs=4M status=progress

If you don't have GNU installed from Brew or MacPorts, just use MacOS's `dd`.

**Step 4**: Boot off the SD card

Once the SD card is fully written, power off the BeagleBone AI, insert the card,
and power back up.  BeagleBone AI will boot off the SD card which you can verify
by logging in and noting the OS image version on the ssh banner.

**Step 5**: Set the booter into flash mode

Edit `/boot/uEnv.txt` and uncomment the last line (`cmdline=`).

    ##enable x15: eMMC Flasher:
    ##make sure, these tools are installed: dosfstools rsync
    cmdline=init=/opt/scripts/tools/eMMC/init-eMMC-flasher-v3-no-eeprom.sh

Once you've edited uEnv.txt, reboot again.  The BeagleBone will begin the flashing process which you can
verify by the USR LEDs cycling in a pretty pattern.  Once the flashing has
completed, the BeagleBone AI will power itself off.  Remove the SD card, power
up, and you should boot off the new image written to the eMMC.

{% call inset("Alternative OS images", "info") %}
You may also choose to replace the BeagleBone Debian OS with one of TI's own
OS images (Linux, TI-RTOS, or Android) with the <a href="https://www.ti.com/tool/PROCESSOR-SDK-AM57X">AM57x Processor SDK</a>.
Those are much more rough experiences than Debian, but if you want to try it,
log in using the `root` user (no password) after booting from your SD image.
{% endcall %}

### Boot script upgrade

Upgrade the boot scripts by pulling from Robert Nelson's repo.  This updates a
lot of important tools the BeagleBone AI uses to configure the default network
interfaces.

    $ cd /opt/scripts/tools
    $ git pull
    $ sudo ./update_kernel.sh
    $ sudo reboot

You may have to re-[disable the wireless AP](#disable-the-wifi-ap)

## Hardware

The BeagleBone AI features a Texas Instruments Sitara AM5749 system-on-a-chip
with

* 2 &#215; [Arm Cortex-A15 cores](#cortex-a15-processors) (1.5 GHz)
* 2 &#215; [TMS320C66x digital signal processor (DSP)](#c66x-dsps) CorePacs (750 MHz)
* 4 &#215; [Embedded Vision Engine (EVE)](#eve-vector-processors) Deep Learning Accelerators (DLAs) (650 MHz)
* 2 &#215; dual-core [ARM Cortex-M4](#cortex-m4-processors) image processing unit (IPU) subsystems (213 MHz)
* 2 &#215; dual-core [Programmable Real-time Unit](#prus) / Industrial Communications
  Subsystems (PRU-ICSSes) (200 MHz)

### Cortex-A15 processors

The **microprocessor unit (MPU)** has two Arm Cortex-A15 cores.

**Purpose**: The MPU is designed to run the host OS.

### C66x DSPs

The **DSP subsystem** has two C66x digital signal processors which can perform
both fixed-point and floating-point arithmetic.  Each DSP core has two multiply
units and six add units which enable up to 12 GFLOP/s for 32-bit floating point.
or 48 GFLOP/s for 16-bit floating point.  It also has special hardware and
instructions for Galois field multiplication to hardware-accelerate parity for
error correction, RAID, etc.

**Purpose**: The DSPs are power-efficient accelerators for signal processing
algorithms that rely on dense fixed- and floating-point arithmetic such as
parity calculations and fourier transforms.

**Usage**: BeagleBone AI ships with the [TI TMS320C6000 C/C++ code generation
tools][ti c6000-cgt] which include the `cl6x` C/C++ compiler.  TI also provides
a bunch of offload libraries for [FFTs][fftlib], [transcendental math
functions][mathlib], [image processing][imglib] such as de-noising, and [linear
algebra][dsplib].  Their [accelerated libraries][] page is pretty comprehensive.

**More info**: The [TMS320C66x DSP CPU and Instruction Set Reference
Guide][c66x isa guide] contains a lot more detail about the features of these
DSPs, and the [C6000-CGT][ti c6000-cgt] webpage points to documentation on how
to use the DSP compiler toolchain.

[ti c6000-cgt]: https://www.ti.com/tool/C6000-CGT
[c66x isa guide]: https://www.ti.com/lit/ug/sprugh7/sprugh7.pdf
[fftlib]: https://www.ti.com/tool/download/FFTLIB
[mathlib]: https://www.ti.com/tool/MATHLIB
[imglib]: https://www.ti.com/tool/SPRC264
[dsplib]: https://www.ti.com/tool/SPRC265
[accelerated libraries]: https://www.ti.com/microcontrollers-mcus-processors/processors/digital-signal-processors/libraries/libraries.html

### EVE vector processors

The **EVE DLAs** each have two processors: a 32-bit general-purpose processor
called "ARP32" and a 512-bit vector coprocessor called "VCOP."  The VCOP
provides a peak capability of 20.8 GFLOP/s for 16-bit floating point.

**Purpose**: The EVE DLAs are meant to accelerate machine vision applications
including inference using neural networks.  EVE was designed as a low-power
accelerator for [autonomous vehicles][eve paper] and the like.  They are
between [1.5x and 4x faster and use more than 2x more power-efficient than the
C66x DSPs][eve perf and power].

**Usage**: For the BeagleBone AI, it appears that you are meant to interact with
the EVE DLA subsystem entirely through its [TI Deep Learning (TIDL)
libraries][tidl] rather than write your own native code against these
coprocessors.  It looks like the is a C compiler for the ARP32 (`cl-arp32`),
and the VCOP is programmed in a C++ dialect called VCOP Kernel C.  Neither
compiler is not included with BeagleBone AI.

**More info**: Accessing most of Texas Instruments' EVE developer documentation
[requires a non-disclosure agreement][eve nda thread].  In addition, the
[AM574x Technical Reference Manual][] is missing its chapter on the EVE, but
you can find a copy of it in other places including [Chapter 8 of the TDA2Px
Technical Reference Manual][tda2px trm].

[eve paper]: https://doi.org/10.1109/ISCAS.2014.6865062
[eve perf and power]: https://training.ti.com/texas-instruments-deep-learning-tidl-overview
[eve nda thread]: https://e2e.ti.com/support/processors-group/processors/f/processors-forum/967910/am5728-sitara-eve-documentation
[tidl]: https://software-dl.ti.com/processor-sdk-linux/esd/docs/05_00_00_15/linux/Foundational_Components_TIDL.html
[AM574x Technical Reference Manual]: https://www.ti.com/lit/ug/spruhz6l/spruhz6l.pdf
[tda2px trm]: https://www.ti.com/lit/ug/spruif0c/spruif0c.pdf

### Cortex-M4 processors

The two "image processor units" (IPUs) each have two ARM Cortex-M4 r0p1 cores
that run at up to 212.8 MHz.  Interestingly, these cores support performing a
multiply-accumulate in a single cycle.

**Purpose**: These are general-purpose microcontroller cores that you can use
for any near-real-time applications.  Their name arises from their intended use
in real-time image processing pipelines on Sitara AM57x SoCs, and TI supports
installing and running their real-time OS, [TI-RTOS][], on these IPU cores.
Some application notes I've found suggest these are included to control separate
coprocessors for image signal processing and display systems as you might find
in automobile backup cameras, and the TI Deep Learning (TIDL) library uses these
cores to control the EVEs.

**Usage**: Because these are just standard Cortex-M processors at heart, you
should be able to use the [GNU Arm Embedded Toolchain][linaro toolchain]
to build applications for the IPU cores.  Someone has demonstrated that
[programming the Cortex-M4 using Rust][cortex-m4 with rust] is possible if
difficult due to the vague documentation around these cores' integration on the
AM5749 SoC.

[TI-RTOS]: https://www.ti.com/tool/TI-RTOS-MCU
[linaro toolchain]: https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm
[cortex-m4 with rust]: https://github.com/cambridgeconsultants/rust-beagleboardx15-demo

### PRUs

BeagleBone AI includes two dual-core programmable real-time units (PRUs), twice
as many as earlier BeagleBones.

**Purpose**: These realtime processors are somewhere between microcontrollers
and FPGAs in that they are programmed in a RISC assembly language but have
deterministic, single-cycle execution of all operations.  This makes them ideal
for implementing timing-sensitive protocols such as Ethernet; in fact, TI
provides the code to [turn a PRU into a 100 Mbit Ethernet NIC][pru ethernet] to
demonstrate how this can be done.

**Usage**: These devices are programmed in the same way as I described on my
[BeagleBone PRU page][].  BeagleBone AI ships with the [PRU Code Generation
Tools][pru cgt] which includes the `clpru` C compiler.

[pru ethernet]: https://software-dl.ti.com/processor-sdk-linux/esd/AM65X/latest/exports/docs/linux/Foundational_Components/PRU-ICSS/Linux_Drivers/PRU-ICSS_Ethernet.html
[pru cgt]: https://www.ti.com/tool/PRU-CGT

### Linux interfaces

The BeagleBone AI exposes many of its coprocessors through the same remote processor
interface as the PRUs:

```
debian@beaglebone:~$ ls -l /sys/class/remoteproc
total 0
lrwxrwxrwx 1 root root 0 Sep 11 23:04 remoteproc0 -> ../../devices/platform/44000000.ocp/58820000.ipu/remoteproc/remoteproc0
lrwxrwxrwx 1 root root 0 Sep 11 23:04 remoteproc1 -> ../../devices/platform/44000000.ocp/55020000.ipu/remoteproc/remoteproc1
lrwxrwxrwx 1 root root 0 Sep 11 23:04 remoteproc2 -> ../../devices/platform/44000000.ocp/40800000.dsp/remoteproc/remoteproc2
lrwxrwxrwx 1 root root 0 Sep 11 23:04 remoteproc3 -> ../../devices/platform/44000000.ocp/41000000.dsp/remoteproc/remoteproc3
lrwxrwxrwx 1 root root 0 Sep 11 23:04 remoteproc4 -> ../../devices/platform/44000000.ocp/4b226004.pruss_soc_bus/4b200000.pruss/4b234000.pru/remoteproc/remoteproc4
lrwxrwxrwx 1 root root 0 Sep 11 23:04 remoteproc5 -> ../../devices/platform/44000000.ocp/4b226004.pruss_soc_bus/4b200000.pruss/4b238000.pru/remoteproc/remoteproc5
lrwxrwxrwx 1 root root 0 Sep 11 23:04 remoteproc6 -> ../../devices/platform/44000000.ocp/4b2a6004.pruss_soc_bus/4b280000.pruss/4b2b4000.pru/remoteproc/remoteproc6
lrwxrwxrwx 1 root root 0 Sep 11 23:04 remoteproc7 -> ../../devices/platform/44000000.ocp/4b2a6004.pruss_soc_bus/4b280000.pruss/4b2b8000.pru/remoteproc/remoteproc7
```

This tells us that

- remoteproc0 and remoteproc1 are the ARM Cortex-M4 "image processing units"
  (IPUs)
- remoteproc2 and remoteproc3 are the TI TMS320C66x DSPs
- remoteproc4 through remoteproc7 are our good old friends, the programmable
  real-time units (PRUs).

You may notice that the EVEs are not represented here.  It looks like the EVEs
do not have a userspace interface, and peeling apart the demo TIDL applications
that use the EVEs (see below) reveals that EVEs are accessed through `/dev/mem`.
The only way to know how to program the EVEs directly is to know their memory
space and to perform memory-mapped I/O directly into EVE registers and buffers.
Details on how to do this are likely locked away under NDA.

The remoteproc interface also allows you to inspect what the Cortex-M4 and C66x
DSPs are doing.  For example to get an idea of what code was running on the
second Cortex-M4 core (`remoteproc1`):

    $ sudo tail /sys/kernel/debug/remoteproc/remoteproc0/trace0
    [0][      0.014] [t=0x01287e67] xdc.runtime.Main: EVE2 attached
    [0][      0.017] [t=0x013bf9bb] xdc.runtime.Main: EVE3 attached
    [0][      0.020] [t=0x014f8ea5] xdc.runtime.Main: EVE4 attached
    [0][      0.020] [t=0x0150b475] xdc.runtime.Main: Opening MsgQ on EVEs...
    [0][      1.020] [t=0x1aae9599] xdc.runtime.Main: OCL:EVE1:MsgQ opened
    [0][      2.020] [t=0x340d5f4b] xdc.runtime.Main: OCL:EVE2:MsgQ opened
    [0][      3.020] [t=0x4d6c1f01] xdc.runtime.Main: OCL:EVE3:MsgQ opened
    [0][      4.020] [t=0x66caf409] xdc.runtime.Main: OCL:EVE4:MsgQ opened
    [0][      4.020] [t=0x66cc11d7] xdc.runtime.Main: Pre-allocating msgs to EVEs...
    [0][      4.021] [t=0x66d1cfd7] xdc.runtime.Main: Done OpenCL runtime initialization. Waiting for messages...

We see that it was last executing code to control the four EVE vector
coprocessors.  The TIDL library had loaded this code as part of its execution.

[BeagleBone PRU page]: {filename}beaglebone-pru.md

## TIDL

TIDL is the C++ library that provides a simple interface atop the C66x and EVE
coprocessors to do inference.  There are demo applications in two places:

1. `/var/lib/cloud9/BeagleBone/AI/tidl` contains a demo app that acts as an
   mjpg-streamer plugin to classify a video stream coming from a webcam.  It was
   developed specifically for the BeagleBone AI based on TI demo apps.

2. `/usr/share/ti/examples/tidl` contains the examples that ship with the [TIDL
   API source package][tidl api ti git repo].

[tidl api ti git repo]: https://git.ti.com/cgit/tidl/tidl-api/

The official examples from the TIDL API repo are much more expansive and include
both C++ and Python versions of code, but they haven't been Cloud9-ified and
must be accessed via command line.

### BeagleBone Demo App

The BeagleBone AI comes with a single demo application that uses both the EVEs
and C66x DSPs to demonstrate image classification.  You can run it in Cloud9
as documented in the [TIDL on BeagleBone AI][] blog post, but I had an easier
time running it directly from the command line.  To do so,

    $ cd /var/lib/cloud9/BeagleBone/AI/tidl
    $ make

This should compile.  Then plug your favorite webcam into the USB port of your
BeagleBone AI.  Confirmed that Linux recognizes the webcam:

```
$ journalctl | grep usb | tail
Sep 12 14:54:06 beaglebone kernel: usb 1-1: SerialNumber: BCA5A510
Sep 12 14:54:06 beaglebone kernel: input: UVC Camera (046d:0825) as /devices/platform/44000000.ocp/488c0000.omap_dwc3_2/488d0000.usb/xhci-hcd.1.auto/usb1/1-1/1-1:1.0/input/input2
Sep 12 14:54:06 beaglebone kernel: usbcore: registered new interface driver uvcvideo
```

Then run the demo app:

    $ make run
    /var/lib/cloud9/common/Makefile:27: MODEL=BeagleBoard.org_BeagleBone_AI,TARGET=,COMMON=/var/lib/cloud9/common
    Makefile:10: warning: overriding recipe for target 'clean'
    /var/lib/cloud9/common/Makefile:224: warning: ignoring old recipe for target 'clean'
    ...
    About to start ProcessFrame loop!!
    http://localhost:8080/?action=stream

You can then navigate to <http://beaglebone.local:8090/?action=stream> to see
the video stream.  If you put something in front of your webcam, you should see
a classification appear in green text in the upper-left corner of the video
stream:

{{ figure("tidl-classifier.png", alt="Screenshot from TIDL demo app classifier") }}

You should also see the classification appear in the terminal:

    (487)=cellular_telephone
    (487)=cellular_telephone
    (487)=cellular_telephone
    (504)=coffee_mug
    (504)=coffee_mug

You may notice that the classifier thinks a lot of things are cellular
telephones; this is because the demo app is only set up to [classify ten
different types of items][tidl demo labels]: baseballs, sunglasses, coffee
mugs, beer glasses, water bottles, bagels, digital watches, cell phones, ping
pong balls, and pill bottles.  Since these are the only things this demo app
is looking for, it will never label objects as anything else.

Sadly, cats are not among the list, but you can edit the `classification.tidl.cpp`
source and pick whatever labels you'd like from the imagenet list in
`/usr/share/ti/examples/tidl/classification/imagenet.txt`.  Or you can just
load _all_ the labels and let the classifier go nuts; change the definition of
`selected_size` and replace the list of labels with a loop that just copies
the loaded labels:

```c++
populate_labels("/usr/share/ti/examples/tidl/classification/imagenet.txt");

selected_items_size = size; // 10;
selected_items = (int *)malloc(selected_items_size*sizeof(int));
if (!selected_items) {
    std::cout << "selected_items malloc failed" << std::endl;
    return false;
}
// instead of copying individual labels, copy all of them
for (int i = 0; i < selected_items_size; i++)
    selected_items[i] = i;

std::cout << "loading configuration" << std::endl;
configuration.numFrames = 0;
```

After this change, a bunch of incorrect labels are spit out by the application,
but it is able to correctly classify George as a tabby cat:

{{ figure("tidl-classifier-george.png", alt="Screenshot from TIDL demo app classifying George the cat") }}

[TIDL on BeagleBone AI]: https://beagleboard.org/p/175809/tidl-on-beaglebone-ai-1ee263
[tidl demo labels]: https://github.com/beagleboard/cloud9-examples/blob/v2020.01/BeagleBone/AI/tidl/classification.tidl.cpp#L106-L115

### TIDL for Python

TIDL also includes a Python3 interface which is included with the BeagleBone AI
version of the TIDL API.  However it's not obvious _how_ to use it since naively
trying to run the Python example apps fails:

    $ cd /usr/share/ti/examples/tidl/pybind
    $ ./one_eo_per_frame.py
    Traceback (most recent call last):
      File "./one_eo_per_frame.py", line 35, in <module>
        from tidl import DeviceId, DeviceType, Configuration, Executor, TidlError
    ModuleNotFoundError: No module named 'tidl'

Unlike most Python packages, the TIDL Python interface is a `.so`, not a
directory full of `.py` files so I had a hard time figuring out where to look
for it.  It turns out the trick is to add the following to your `PYTHONPATH`:

    $ PYTHONPATH=/usr/share/ti/tidl/tidl_api ./imagenet.py
    Input: ../test/testvecs/input/objects/cat-pet-animal-domestic-104827.jpeg
    TIOCL FATAL: Failed to open file /dev/mem

This time TIDL was found, but we need to run as root due to TIDL's need to
directly manipulate `/dev/mem`.  So,

    $ sudo PYTHONPATH=/usr/share/ti/tidl/tidl_api ./imagenet.py
    [sudo] password for debian:
    Input: ../test/testvecs/input/objects/cat-pet-animal-domestic-104827.jpeg
    1: Egyptian_cat,   prob = 34.12%
    2: tabby,   prob = 34.12%
    3: Angora,   prob =  9.41%
    4: tiger_cat,   prob =  7.84%

Since TIDL Python apps have to run as root, you may run into unexpected errors
even if you `export PYTHONPATH=/usr/share/ti/tidl/tidl_api` in your `.bashrc`.

## Assorted Howtos

Many how-to's are covered on my [BeagleBone Black howto section]({filename}beaglebone.md#assorted-howtos).

### Determine CPU temperature

    $ cat /sys/devices/virtual/thermal/thermal_zone0/temp
    37000

This is 37 celsius.

### Give all DRAM to Linux

If you `free -m` on BeagleBone AI,

    glock@greystone:~$ free -m
                  total        used        free      shared  buff/cache   available
    Mem:            612         120         365           4         127         474
    Swap:             0           0           0

You'll see that there's only 612 MiB of RAM available to Linux, not the full
1 GiB advertised.  This is because BeagleBone's OS is configured to [reserve a
lot of memory C66x DSPs and EVE DLAs][missing memory thread].  If you don't
intend to use the DSPs or DLAs though, you can recover this memory.

First check your kernel version:

    $ uname -r
    4.14.108-ti-r143

Then edit the device tree that's loaded on boot, making sure to edit the correct
version that matches our kernel (4.14 in our case):

    $ cd /opt/source/dtb-4.14-ti
    $ git pull
    $ vi src/arm/am5729-beagleboneai.dts

Scroll down a bit and at around line 23 you'll see a block that begins with
`reserved-memory {`:

```devicetree
/*
    reserved-memory {
        #address-cells = <2>;
        #size-cells = <2>;
...
        cmem_block_mem_0: cmem_block_mem@a0000000 {
            reg = <0x0 0xa0000000 0x0 0x18000000>;
            no-map;
            status = "okay";
        };
    };
*/
```

Comment this out using C-style comments (`/* ... */`).  Also comment out the
following `cmem {` block because it references cmem memory blocks defined in the
`reserved-memory` block we just disabled above:

```devicetree
/*
    cmem {
        compatible = "ti,cmem";
        #address-cells = <1>;

...

        cmem_block_1: cmem_block@1 {
            reg = <1>;
            memory-region = <&cmem_block_mem_1_ocmc3>;
        };
    };
*/
```

Finally, comment out the bits that reference these disabled memory regions.
There are two for the IPUs (the Cortex-M4s which control the EVEs) and two for
the DSPs (C66x):

```devicetree
/*
&ipu1 {
        status = "okay";
        memory-region = <&ipu1_memory_region>;
};

&ipu2 {
        status = "okay";
        memory-region = <&ipu2_memory_region>;
};

&dsp1 {
        status = "okay";
        memory-region = <&dsp1_memory_region>;
};

&dsp2 {
        status = "okay";
        memory-region = <&dsp2_memory_region>;
};
*/
```

Then back in `/opt/source/dtb-4.14-ti` (or whatever directory matches your
kernel), run `make` as the `debian` user:

    $ make
    ...
      DTC     src/arm/am5729-beagleboneai.dtb

Then install the rebuilt device tree:

    $ sudo make install
    ...
    'src/arm/am5729-beagleboneai.dtb' -> '/boot/dtbs/4.14.108-ti-r143/am5729-beagleboneai.dtb'

After this, cross your fingers and `sudo reboot`.  Once the system comes back
up, you should see almost the full 1 GiB now:

    $ free -m
                  total        used        free      shared  buff/cache   available
    Mem:            993          51         865           5          76         913
    Swap:             0           0           0

[missing memory thread]: https://groups.google.com/g/beagleboard/c/-kDcIPsLCkc/m/xHyrFKepAgAJ
