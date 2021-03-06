---
title: Configuring Raspberry Pi for Headless Boot
shortTitle: RPi Headless Boot
---

If a `wpa_supplicant.conf` file is located in the `/boot` directory of a freshly
flashed Raspbian SD card, it will be copied into `/etc/wpa_supplicant` when the
Pi is booted.  This `wpa_supplicant.conf` file can be created and placed on the
SD card using the same system you used to copy the Raspbian image to the SD
card, allowing you to boot up a Raspberry Pi for the first time and have it
automatically connect to your wifi network.

This `wpa_supplicant.conf` should look something like this:

    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1
    country=US
    
    network={
        ssid="my_wifi_ssid"
        psk="my_password_in_plaintext"
        key_mgmt=WPA-PSK
    }

Of note, `ctrl_interface=` is required for command-line utilities to communicate
with wpa-supplicant.  Without this, you're apt to get errors like "Could not
connect to wpa\_supplicant."

You also have to make sure that SSH is enabled on first boot to actually access
your newly minted Pi over wifi.  To do this, put an empty file named `ssh` into
the same `/boot` directory of the SD card.  Raspbian will detect this file on
boot, enable SSH and remote login, and then delete this file.

From this point, you can use something like [Ansible to configure the Raspberry
Pi][ansible-config] without having to plug in a keyboard, mouse, or monitor.
Just be sure to change the default login/password, since anyone who can ssh to
the Pi will be able to log in using the `pi` user account.

[ansible-config]: https://github.com/glennklockwood/rpi-ansible
