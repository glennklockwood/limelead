---
title: Using the Sense HAT on BeagleBone Black
---

The Sense HAT is a well-known peripheral (HAT) for Raspberry Pi that contains a
multitude of handy input sensors and a fancy 8x8 LED matrix.  It ships with
drivers for Raspbian OS that make it all just work, but its sensors are useful
even if you don't want to use a Raspberry Pi with it.

Since the Sense HAT relies on standard interfaces, you can wire it into any
single-board computer and, with a little work, tap into its features.  This page
contains my notes in using the Sense HAT with a BeagleBone Black, but a similar
procedure can be followed for any controller (including Arduino) that supports
I2C.

## Available Sensors

The Sense HAT contains the following sensors attached via I2C:

Model        | I2C Address    | Functionality
-------------|----------------|----------------------------------
[LPS25H][]   | `0x5C`         | measure pressure
[LSM9DS1][]  | `0x1C`, `0x6A` | accelerometer, gyroscope, magnetometer
[HTS221][]   | `0x5F`         | measure temperature and humidity

The above sensors are standard I2C devices and can easily be accessed using only
four connections (SCL, SDA, 3.3V, and ground).

[LPS25H]: https://learn.adafruit.com/adafruit-lps25-pressure-sensor
[LSM9DS1]: https://learn.adafruit.com/adafruit-lsm9ds1-accelerometer-plus-gyro-plus-magnetometer-9-dof-breakout
[HTS221]: https://learn.adafruit.com/adafruit-hts221-temperature-humidity-sensor

The LED matrix is a little more complicated:

Model        | I2C Address    | Functionality
-------------|----------------|----------------------------------
[LED2472G][] | `0x46`         | LED display driver

It works in conjuction with a 5V [SN74AHCT245PWR bus transceiver][], an external
5V power source for the LEDs, and the the on-board ATTiny88 microcontroller.  If
you wish to use the LED driver functionality, you will have to supply 5V power
as well.

[LED2472G]: https://www.st.com/en/power-management/led2472g.html
[SN74AHCT245PWR bus transceiver]: https://www.ti.com/store/ti/en/p/product/?p=SN74AHCT245PWR

Finally, there is a joystick ([Alps Alpine SKRHABE010][]) and EEPROM ([onsemi CAT24C32][])
as well:

- The joystick is wired inline with the LED matrix driver and I don't fully
  grasp why that is.
- The EEPROM is required by all Raspberry Pi HATs and has I2C address `0x50`.
  However its SCL and SDA pins are not on the same bus as the Sense HAT's
  sensors, so you have to physically wire these into the same I2C bus going into
  your BeagleBone to access it.  That said, you don't really want to mess with
  this EEPROM since messing with it will prevent the Sense HAT from working with
  regular Raspberry Pi.

[Alps Alpine SKRHABE010]: https://tech.alpsalpine.com/prod/e/html/multicontrol/switch/skrh/skrhabe010.html
[onsemi CAT24C32]: https://www.onsemi.com/products/timing-logic-memory/memory/eeprom-memory/cat24c32

## Wireup

The [full pinout for the Sense HAT's header][sense hat pinout] is published
online, but it took a little trial and error with a multimeter to figure out the
correct orientation.  It turns out that the minimum number of connections you
need to use the sensors on the Sense HAT are as follows:

{{ figure("sensehat-pinout.jpg", alt="Sense HAT pinout photo") }}

That is, you only need 3.3V, ground, and the I2C clock (SCL) and I2C data (SDA)
pins from the hat.  Connecting them to the I2C bus on a BeagleBone Black 
involves:

- Ground (black) to P9\_2 (but any ground pin will work)
- 3.3V (red) to P9\_3 (any VDD 3.3 V pin will work)
- I2C SCL (yellow) to P9\_19 which is I2C bus 2's SCL
- I2C SDA (blue) to P9\_20 which is I2C bus 2's SDA

and it should look like this:

{{ figure("bbb-sensehat.jpg", alt="Sense HAT pinout photo") }}

As soon as you apply 3.3V and ground, the LED matrix will light up.

[sense hat pinout]: https://pinout.xyz/pinout/sense_hat
