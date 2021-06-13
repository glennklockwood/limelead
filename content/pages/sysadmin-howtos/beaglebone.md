---
title: Getting started with the BeagleBone Black
shortTitle: BeagleBone
---

## System Configuration

I have been folding much of this into [Ansible playbooks for SBCs][], so have a
look at the `beaglebone` role there for more details.

### BeagleBone-specific services

In addition to stock Debian, the BeagleBone board has some extra services that
are enabled by default:

- **cloud9** - This is the IDE that the [BeagleBone 101 page][] has you work
  through as an alternative to sshing directly into the BeagleBone and thrashing
  around. Note that this service only starts when triggered by _cloud9.socket_.
- **bonescript** - This sets up the socket and the nodejs server
  that exposes a lot of GPIO functionality via a REST interface.
- **bonescript-autorun** - Runs `/usr/local/lib/node_modules/bonescript/autorun.js`
  which does something related to watching files in the cloud9 directory
  (`/var/lib/cloud9`).
- **nodered** - This sets up the [Node-RED][] programming environment and UI.
  As far as I can tell, the fact that BeagleBone Black does this is
  undocumented.
- **nginx** - nginx is configured to proxy the above three services
  through http://beaglebone.local:80/
- **generic-board-startup** - This calls a script (`/opt/scripts/boot/generic-startup.sh`)
  that does the following:
    1. Shuts down the board if `init-eMMC-flasher` was passed as a boot argument
       by checking `/proc/cmdline` - this is used when flashing the eMMC from an
       SD card.
    2. Checks for `/etc/ssh/ssh.regenerate` and, if it exists, generates new host
       ssh keys.  Used to make each board have unique SSH keys when flashed from
       the same image.
    3. Checks for `/boot/efi/EFI/efi.gen` and, if it exists, reinstalls grub
    4. Checks for `/resizerootfs` and, if it exists, resizes the root partition
    5. Runs a board-specific script from `/opt/scripts/boot/`.  On BeagleBone
       Black, this does:
        1. Initializes a [DLP2000 projector cape][] if present (seems pretty
           specific...)
        2. Delets stuff from `/var/cache/doc-` for Beagleboards that are not
           BeagleBone Black to reclaim eMMC space.
        3. Configures the USB gadget functionality (network, mass storage device,
           serial console)
        4. Configures GPIO pins for BeagleBone Blue
        5. Configures robotics cape if desired
        6. Configures onboard WiLink (Bluetooth and Wifi) if present

It's not clear that any of these services are necessary after you're done
kicking the tires with Cloud9, BoneScript, and Node-RED.  The
_generic-board-startup_ service can probably be disabled as well as long as you
aren't using the USB gadget functionality or using the projector cape.
It will be re-enabled whenever you re-flash the eMMC, so its functionality
post-flash will always run when it is supposed to.

If you want to reclaim some eMMC space, you can also remove these BeagleBone
demo software packages directly:

    apt remove --purge bb-node-red-installer bb-usb-gadgets bone101 bonescript c9-core-installer doc-beaglebone-getting-started
    rm -rf /var/lib/cloud9 /opt/cloud9
    rm -rf /var/cache/doc-beaglebone-getting-started
    apt remove --purge nodejs npm
    rm -rf /usr/local/lib/node_modules
    sudo apt autoremove --purge

[Node-RED]: https://www.nodered.org/
[DLP2000 projector cape]: https://www.digikey.com/en/products/detail/texas-instruments/DLPDLCR2000EVM/7598640

## The Programmable Real-time Unit (PRU)

The most unique feature of BeagleBone (and its underlying TI Sitara SoC) are its
PRUs which are realtime microcontrollers that are nicely integrated with the
ARM core.  You have two options to program the PRUs:

1. **Using [TI's Code Composer Studio (CCS)][]**.  This is overly complicated if
   all you want to do is treat the PRUs as a part of an embedded Linux system
   though.
2. **Program the PRUs from within Linux** on the BeagleBone itself.  This is the
   easier approach if you are familiar with Linux but not programming ARM
   directly.

Hereafter we're only considering the second option, and the BeagleBone OS ships
with the necessary tools to make this work already in `/usr/lib/ti/pru-software-support-package`.
In this mode, the PRUs are exposed to Linux as [remote processors][] which have
a pretty simple API with which you can

1. Load "firmware" (compiled code) into a PRU
2. Start execution on a PRU
3. Stop execution on a PRU

These _remote processors_ can be accessed in `/sys/class/remoteproc` which, on
BeagleBone Black, contains:

- `remoteproc0` - the ARM Cortex-M3 processor on the BeagleBone.  This isn't
  documented very well because it is preloaded with code that handles power
  management on the board.  If you don't care about power management, I assume
  you could overwrite its firmware and do as you please with it.
- `remoteproc1` - PRU0, called `4a334000.pru`
- `remoteproc2` - PRU1, called `4a338000.pru`

### Basic usage

To load compiled firmware into a PRU, first copy the compiled code into
`/lib/firmware`:

    cp myfirmware.bin /lib/firmware/myfirmware.bin

Linux will read the contents of `/sys/class/remoteproc/remoteproc1/firmware` and
look for a file in `/lib/firmware` with that name to load into PRU0 when it is
started, so we have to tell it the name of this new firmware:

    echo "myfirmware.bin" > /sys/class/remoteproc/remoteproc1/firmware

Then tell the PRU to boot up:

    echo "start" > /sys/class/remoteproc/remoteproc1/state

TI's documentation for all this can be found in the [RemoteProc and RPMsg][]
section of the [Processor SDK Linux Software Developer's Guide][].

[TI's Code Composer Studio (CCS)]: https://www.ti.com/tool/CCSTUDIO-SITARA
[remote processors]: https://www.kernel.org/doc/html/latest/staging/remoteproc.html
[RemoteProc and RPMsg]: https://software-dl.ti.com/processor-sdk-linux/esd/docs/latest/linux/Foundational_Components/PRU-ICSS/Linux_Drivers/RemoteProc_and_RPMsg.html
[Processor SDK Linux Software Developer's Guide]: https://software-dl.ti.com/processor-sdk-linux/esd/docs/latest/devices/AM335X/linux/index.html

### Hello world example

A minimal working example of a PRU firmware source is as follows:

```c
#include <stdint.h>
#include <rsc_types.h>  /* provides struct resource_table */

#define CYCLES_PER_SECOND 200000000 /* PRU has 200 MHz clock */

#define P9_31 (1 << 0) /* R30 at 0x1 = pru1_pru0_pru_r30_0 = ball A13 = P9_31 */

volatile register uint32_t __R30; /* output register for PRU */

void main(void) {
    while (1) {
        __R30 |= P9_31; /* set first bit in register 30 */
        __delay_cycles(CYCLES_PER_SECOND / 4); /* wait 0.5 seconds */
        __R30 &= ~P9_31; /* unset first bit in register 30 */
        __delay_cycles(CYCLES_PER_SECOND / 4); /* wait 0.5 seconds */
    }
}

/* required by PRU */
#pragma DATA_SECTION(pru_remoteproc_ResourceTable, ".resource_table")
#pragma RETAIN(pru_remoteproc_ResourceTable)
struct my_resource_table {
    struct resource_table base;
    uint32_t offset[1];
} pru_remoteproc_ResourceTable = { 1, 0, 0, 0, 0 };
```

The PRU can directly toggle a subset of the BeagleBone's GPIO pins in a single
cycle by manipulating bits in register #30.  That register is exposed in
C as `__R30`, so modifying that register's contents directly triggers a change
in one or more GPIO pin states.  See the [PRU Optimizing C/C++ Compiler User
Guide][pru compiler user guide] Section 5.7.2 for more info.

The first (least significant) bit in `__R30` controls pin 31 on header P9, so
flipping that bit on and off will make that pin go high and low.  Since the PRUs
run at 200 MHz and can complete one operation per cycle, this means a pin can be
flipped on or off in 5 ns.  That's fast!

The resource table junk at the bottom has to be in any code loaded into the PRU.
This table is used to configure things like its buffers for communicating with
the ARM host and handling interrupts.

[pru compiler user guide]: https://www.ti.com/lit/ug/spruhv7b/spruhv7b.pdf

### Compiling PRU firmware

Compiling this code for the PRU can be done with either the official TI
toolchain (the `clpru` compiler and `lnkpru` linker) or the GCC frontend for
the PRU.  I haven't tried GCC yet, so let's stick with the TI toolchain.  The
minimal makefile for the above looks like this:

```make
PRU_SWPKG = /usr/lib/ti/pru-software-support-package

CC = clpru
LD = lnkpru
CFLAGS = --include_path=$(PRU_SWPKG)/include \
         --include_path=$(PRU_SWPKG)/include/am335x
LDFLAGS = $(PRU_SWPKG)/labs/lab_2/AM335x_PRU.cmd

all: am335x-pru0-fw

hello-pru0.o: hello-pru0.c
	$(CC) $(CFLAGS) $^ --output_file $@

am335x-pru0-fw: hello-pru0.o
	$(LD) $(LDFLAGS) $^ -o $@
```

This will do the following:

```
$ clpru --include_path=/usr/lib/ti/pru-software-support-package/include \
        --include_path=/usr/lib/ti/pru-software-support-package/include/am335x \
        hello-pru0.c \
        --output_file hello-pru0.o

$ lnkpru /usr/lib/ti/pru-software-support-package/labs/lab_2/AM335x_PRU.cmd \
         hello-pru0.o \
         -o am335x-pru0-fw
```

This compiles the C source into an object, then links the object with a special
linker command file (`AM335x_PRU.cmd`) to create a complete firmware that the
PRU can execute.  This firmware is called `am335x-pru0-fw`.

### Configuring GPIO pins

In the above example, we want to allow the PRU to control `P9_31` through its
`__R30` register.  To do that, we have to make sure that `P9_31` is configured
to expose its PRU output mode functionality:

    $ config-pin P9_31 pruout
    Current mode for P9_31 is:     pruout

### Launching code

You cannot load firmware onto a PRU while it's running, so check its state:

    $ cat /sys/class/remoteproc/remoteproc1/state
    offline

If it's anything but `offline`, stop it using 

    $ echo stop > /sys/class/remoteproc/remoteproc1/state

Then copy our firmware into the directory where Linux will look for new firmware
to load:

    $ cp am335x-pru0-fw /lib/firmware/am335x-pru0-fw

Then make sure that Linux will be looking for a file with this name in
`/lib/firmware`:

    $ cat /sys/class/remoteproc/remoteproc1/firmware
    am335x-pru0-fw

This tells us that when we start the PRU, it will indeed look for a file called
`am335x-pru0-fw` in `/lib/firmware`.  Now just start the PRU:

    $ echo start > /sys/class/remoteproc/remoteproc1/state

And verify that it's running by either looking at the LED to confirm that
it blinks on and off at quarter-second intervals:

{{ figure("bbb-hello-pru.gif", alt="Blinking LED controlled by the PRU") }}

Or ask Linux to check on its state:

    $ cat /sys/class/remoteproc/remoteproc1/state
    running

If the state is still `offline`, there was a problem.  Check `journalctl` for
errors:

    $ journalctl --system --priority err
    ...
    Jun 08 22:20:49 beaglebone kernel: remoteproc remoteproc1: header-less resource table
    Jun 08 22:20:49 beaglebone kernel: remoteproc remoteproc1: Boot failed: -22

In the above example, I tried to boot code that was missing the resource table
data structure.

You can download the above minimum viable product from [my BeagleBone
repository on GitHub][beaglebone-pru github].

[beaglebone-pru github]: https://github.com/glennklockwood/beaglebone-pru

## Assorted Howtos

### Determine OS image version

`cat /etc/dogtag` to see.

### Determine board version

You can `cat /proc/device-tree/model` for a single-line board description.

If you are hardcore, you can also read the EEPROM to find out.  The EEPROM is
accessible from i2c bus 0 as device `0x50`:

    $ dd if=/sys/class/i2c-dev/i2c-0/device/0-0050/eeprom ibs=1 skip=4 count=12 status=none conv=unblock cbs=12

The board identification object's format is documented (obliquely) by TI since
U-boot reads it during bootup; see [this article][EEPROM format article]
for specifics on how the EEPROM contents can be interpreted and the
[U-boot source code][] for expected values.

[EEPROM format article]: https://siliconbladeconsultants.com/2020/07/06/beaglebone-black-and-osd335x-eeprom/
[U-boot source code]: https://github.com/beagleboard/u-boot/blob/55ac96a8461d06edfa89cda37459753397de268a/board/ti/am335x/board.h

### Determine CPU temperature

Turns out you cannot because [TI does not expose thermal sensors to
Linux](https://stackoverflow.com/questions/28099822/reading-cpu-temperature-on-beaglebone-black).

### Stop onboard LEDs from blinking

These LEDs are exposed to userspace under `/sys/class/leds/*`.  You can see what
triggers their blinking by looking at the `trigger` file in this area, e.g.,

    $ cat /sys/class/leds/beaglebone\:green\:usr0/trigger
    none rfkill-any rfkill-none kbd-scrolllock kbd-numlock kbd-capslock kbd-kanalock kbd-shiftlock kbd-altgrlock kbd-ctrllock kbd-altlock kbd-shiftllock kbd-shiftrlock kbd-ctrlllock kbd-ctrlrlock mmc0 mmc1 usb-gadget usb-host timer oneshot disk-activity disk-read disk-write ide-disk mtd nand-disk [heartbeat] backlight gpio cpu cpu0 activity default-on panic netdev 

This means that it has a heartbeat trigger, or just blinks twice, pauses, and
repeats.  You can temporarily disable this behavior:

    $ echo none > /sys/class/leds/beaglebone\:green\:usr0/trigger

You can see the current default trigger in the device tree:

    $ cat /proc/device-tree/leds/led2/label && echo
    beaglebone:green:usr0

    $ cat /proc/device-tree/leds/led2/linux,default-trigger && echo
    heartbeat

Or if you want to see it in device tree source format,

    $ dtc -I fs -O dts /proc/device-tree | less

To permanently change this behavior, you have to create a new device tree
overlay since the default trigger is controlled by the kernel.  You can see
where this default value is coming from by examining the device tree blob
source you're using.  `/opt/scripts/tools/version.sh` tells you which base
device tree and overlays were loaded on boot, and it gets these by:

- `cat /proc/device-tree/chosen/base_dtb` - gives you the name of the dts file
  that generated the base device tree file that is loaded
- `ls /proc/device-tree/chosen/overlays` - gives you a list of overlays
  currently loaded

You can inspect the source of the base device tree using the following:

    $ dtc -I dtb -O dts /boot/dtbs/$(uname -r)/$(sed -e 's/\.dts.*$/.dtb/' /proc/device-tree/chosen/base_dtb) | less

And you can inspect the chosen overlays by finding their binary `dtbo` files in
`/lib/firmware` and using the same `dtc -I dtb -O dts ...` command on them.

## Access GPIOs on P8

The HDMI port on BeagleBone is implemented as a virtual cape, and it lays claim
to a bunch of the GPIO pins on header P8 (pins 27-46).  You can disable this
cape on boot by telling U-boot to not load its associated device tree overlay.

Manipulating which capes (and device tree overlays) are loaded at boot is all
done in `/boot/uEnv.txt`.  Just comment out the `disable_uboot_overlay_video=1`
line and reboot.  You can confirm that the HDMI cape is unloaded after reboot
by inspecting `/proc/device-tree/chosen/overlays/` before and after; you should
notice that `BB-HDMI-TDA998x-00A0` disappears.

More information on how U-boot and U-boot overlays work on BeagleBone (and how
they influence the default functions of all the GPIOs) on the
[BeagleBone/Debian wiki page][].

[BeagleBone/Debian wiki page]: https://elinux.org/Beagleboard:BeagleBoneBlack_Debian#U-Boot_Overlays

## Set GPIO pin modes

Debian ships with a command-line tool `config-pin` which temporarily sets the
function of each GPIO pin.  It will change the function of a pin until the next
reboot, but to change the function permanentl, you have to create a device tree
overlay (yuck).

`config-pin` expects pins specified in `pX_YY` format (e.g., `p8_15` for
GPIO1-15 or `P9_25` for GPIO3-21) and supports the following operations:

```
# Show current mode of a pin:
$ config-pin -q p9_24
Current mode for P9_24 is:     default

# List supported pin modes:
$ config-pin -l P8_42
Available modes for P8_42 are: default gpio gpio_pu gpio_pd eqep pruout pruin

# Set a pin mode:
$ config-pin p8_45 pruout
Current mode for P8_45 is:     pruout
```

A super-useful table that shows the mapping between PRU addresses, GPIO device
addresses, and headers is on the [official wiki][PRU GPIO mode table].  The
[BeagleBone Black System Reference Manual][] also has [mode mappings for the P8
header][bbb-srm p8 table] on page 65 and the analogous [table for the P9
header][bbb-srm p9 table] on page 67.

[PRU GPIO mode table]: https://elinux.org/Ti_AM33XX_PRUSSv2#Beaglebone_PRU_connections_and_modes
[bbb-srm p8 table]: https://github.com/beagleboard/beaglebone-black/wiki/System-Reference-Manual#711-connector-p8
[bbb-srm p8 table]: https://github.com/beagleboard/beaglebone-black/wiki/System-Reference-Manual#712-connector-p9

## Out-of-box experience

The out-of-box experience, despite being zero-download, feels incomplete.  It
uses a web-based user interface (nice), but dumps you into a directory full of
examples without any tutorial (not nice).  The online documentation (for
example, the [BeagleBone 101 page][]) claims that you can try code right there
in your browser.  However this functionality relies on a custom Javascript-based
framework that, while logically motivated, has no parallels outside of the
BeagleBone ecosystem, and I couldn't actually get it to work for whatever
definition of "work" makes sense.  I still don't really know what's supposed
to happen when I connect to <http://beaglebone.local/bone101/>.

In addition, a lot of the documentation is spread across [beagleboard.org][official Getting Started docs],
[elinux.org][], and a [Texas Instruments wiki][] which appears to have had all
its contents deleted from the internet recently.  The documentation contains
screen shots that are out of date, and the elinux.org wiki appears to be more a
historical record of how things have evolved rather than how things exist today
for new users; for example, many references to Angstrom Linux still exist
despite Beagleboard Black not shipping since 2013.  Sadly, it appears that there
was a lot of excitement and activity around Beagleboards in the early 2010s, but
if you weren't on the bandwagon then, you are facing an uphill journey to piece
together what documentation is presently accurate.

What follows are some notes on my experiences in June 2021.

USB tunneled Ethernet doesn't appear to work out of box.  macOS picks up the
adapter (as being unresponsive), the BeagleBone assigns itself the correct
address (192.168.7.2), but macOS doesn't see the BeagleBone network device as
being connected.  After some amount of time (I'm not sure what triggers it)
though, the adapter does come up and the BeagleBone can be accessed via
<http://192.168.7.2/>.  I think this configuration is specified in
`/etc/default/bb-boot`

The [official Getting Started docs][] suggest that there is a nice getting
started guide hosted on the board at the device IP address, but this does not
seem to be the case.  Cloud9 is what comes up if you connect to the BeagleBone
via http, and it throws you in the deep end.  I think what is meant to show up
is the [BeagleBone 101 page][].  Picking through `/etc/nginx/sites-enabled/default`
reveals that this functionality has been moved to
<http://beaglebone.local/bone101/> instead.  In total, the following sites are
configured:

- <http://beaglebone.local/> - Cloud9
- <http://beaglebone.local/bone101/> - BeagleBone 101 - although this proxies to
  port 8000 which is unresponsive.  _bonescript.service_ handles this, but
  there's some kind of bug in the _bonescript.service_ and the underlying
  nodejs script that prevents this from working.  As best I can tell, nodejs
  says the socket is already in use.  If you start this manually though, going
  to the link just gives you a static "upgrade your software" page.
- <http://beaglebone.local/nodered/> - Node-RED
- <http://beaglebone.local/ui/> - Unsure what this is about.

First thing cloud9 says to do is upgrade per <https://bbb.io/upgrade>.  This has
you just pull scripts from [some guy's GitHub repo][].  A little digging reveals
that this repo is maintained by one of the Beagleboard Foundation board members
who is engineer at Digikey; I am surprised there is no formal BeagleBone
Foundation branding around this, but the code itself looks professional.  More
information on the cast of characters involved appears [here](https://beagleboard.org/about).

Beyond this, there's not much to do--browse the example source code, run some of
the test scripts in cloud9, and move on with life.

[Ansible playbooks for SBCs]: http://github.com/glennklockwood/rpi-ansible
[BeagleBone 101 page]: https://beagleboard.org/Support/bone101
[official Getting Started docs]: https://beagleboard.org/getting-started
[some guy's GitHub repo]: https://github.com/RobertCNelson
[eLinux.org]: https://elinux.org/Beagleboard
[Texas Instruments wiki]: https://processors.wiki.ti.com/index.php
[BeagleBone Black System Reference Manual]: https://github.com/beagleboard/beaglebone-black/blob/master/BBB_SRM.pdf
