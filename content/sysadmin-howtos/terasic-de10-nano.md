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

# 1. Initial Setup

My host computer is an iMac running macOS, and I used this to get my DE10-Nano
up and running.  Because the DE10-Nano and the Altera software stack aren't
really meant to work with macOS, I make heavy use of Virtualbox (for macOS) and
a CentOS 7 virtual machine to do some of the Linux-specific stuff.  I'll note
which parts of the following instructions require Linux specifically.

## 1.1. Downloading the OS image

The DE10-nano kit comes with a micro-SD card that is supposed to come
pre-flashed with Angstrom Linux and the appropriate Altera drivers, but mine
came empty.  So, I went to the [Terasic DE10-Nano Kit download page at
Intel](https://downloadcenter.intel.com/download/26687/) and downloaded
    
    de10-nano-image-Angstrom-v2016.12.socfpga-sdimg.2017.03.31.tgz
    
which contains only one file (`de10-nano-image-Angstrom-v2016.12.socfpga-sdimg`)
which is the image.

I plugged the blank micro-SD card into my iMac and used
[Etcher](http://www.etcher.io) to burn it.  Etcher only lets you write image
files that end with `.img` and not `.sdimg`, so I had to add the `.img`
extension on to the uncompressed `de10-nano-image-Angstrom-v2016.12.socfpga-sdimg`
file.

## 1.2. Resize the file system

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

    
# 2. Connecting

Once your micro-SD card is flashed and the DE10-nano is successfully booted, one
of the user LEDs should pulse like a heartbeat once Linux is booted.

Once Linux is booted, the DE10-nano is very easy to get into; the only account
is `root`, and it has no password.  You can get in via

* Serial connection via the UART-to-USB mini-B connection on the DE10-nano
* SSH (passwordless root login is enabled--yuck!)
* VNC (again, passwordless root login to desktop works)

## 2.1. Serial connection

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

## 2.2. Ethernet over USB

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

## 2.3. SSH

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
    
## 2.4. VNC

The default VNC client that ships with macOS doesn't seem to work with the
DE10-nano's VNC server, so I followed Terasic's instructions and downloaded the
free RealVNC client.  Connecting to the IP address (192.168.1.182 in my case)
just worked and dropped me in an XFCE desktop, logged in as root.

# 3. Basic Configuration

## 3.1. Adding a non-root user

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

## 3.2. Installing Software

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

* `coreutils` - replace the busybox version of common Linux commands with the full Linux versions
* `file` - determine the file type

It's also helpful to `opkg list > opkg_list.txt` so that you can just grep a
local copy of the software repository when searching for packages.

## 3.3. Basic Security

Edit `/etc/ssh/sshd_config` and change `PermitRootLogin` to `no`.

Disable the VNC service (if you aren't using it):

    # systemctl stop de10-nano-x11vnc-init.service
    # systemctl disable de10-nano-x11vnc-init.service
    # systemctl status de10-nano-x11vnc-init.service

You can also go ahead and disable `de10-nano-xfce-init.service` as well if you
don't plan on using the desktop UI at all.
