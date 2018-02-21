---
date: "2018-01-06T12:52:00-07:00"
draft: false
title: "Getting started with the Terasic DE10-Nano"
last_mod: "January 6, 2018"
parentdirs: [ 'sysadmin-howtos' ]
---

## Table of Contents

* [1. Initial Setup](#1-initial-setup)
    * [1.1. Downloading the OS image](#1-1-downloading-the-os-image)
    * [1.2. Resize the file system](#1-2-resize-the-file-system)
* [2. Connecting](#2-connecting)
    * [2.1. Serial connection](#2-1-serial-connection)
    * [2.2. Ethernet over USB](#2-2-ethernet-over-usb)
    * [2.3. SSH](#2-3-ssh)
    * [2.4. VNC](#2-4-vnc)
* [3. Basic Configuration](#3-basic-configuration)
    * [3.1. Adding a non-root user](#3-1-adding-a-non-root-user)
    * [3.2. Installing Software](#3-2-installing-software)
    * [3.3. Basic Security](#3-3-basic-security)
    * [3.4. Enabling non-root i2c, spi, and GPIO access](#3-4-enabling-non-root-i2c-spi-and-gpio-access)
* [4. Advanced Configuration](#4-advanced-configuration)
    * [4.1. Getting wifi working](#4-1-getting-wifi-working)
   
## 1. Initial Setup

My host computer is an iMac running macOS, and I used this to get my DE10-Nano
up and running.  Because the DE10-Nano and the Altera software stack aren't
really meant to work with macOS, I make heavy use of Virtualbox (for macOS) and
a CentOS 7 virtual machine to do some of the Linux-specific stuff.  I'll note
which parts of the following instructions require Linux specifically.

### 1.1. Downloading the OS image

The DE10-nano kit comes with a micro-SD card that is supposed to come
pre-flashed with Angstrom Linux and the appropriate Altera drivers, but mine
came empty.  So, I went to the [Terasic DE10-Nano Kit download page at Intel][] and downloaded
    
    de10-nano-image-Angstrom-v2016.12.socfpga-sdimg.2017.03.31.tgz
    
which contains only one file (`de10-nano-image-Angstrom-v2016.12.socfpga-sdimg`)
which is the image.

I plugged the blank micro-SD card into my iMac and used
[Etcher][] to burn it.  Etcher only lets you write image
files that end with `.img` and not `.sdimg`, so I had to add the `.img`
extension on to the uncompressed `de10-nano-image-Angstrom-v2016.12.socfpga-sdimg`
file.

### 1.2. Resize the file system

The SD card shipped by Terasic is 8 GB but the Angstrom Linux image is only
~2.5 GB, so there's a lot of free space on the card that Linux doesn't use by
default.  I opted to expand the partition and file system after flashing the
image so I could make use of the full 8 GB.

Expanding the file system cannot be done live, so you need a second Linux system
on which you can perform the following expansion process for the newly flashed
SD card.  I used a Virtualbox VM with my USB SD card reader passed through.

My SD card showed up as `/dev/sdb` when I plugged it in.  It contains a
`vfat`-based boot file system (called `de10-nano`) and an `ext3`-based root
file system (with no name).  Unmount them:

    # umount /dev/sdb1
    # umount /dev/sdb2

Then we mess around with the partition table using `parted`.  Note that you'll
be deleting partitions in the partition table, then defining new larger
partitions atop the data that remained unchanged.  This sounds a little scary,
but it works:

    # parted /dev/sdb
    (parted) unit s                                                           
    (parted) p
    Model: Mass Storage Device (scsi)
    Disk /dev/sdb: 15441920s
    Sector size (logical/physical): 512B/512B
    Partition Table: msdos
    Disk Flags: 
    
    Number  Start    End       Size      Type     File system  Flags
     3      2048s    6143s     4096s     primary
     1      6144s    210943s   204800s   primary  fat16        boot, lba
     2      210944s  4700159s  4489216s  primary  ext3

Partition 2 (ext3) is the root partition that we want to expand.  So, we first
delete that partition definition:

    (parted) rm 2

Then recreate it with the same starting offset (`210994`) but using 100% of the
remaining space:

    (parted) mkpart primary 210944s 100%
    
    (parted) p                                                                
    Model: Mass Storage Device (scsi)
    Disk /dev/sdb: 15441920s
    Sector size (logical/physical): 512B/512B
    Partition Table: msdos
    Disk Flags: 
    
    Number  Start    End        Size       Type     File system  Flags
     3      2048s    6143s      4096s      primary
     1      6144s    210943s    204800s    primary  fat16        boot, lba
     2      210944s  15441919s  15230976s  primary  ext3
     
    (parted) q
    
Now we've resized the physical partition.  Run `e2fsck` on the file system that
was affected by this partition change:

    # e2fsck -f /dev/sdb2
    
Then expand the ext3 file system to use the remaining space on the newly
enlarged partition:

    # resize2fs /dev/sdb2
    resize2fs 1.42.9 (28-Dec-2013)
    Resizing the filesystem on /dev/sdb2 to 1903872 (4k) blocks.
    The filesystem on /dev/sdb2 is now 1903872 blocks long.

    
## 2. Connecting

Once your micro-SD card is flashed and the DE10-nano is successfully booted, one
of the user LEDs should pulse like a heartbeat once Linux is booted.

Once Linux is booted, the DE10-nano is very easy to get into; the only account
is `root`, and it has no password.  You can get in via

* Serial connection via the UART-to-USB mini-B connection on the DE10-nano
* SSH (passwordless root login is enabled--yuck!)
* VNC (again, passwordless root login to desktop works)

### 2.1. Serial connection

    glock@Glenns-iMac:~$ sudo cu -l /dev/tty.usbserial-A106I3A5 -s 115200
    
    Password:
    Connected.
    
    .---O---.                                           
    |       |                  .-.           o o        
    |   |   |-----.-----.-----.| |   .----..-----.-----.
    |       |     | __  |  ---'| '--.|  .-'|     |     |
    |   |   |  |  |     |---  ||  --'|  |  |  '  | | | |
    '---'---'--'--'--.  |-----''----''--'  '-----'-'-'-'
                    -'  |
                    '---'
    
    The Angstrom Distribution de10-nano ttyS0
    
    Angstrom v2016.12 - Kernel 4.1.33-ltsi-altera
    
    de10-nano login: root
    Password:

The default `root` account has no password, so just hit return.

### 2.2. Ethernet over USB

The DE10-SOC comes configured to use RNDIS to tunnel Ethernet over USB; this
protocol is only supported on Windows and Linux though, so _Ethernet over USB
will not work on modern macOS versions_.  Plugging the USB-OTG into my Mac does
literally nothing other than enumerate the board as Linux "Multifunction
Composite Gadget."  The USB mass storage device won't even show up on Mac, so
you can't read the Ethernet over USB documentation that should come up per the
Intel documentation.

I opted to just pass through the device from macOS into a CentOS 7 VM, where the
device seems to work exactly as intended.  Once the appropriate device was
passed through, unplugging and replugging the USB cable causes the Linux VM to
show:

    [  172.825663] usb 1-1: Manufacturer: Linux 4.1.33-ltsi-altera with ffb40000.usb
    [  172.870983] usbcore: registered new interface driver cdc_ether
    [  172.874240] cdc_acm 1-1:1.2: ttyACM0: USB ACM device
    [  172.881254] usbcore: registered new interface driver cdc_acm
    [  172.881256] cdc_acm: USB Abstract Control Model driver for USB modems and ISDN adapters
    [  172.889530] rndis_host 1-1:1.0 usb0: register 'rndis_host' at usb-0000:00:0c.0-1, RNDIS device, 06:2f:81:67:98:2f
    [  172.889545] usbcore: registered new interface driver rndis_host
    [  172.891935] usb-storage 1-1:1.4: USB Mass Storage device detected
    [  172.905545] scsi host3: usb-storage 1-1:1.4
    [  172.905595] usbcore: registered new interface driver usb-storage
    [  172.907863] usbcore: registered new interface driver uas
    [  172.916021] IPv6: ADDRCONF(NETDEV_UP): enp0s12u1: link is not ready

We see that `enp0s12u1` is the new Ethernet-over-USB device.  This has to be
configured to use the same subnet as the DE10; the appropriate settings are

* IP: 192.168.7.2
* Netmask: 255.255.255.0
* Gateway: 192.168.7.1

Use either the GUI or `ifconfig` to set these.  Then you should be able to
`ping 192.168.7.1` to talk to the DE10.

### 2.3. SSH

Get the IP of the system from either your home router or (if you've logged in
via serial) `ifconfig`.  Then SSH to this IP address:

    $ ssh root@192.168.1.182

The default ECSDA encryption is a bit slow, so ssh may hang for longer than
usual before prompting to accept the host key:

    The authenticity of host '192.168.1.182 (192.168.1.182)' can't be established.
    ECDSA key fingerprint is ....
    Are you sure you want to continue connecting (yes/no)? yes
    Warning: Permanently added '192.168.1.182' (ECDSA) to the list of known hosts.
    glock@192.168.1.182's password: 
    de10-nano:~$ who
    glock           pts/0           00:00   Dec 26 21:32:29  192.168.1.128
    
### 2.4. VNC

The default VNC client that ships with macOS doesn't seem to work with the
DE10-nano's VNC server, so I followed Terasic's instructions and downloaded the
free RealVNC client.  Connecting to the IP address (192.168.1.182 in my case)
just worked and dropped me in an XFCE desktop, logged in as root.

## 3. Basic Configuration

### 3.1. Adding a non-root user

First thing to do after logging in is set a root password:

    root@de10-nano:~# passwd

Then add an unprivileged user and set its password:

    root@de10-nano:~# useradd --comment "Glenn K. Lockwood" --gid 100 --groups wheel,staff --create-home --shell /bin/bash glock
    root@de10-nano:~# passwd glock

Make sure the user account works:

    root@de10-nano:~# su - glock
    mesg: Operation not permitted
    de10-nano:~$ whoami
    glock

Not sure why the `mesg: Operation not permitted` error comes up, but it's
harmless.

### 3.2. Installing Software

    # opkg update
    # opkg list | grep sudo
    # opkg install sudo
    
Then

    # visudo

and ensure that `wheel` group members are allowed to sudo by uncommenting the
following line:

    ## Uncomment to allow members of group wheel to execute any command
    %wheel ALL=(ALL) ALL

Other useful software packages to install include

| package      | description 
|--------------|---------------------------------------------------------------
| `coreutils`  | replace the busybox version of common Linux commands with the full Linux versions
| `man`        | so you can read manual pages
| `man-pages`  | the actual man pages
| `file`       | determine the file type
| `python-pip` | so you can `pip install` python packages
| `screen`     | GNU screen

It's also helpful to `opkg list > opkg_list.txt` so that you can just grep a
local copy of the software repository when searching for packages.

### 3.3. Basic Security

Edit `/etc/ssh/sshd_config` and change `PermitRootLogin` to `no`.

Disable the VNC service (if you aren't using it):

    # systemctl stop de10-nano-x11vnc-init.service
    # systemctl disable de10-nano-x11vnc-init.service
    # systemctl status de10-nano-x11vnc-init.service

You can also go ahead and disable `de10-nano-xfce-init.service` as well if you
don't plan on using the desktop UI at all.

### 3.4. Enabling non-root i2c, spi, and GPIO access

First create new groups called `i2c`, `spi`, and `gpio` (the GIDs don't matter).  Then create a file called `/etc/udev/rules.d/99-com.rules` which contains:

    SUBSYSTEM=="i2c-dev", GROUP="i2c", MODE="0660"
    SUBSYSTEM=="spidev", GROUP="spi", MODE="0660"
    SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c '\
        chown -R root:gpio /sys/class/gpio && chmod -R 770 /sys/class/gpio;\
        chown -R root:gpio /sys/devices/virtual/gpio && chmod -R 770 /sys/devices/virtual/gpio;\
        chown -R root:gpio /sys$devpath && chmod -R 770 /sys$devpath\
    '"

Incidentally, this file is taken (in part) from Raspbian and is exactly how Raspberry Pi allows non-root users to manipulate the I2C, SPI, and GPIO devices on that SoC.  There are some caveats surrounding the GPIO case since there is latency associated with all the `chown`s that must happen when GPIO pins are initialized by an application.  See [GPIO/I2C/SPI-access without root-permissions][] for the specific caveats on how to work around this.

## 4. Advanced Configuration

### 4.1. Getting wifi working

I have an rt8192-based USB wifi dongle that I wanted to plug into the DE10-nano.
After buying a [USB OTG adapter][] to add some standard USB type B ports into
which I could plug my [Edimax wifi dongle][].  On the first plug-in, everything
seemed to work well and I configured the adapter per 
[Adafruit's BeagleBone wifi guide][] and it worked, but after rebooting, the wifi
adapter no longer worked and I started getting these suspicious USB bus errors:

    [   18.433665] rtl_usb: reg 0x4, usbctrl_vendorreq TimeOut! status:0xffffff92 value=0x80208f0e
    [   28.436455] rtl_usb: reg 0x21, usbctrl_vendorreq TimeOut! status:0xffffff92 value=0x80208f0e
    [   38.436463] rtl_usb: reg 0x0, usbctrl_vendorreq TimeOut! status:0xffffff92 value=0x80674120
    [   39.146471] dwc2 ffb40000.usb: s3c_hsotg_handle_rx: unknown status 000e0004
    [   40.146460] dwc2 ffb40000.usb: s3c_hsotg_handle_rx: unknown status 000e000f
    [   40.153623] usb 1-1-port1: cannot reset (err = -110)
    [   41.156459] dwc2 ffb40000.usb: s3c_hsotg_handle_rx: unknown status 000e0000
    [   41.163619] usb 1-1-port1: cannot reset (err = -110)

After a few minutes, I got some nasty deadlock warnings from the kernel:

    [  240.236457] INFO: task kworker/1:0:12 blocked for more than 120 seconds.
    [  240.250413]       Tainted: G           O    4.1.33-ltsi-altera #1
    [  240.263716] "echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.
    [  240.278970] kworker/1:0     D c07dc978     0    12      2 0x00000000
    [  240.292799] Workqueue: events_power_efficient reg_timeout_work
    [  240.305982] [<c07dc978>] (__schedule) from [<c07dcdcc>] (schedule+0x4c/0xa4)
    [  240.320348] [<c07dcdcc>] (schedule) from [<c07dd174>] (schedule_preempt_disabled+0x18/0x1c)
    [  240.336170] [<c07dd174>] (schedule_preempt_disabled) from [<c07de894>] (__mutex_lock_slowpath+0xac/0x164)
    [  240.353196] [<c07de894>] (__mutex_lock_slowpath) from [<c07de9a8>] (mutex_lock+0x5c/0x60)
    [  240.368849] [<c07de9a8>] (mutex_lock) from [<c05ec958>] (rtnl_lock+0x20/0x24)
    [  240.383543] [<c05ec958>] (rtnl_lock) from [<c073698c>] (reg_timeout_work+0x18/0x3c)
    [  240.398784] [<c073698c>] (reg_timeout_work) from [<c003e094>] (process_one_work+0x210/0x50c)
    [  240.414829] [<c003e094>] (process_one_work) from [<c003eecc>] (worker_thread+0x54/0x568)
    [  240.430462] [<c003eecc>] (worker_thread) from [<c00440f0>] (kthread+0xec/0x104)
    [  240.445296] [<c00440f0>] (kthread) from [<c000fb68>] (ret_from_fork+0x14/0x2c)

After scouring the output of `dmesg` and `journalctl -b`, I noticed that on
boot, the USB OTG adapter and the wifi actually did configure and come up
momentarily, but they went offline at around the time that these messages
appeared:

    [    7.631038] usb0: HOST MAC de:82:da:8a:80:bb
    [    7.641618] usb0: MAC 4e:3a:11:5e:1b:a7
    [    7.658212] g_multi gadget: Multifunction Composite Gadget
    [    7.670041] g_multi gadget: userspace failed to provide iSerialNumber
    [    7.682810] g_multi gadget: g_multi ready
    [    7.696105] dwc2 ffb40000.usb: bound driver g_multi

It turns out that the DE10-Nano has a service that enables Ethernet-over-USB on
bootup and effectively hijacks the USB OTG port on boot.  Disabling this
service: 

    # systemctl disable de10-nano-gadget-init.service

appears to be absolutely required to use the DE10-Nano as a USB host, or else
the USB OTG port gets configured as a host, then switches to a device, then
leaves different parts of Linux confused about its ultimate state.

I later found that the USB would still drop with this error, suggesting that
the device was reverting from host mode:

    [  588.465205] dwc2 ffb40000.usb: Mode Mismatch Interrupt: currently in Device mode

Disabling the `de10-nano-synergy-init` service seems to work around this:

    # systemctl disable de10-nano-synergy-init.service

The configuration for this service tries to bind the synergy client to the USB
OTG Ethernet gadget, so this may have been causing the regression.

[Terasic DE10-Nano Kit download page at Intel]: https://downloadcenter.intel.com/download/26687/
[Etcher]: http://www.etcher.io
[GPIO/I2C/SPI-access without root-permissions]: http://forum.up-community.org/discussion/2141/tutorial-gpio-i2c-spi-access-without-root-permissions
[USB OTG adapter]: http://a.co/cVUx9Qk
[Edimax wifi dongle]: http://a.co/452ghll
[Adafruit's BeagleBone wifi guide]: https://learn.adafruit.com/beaglebone/wifi
