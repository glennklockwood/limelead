---
title: Getting started with BeagleBone Black
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
        2. Delets stuff from `/var/cache/doc-` for BeagleBoards that are not
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

## PRU Programming

Programming to the PRUs from the BeagleBone itself depends on a set of scripts
in the [BeagleBoard cloud9-examples repository][cloud9-examples repo].  The
build process is weird because compiling, uploading code, and executing code
is all hidden by a `make` command according to the [most detailed
guides](https://markayoder.github.io/PRUCookbook/02start/start.html#_blinking_an_led).
The actual workflow appears to be:

```bash
# Stop PRU0
echo stop > /sys/class/remoteproc/remoteproc1/state

# Compile the PRU source into binary
clpru -fe /tmp/cloud9-examples/hello.pru0.o hello.pru0.c \
    --include_path=/home/glock/src/cloud9-examples/common \
    --include_path=/usr/lib/ti/pru-software-support-package/include \
    --include_path=/usr/lib/ti/pru-software-support-package/include/am335x \
    --include_path=/usr/share/ti/cgt-pru/include \
    -DCHIP=am335x \
    -DCHIP_IS_am335x \
    -DMODEL=TI_AM335x_BeagleBone_Black \
    -DPROC=pru \
    -DPRUN=0 \
    -v3 -O2 \
    --printf_support=minimal \
    --display_error_number \
    --endian=little \
    --hardware_mac=on \
    --obj_directory=/tmp/cloud9-examples \
    --pp_directory=/tmp/cloud9-examples \
    --asm_directory=/tmp/cloud9-examples \
    -ppd \
    -ppa \
    --asm_listing \
    --c_src_interlist

# Link the PRU binary
lnkpru -o /tmp/cloud9-examples/hello.pru0.out /tmp/cloud9-examples/hello.pru0.o \
    --reread_libs \
    --warn_sections \
    --stack_size=0x100 \
    --heap_size=0x100 \
    -m /tmp/cloud9-examples/hello.pru0.map \
    -i/usr/share/ti/cgt-pru/lib \
    -i/usr/share/ti/cgt-pru/include \
    /home/glock/src/cloud9-examples/common/am335x_pru.cmd \
    --library=libc.a \
    --library=/usr/lib/ti/pru-software-support-package/lib/rpmsg_lib.lib 

# Copy the binary to the PRU firmware
cp /tmp/cloud9-examples/hello.pru0.out /lib/firmware/am335x-pru0-fw

# Run the write_init_pins.sh script on this compiled binary
/home/glock/src/cloud9-examples/common/write_init_pins.sh /lib/firmware/am335x-pru0-fw

# Start the PRU back up
echo start > /sys/class/remoteproc/remoteproc1/state
```

It sounds like there may be a better way of doing this now provided by TI in
their [PRU Software Support Package][].  There is a [PRU Software Support
Package git repository][PRU-SWPKG git repo] that I haven't looked into yet that
seems a little less janky than the one bundled with the [cloud9-examples repo][]
above.  On closer examination of the actual compiler commands above though, it
sounds like the janky cloud9 build process is layered on top of stuff in
`/usr/lib/ti/pru-software-support-package`.

[PRU Software Support Package]: https://www.ti.com/tool/PRU-SWPKG
[PRU-SWPKG git repo]: https://git.ti.com/cgit/pru-software-support-package/pru-software-support-package/
[cloud9-examples repo]: https://github.com/beagleboard/cloud9-examples/tree/v2020.01/common

## Random Tips

**What image version are you running?**  `cat /etc/dogtag` to see.

**What board version do you have?**  You can read the EEPROM to find out.
The EEPROM is accessible from i2c bus 0 as device `0x50`:

```
dd if=/sys/class/i2c-dev/i2c-0/device/0-0050/eeprom ibs=1 skip=4 count=12 status=none conv=unblock cbs=12
```

The board identification object's format is documented (obliquely) by TI since
U-boot reads it during bootup; see [this article][EEPROM format article]
for specifics on how the EEPROM contents can be interpreted and the
[U-boot source code][] for expected values.

You can also `cat /proc/device-tree/model` for a single-line board description
that requires less interpretation.

[U-boot source code]: https://github.com/beagleboard/u-boot/blob/55ac96a8461d06edfa89cda37459753397de268a/board/ti/am335x/board.h
[EEPROM format article]: https://siliconbladeconsultants.com/2020/07/06/beaglebone-black-and-osd335x-eeprom/

## Out-of-box experience opinions

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
