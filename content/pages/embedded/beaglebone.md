---
title: Getting started with the BeagleBone Black
shortTitle: BeagleBone
---

## System Configuration

I have been folding much of this into [Ansible playbooks for SBCs][], so have a
look at the `beaglebone` role there for more details.

The first step after successfully powering on is to follow the instructions on
[upgrade the software on your Beagle][bbb.io/upgrade].  Afterwards, there's
additional cleanup you can do to turn off non-essential services and free up
space on the eMMC.

[bbb.io/upgrade]: https://bbb.io/upgrade

### Basic BeagleBone security

The default login for BeagleBone is via username `debian` and password `temppwd`
which is plastered all over every interface it exposes.  This is a big problem
on BeagleBone Black Wireless because it boots up and starts its own wireless
access point (AP) by default, allowing anyone within wifi range to have full
administative access to your device.

If you live in a densely populated area (like the Bay Area, where I live), you
should disable this as soon as possible:

1. Edit `/etc/default/bb-wl18xx`
2. Change `TETHER_ENABLED=yes` to `TETHER_ENABLED=no`
3. Reboot

Once the BeagleBone comes back up, you can verify that that the access point is
off:

```
debian@beaglebone:~$ ip addr list SoftAP0
Device "SoftAP0" does not exist.
```

If the device still exists, you are likely still vulnerable.

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

### Access GPIOs on P8

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

### Set GPIO pin modes

Debian ships with a command-line tool `config-pin` which temporarily sets the
function of each GPIO pin.  It will change the function of a pin until the next
reboot, but to change the function permanently, you have to create a device tree
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
[bbb-srm p9 table]: https://github.com/beagleboard/beaglebone-black/wiki/System-Reference-Manual#712-connector-p9

### Re-image the eMMC

To install a newer version of the BeagleBone OS or reset it to the stock OS
image, you have to re-flash the OS image on the eMMC.  A lot of instructions
online say that holding down the boot select button while powering on is
enough to both boot from the SD card image and flash it to the eMMC.
**This does not work for BeagleBone Black**; it just forces the BeagleBone
Black to boot off the SD card instead of the eMMC.

To copy the SD card to the eMMC, you have to

1. Write an OS image to an SD card, insert the SD card, power down the
   BeagleBone, then power it on while holding the boot select button on the
   upper side of the BeagleBone, near the SD card slot.
2. Connect to the BeagleBone using its serial-over-USB to get to the console
   of the OS that booted off the SD card.
3. Log in and edit /boot/uEnv.txt.  At the bottom of the file, uncomment the
   following line:

```
cmdline=init=/opt/scripts/tools/eMMC/init-eMMC-flasher-v3.sh
```

This tells the BeagleBone should run the script to flash the eMMC on boot-up.

Now reboot without holding the boot select button.  This will cause the eMMC
to be re-flashed which will take a while.  After it is complete, pop out the
SD card so that the BeagleBone boots back off of eMMC, and you should have a
fresh OS installed.

## Out-of-box experience

I got a couple of different BeagleBones at the same time, and they each came
with different versions of the BeagleBone OS image.  Namely,

1. My BeagleBone Black Wireless came preinstalled with the 2018-10-07 standard
   image
2. My BeagleBone Black came preinstalled with the 2020-04-06 IoT image because
   (apparently) the standard image is no longer updated.

I had very different out-of-box experiences with these two.

### Debian Image 2018-10-07

**The good:**

The 2018-10-07 image was as-advertised.  I plugged the BeagleBone Black Wireless
into my Mac using the provided micro-USB cable and it powered on.  Three
different interfaces into the BeagleBone were immediately available:

1. My Mac recognized the FAT partition as a USB mass storage device and mounted
   it
2. My Mac also recognized the BeagleBone's serial-over-USB, exposed it as
   `/dev/tty.usbmodem2009BBWG09115`, and I was able to connect using 115,200
   baud
3. The BeagleBone started up a wireless access point to which anyone can
   connect.  Once connected, the BeagleBone is accessible at 192.168.8.1.

Using the third method (connect to the wifi AP), navigating to
<http://192.168.1.1/> brings up a version of the [BeagleBone 101 page][] that
appears to be newer than what's on beagleboard.org.  In addition to what's on
the beagleboard.org version, the embedded version of BeagleBone 101 has

1. Working BoneScript widgets
2. A neat interactive BeagleBone-UI that allows you to play with the BeagleBone
   GPIO pins visually using the browser
3. A link to and description of the onboard Node-RED services that are also
   included

**The bad:**

A lot of BeagleBone documentation is spread across [beagleboard.org][official Getting Started docs],
[elinux.org][], and a [Texas Instruments wiki][] which appears to have had all
its contents deleted from the internet recently.  The documentation contains
screen shots that are out of date, and the elinux.org wiki appears to be more a
historical record of how things have evolved rather than how things exist today
for new users; for example, many references to Angstrom Linux still exist
despite Beagleboard Black not shipping since 2013.

Sadly, it appears that there was a lot of excitement and activity around
Beagleboards in the early 2010s, but if you weren't on the bandwagon then, you
are facing an uphill journey to piece together what documentation is presently accurate.

### IoT Image 2020-04-06

A lot broke between the 2018-10-07 image and the 2020-04-06 image, leaving the
out-of-box experience for new BeagleBone owners very poor.  I hope anyone who
gets discouraged by this finds these notes and my instructions on how to
(mostly) get the 2020-04-06 image working the way older versions did.  Things
that do not work:

1. Instead of taking you to the BeagleBone 101 getting started page, going to
   <http://beaglebone.local/> dumps you into Cloud9 with a directory full of
   examples without any tutorials or other documentation.
2. The online documentation (for example, the [BeagleBone 101 page][]) claims
   that you can try code right there in your browser, but this functionality
   relies on BoneScript.
   - BoneScript is a custom Javascript-based framework that, while logically
     motivated, has no use or parallels outside of the BeagleBone ecosystem
   - In 2020-10-04, the BoneScript is completely broken out of the box so none
     of it works anyway.

What follows are some notes on my experiences and how to fix them.

#### Fixing USB-tunneled Ethernet

**USB tunneled Ethernet doesn't work out of box**.  macOS picks up the adapter
(as being unresponsive), the BeagleBone assigns itself the correct address 
192.168.7.2), but macOS doesn't see the BeagleBone network device as being
connected.  To get this USB gadget functionality working, you have to

```
$ cd /opt/scripts/tools
$ git pull
$ sudo ./update_kernel.sh
$ sudo reboot
```

#### Fixing the web UI

The [official Getting Started docs][] suggest that there is a nice getting
started guide hosted on the board at the device IP address, but this is broken.
Instead of the [BeagleBone 101 page][], you are dropped into Cloud9 without any
documentation or information on how to use the other services that are included
with BeagleBone's OS.

You can get the original BeagleBone experience by fixing BoneScript and knowing
where to point with your browser.  

BoneScript doesn't work on the 2020-10-04 image because of this error which
fills the systemd log:

```
Sep 12 03:16:36 beaglebone bonescript[839]: events.js:174
Sep 12 03:16:36 beaglebone bonescript[839]:       throw er; // Unhandled 'error' event
Sep 12 03:16:36 beaglebone bonescript[839]:       ^
Sep 12 03:16:36 beaglebone bonescript[839]: Error: listen EADDRINUSE: address already in use systemd
Sep 12 03:16:36 beaglebone bonescript[839]:     at Server.setupListenHandle [as _listen2] (net.js:1260:19)
Sep 12 03:16:36 beaglebone bonescript[839]:     at listenInCluster (net.js:1325:12)
Sep 12 03:16:36 beaglebone bonescript[839]:     at Server.listen (net.js:1423:5)
Sep 12 03:16:36 beaglebone bonescript[839]:     at mylisten (/usr/local/lib/node_modules/bonescript/src/server.js:68:12)
Sep 12 03:16:36 beaglebone bonescript[839]:     at Object.serverStart (/usr/local/lib/node_modules/bonescript/src/server.js:36:18)
Sep 12 03:16:36 beaglebone bonescript[839]:     at ReadFileContext.read [as callback] (/usr/local/lib/node_modules/bonescript/server.js:11:20)
Sep 12 03:16:36 beaglebone bonescript[839]:     at FSReqWrap.readFileAfterOpen [as oncomplete] (fs.js:238:13)
Sep 12 03:16:36 beaglebone bonescript[839]: Emitted 'error' event at:
Sep 12 03:16:36 beaglebone bonescript[839]:     at emitErrorNT (net.js:1304:8)
Sep 12 03:16:36 beaglebone bonescript[839]:     at process._tickCallback (internal/process/next_tick.js:63:19)
Sep 12 03:16:36 beaglebone systemd[1]: bonescript.service: Main process exited, code=exited, status=1/FAILURE
Sep 12 03:16:36 beaglebone systemd[1]: bonescript.service: Failed with result 'exit-code'.
```

This is because the systemd integration for BoneScript simply doesn't work.  To
make it work, first create `/etc/default/bonescript` which contains:

```
{
    "port": 8000,
    "passphrase": "hello world"
}
```

You can set `passphrase` to whatever you'd like.

Then disable the systemd socket for BoneScript; this is the magical piece that
prevents anything from working:

```
$ sudo systemctl disable bonescript.socket
```

This will cause `bonescript.service` to die and not restart, and you can verify
that systemd is no longer listening on the BoneScript socket by making sure that
lsof shows nothing for port 8000:

```
$ sudo lsof -i :8000
```

If you restart the BoneScript service by hand, it will work now:

```
$ sudo systemctl restart bonescript.service
```

You can now access the BeagleBone's proper web interface by going to
<http://beaglebone.local/bone101/Support/bone101/>.  I don't know why this was
put in such an obscure place in the newer BeagleBone Debian images.

If this all works, you should be dropped in the BeagleBone 101 page which
contains links to the demo services included:

- <http://beaglebone.local/> - Cloud9
- <http://beaglebone.local/bone101/> - This just gives you a static "upgrade
  your software" page
- <http://beaglebone.local/nodered/> - Node-RED
- <http://beaglebone.local/ui/> - A neat little interactive prober of the
  BeagleBone pinout

Unfortunately the BoneScript widgets and integration still doesn't work, but
maybe someday I will figure out how to fix that

[Ansible playbooks for SBCs]: http://github.com/glennklockwood/rpi-ansible
[BeagleBone 101 page]: https://beagleboard.org/Support/bone101
[official Getting Started docs]: https://beagleboard.org/getting-started
[some guy's GitHub repo]: https://github.com/RobertCNelson
[eLinux.org]: https://elinux.org/Beagleboard
[Texas Instruments wiki]: https://processors.wiki.ti.com/index.php
[BeagleBone Black System Reference Manual]: https://github.com/beagleboard/beaglebone-black/blob/master/BBB_SRM.pdf
