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

The I2C interface is actually provided by the ATTiny microcontroller which gives
a nicer ([albeit undocumented][undocumented attiny]) interface into the actual
LED2472G circuit.  The [Sense HAT schematics][] suggest the LED matrix
requires 5V since there's a 5V [SN74AHCT245PWR bus transceiver][] inline with
it, but I've found that just using 3.3V is sufficient to drive the LED matrix.

[LED2472G]: https://www.st.com/en/power-management/led2472g.html
[Sense HAT schematics]: https://datasheets.raspberrypi.org/sense-hat/sense-hat-schematics.pdf
[SN74AHCT245PWR bus transceiver]: https://www.ti.com/store/ti/en/p/product/?p=SN74AHCT245PWR
[undocumented attiny]: https://www.raspberrypi.org/forums/viewtopic.php?t=207775

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

As soon as you apply 3.3V and ground, the LED matrix will light up.  You can
also verify that the I2C devices are detected by querying with `i2cdetect`:

```
$ i2cdetect -y -r 2
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- 1c -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- 46 -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- 5c -- -- 5f 
60: -- -- -- -- -- -- -- -- -- -- 6a -- -- -- -- -- 
70: -- -- -- -- -- -- -- --                         
```

Referencing the table above, we see that the LSM9DS1's magnetometer (`0x1C`),
LPS25H (`0x5C`), HTS221 (`0x5F`), and LSM9DS1's accelerometer/gyroscope (`0x6a`)
are all detected.

[sense hat pinout]: https://pinout.xyz/pinout/sense_hat

## Accessing sensors with Python

The easiest way to verify that you can talk to the Sense HAT's sensors is using
CircuitPython libraries.  First set up a virtual environment with all the
necessary libraries:

```
$ python3 -mvenv adafruit
$ . adafruit/bin/activate
(adafruit) $ pip install adafruit-blinka
(adafruit) $ pip install adafruit_bbio
```

Then try out each sensor individually.

### LPS25 pressure sensor

Following the instructions on the [CircuitPython LPS2x Python library documentation][], first install the library:

```
(adafruit) $ pip3 install adafruit-circuitpython-lps2x
```

Then run this simple Python code, noting that we have to explicitly pass the I2C
address because the CircuitPython library expects the LPS25 to be at a different
address:

```python
import board
import adafruit_lps2x

i2c = board.I2C()
lps = adafruit_lps2x.LPS25(i2c_bus=i2c, address=0x5c)

print("Pressure:    {:.2f} hPa".format(lps.pressure))
print("Temperature: {:.2f} C".format(lps.temperature))
```

To test this,

```
(adafruit) $ python3 test-lps25.py 
Pressure:    1013.27 hPa
Temperature: 29.06 C
```

Recall from physics class that atmospheric pressure is 1013.25 hectopascals.

[CircuitPython LPS2x Python library documentation]: https://circuitpython.readthedocs.io/projects/lps2x/en/latest/index.html

### LSM9DS1 accelerometer, gyroscope, and magnetometer

Following the instructions on the [CircuitPython LSM9DS1 library documentation][], first install the library:

```
(adafruit) $ pip3 install adafruit-circuitpython-lsm9ds1
```

Then run this Python code:

```python
import board
import adafruit_lsm9ds1

i2c = board.I2C()
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(
    i2c=i2c,
    mag_address=0x1C,
    xg_address=0x6A)

print("Accelerometer: x={:7.3f}  y={:7.3f}  z={:7.3f} m/s^2".format(*sensor.acceleration))
print("Magnetometer:  x={:7.3f}  y={:7.3f}  z={:7.3f} gauss".format(*sensor.magnetic))
print("Gyroscope:     x={:7.3f}  y={:7.3f}  z={:7.3f} radians/sec".format(*sensor.gyro))
print("Thermometer:   {:.2f} C".format(sensor.temperature))
```

Note that the LSM9DS1 exposes two I2C addresses: one for the magnetometer, and
another for the accelerometer and gyroscope.  We have to specify the addresses
for both explicitly here since the CircuitPython library's defaults are not the
ones used by the Sense HAT.

To then test this,

```
(adafruit) $ python3 test-lsm9ds1.py
Accelerometer: x=  5.611  y=-10.551  z= 19.600 m/s^2
Magnetometer:  x=  0.256  y=  0.315  z=  0.173 gauss
Gyroscope:     x= -1.005  y= -3.195  z= -0.805 radians/sec
Thermometer:   25.50 C
```

[CircuitPython LSM9DS1 library documentation]: https://circuitpython.readthedocs.io/projects/lsm9ds1/en/latest/

### HTS221 temperature and humidity sensor

Following the instructions on the [CircuitPython HTS221 library documentation][], first install the library:

```
(adafruit) $ pip3 install adafruit-circuitpython-hts221
```

Then run this Python code:

```python
import board
import adafruit_hts221

i2c = board.I2C()
hts = adafruit_hts221.HTS221(i2c)

print("Relative humidity: {:.1f}%".format(hts.relative_humidity))
print("Temperature:       {:.2f} C".format(hts.temperature))
```

You should see output that looks like this:

```
(adafruit) $ python3 test-hts221.py
Relative humidity: 51.0%
Temperature:       30.23 C
```

[CircuitPython HTS221 library documentation]: https://circuitpython.readthedocs.io/projects/hts221/en/latest/index.html

### LED matrix display

There is no CircuitPython library for the Sense HAT's LED2472G and 8x8 LED
matrix because the Sense HAT doesn't actually expose the LED2472G natively;
instead, its onboard ATTiny microcontroller exposes an I2C interface that makes
programming the LED matrix much easier.

However, we can still make our own CircuitPython driver for the Sense HAT's I2C
interface into these LEDs.  It looks something like this:

```python
import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice

DEVICE_ADDRESS = 0x46

class LED2472G:
    def __init__(self, i2c_bus, address=DEVICE_ADDRESS):
        self.i2c_device = I2CDevice(i2c, address)
        self.clear()

    def clear(self):
        self.pixels = [0] * (8 * 8 * 3 + 1)

    def set_pixel(self, x, y, red, green, blue):
        linear_addr = x * 8 + y
        r_addr = (y * 24) + x + 1
        g_addr = r_addr + 8
        b_addr = g_addr + 8
        self.pixels[r_addr] = int(red * 64)
        self.pixels[g_addr] = int(green * 64)
        self.pixels[b_addr] = int(blue * 64)

    def update(self):
        with self.i2c_device as display:
            display.write(bytearray(self.pixels))
```

Put simply, we control the 64 LEDs using the knowledge that I2C registers...

- 1-8 control the redness of LEDs along the first row
- 9-16 control the greenness of the LEDs along the first row
- 17-24 control the blueness of the LEDs along the first row
- 25-32 control the redness of LEDs along the second row
- 33-40 control the greenness of the LEDs along the second row
- etc

The value of each register only holds six bits (0b00111111), so 63 is the
highest brightness you can set.  If you set the two highest-order bits, (e.g.,
`0b11000000)`, you wind up lighting up part of the next LED in the column,
the lower six bits are ignored, and the intended LED sits at maximum brightness.

To test the above driver, you can do something like this:

```python
i2c = board.I2C()
display = LED2472G(i2c)

print("Use ctrl+d to exit the following loop!")
while True:
    addr = input("Enter x, y (0-7): ")
    x, y = [int(z) for z in addr.replace(",", " ").split()]
    value = input("Enter r, g, b (0.0-1.0): ")
    r, g, b = [float(z) for z in value.replace(",", " ").split()]
    display.clear()
    display.set_pixel(x, y, r, g, b)
    display.update()
```

Enter x and y coordinates (in zero-based indexing) and red, green, and blue
values that range from 0.0 to 1.0, and the corresponding LED should illuminate
to that color.
