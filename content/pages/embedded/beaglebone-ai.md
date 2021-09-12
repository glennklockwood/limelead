---
title: Getting started with the BeagleBone AI
shortTitle: BeagleBone AI
---

## Out of box

As of the 2020-04-06 Debian image, the only network interface that works out of
the box is the Wifi access point (AP).

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

Wifi is configured using connman.  To connect to your local Wifi network:

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

### Disable the insecure Wifi AP

Disable the AP to prevent your neighbors from being able to root your new
BeagleBone.  Unlike the BeagleBone Black Wireless, the BeagleBone AI doesn't
honor the `TETHER_ENABLED` variable in `/etc/default/bb-wl18xx`; in fact, it
doesn't look like the AP setup service (`/usr/bin/bb-bbai-tether`) provides a
way to disable tethering.  Instead, you have to disable the service outright:

```
debian@beaglebone:~$ sudo systemctl disable bb-bbai-tether.service
```

## Upgrading the OS image

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

```
##enable x15: eMMC Flasher:
##make sure, these tools are installed: dosfstools rsync
cmdline=init=/opt/scripts/tools/eMMC/init-eMMC-flasher-v3-no-eeprom.sh
```

Once you've edited uEnv.txt, reboot again.  The BeagleBone will begin the flashing process which you can
verify by the USR LEDs cycling in a pretty pattern.  Once the flashing has
completed, the BeagleBone AI will power itself off.  Remove the SD card, power
up, and you should boot off the new image written to the eMMC.

### Upgrading boot scripts

Upgrade the boot scripts by pulling from Robert Nelson's repo.  This updates a
lot of important tools the BeagleBone AI uses to configure the default network
interfaces.

```
$ cd /opt/scripts/tools
$ git pull
$ sudo ./update_kernel.sh
$ sudo reboot
```
