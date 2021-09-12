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

The BeagleBone AI has significantly more peripherals than the BeagleBone Black,
and many are exposed via the same remote processor interface as the PRUs:

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
  (IPUs).  Each IPU has two Cortex-M4 cores.
- remoteproc2 and remoteproc3 are the TI TMS320C66x digital signal processor
  (DSP) "CorePacs."  Each has wide vector instructions that can do up to 32&#215; 32-bit multiplies per cycle.
- remoteproc4 through remoteproc7 are our good old friends, the BeagleBone 
  programmable real-time units (PRUs).

These devices can be programmed with a process similar to programming PRUs that
I describe in my [BeagleBone PRU page][].

[BeagleBone PRU page]: {filename}beaglebone-pru.md

## Assorted Howtos

Many how-to's are covered on my [BeagleBone Black howto section]({filename}beaglebone.md#assorted-howtos).

### Determine CPU temperature

    $ cat /sys/devices/virtual/thermal/thermal_zone0/temp
    37000

This is 37 celsius.
