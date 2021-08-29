---
title: Using the PMSA300I Particle Sensor
shortTitle: Using the PMSA300I Particle Sensor
---

These are my notes on playing with the [Adafruit PMSA003I Air Quality
Breakout](https://www.adafruit.com/product/4632) which can measure and report
various air quality statistics.  This is one of the sensors used in PurpleAir
sensors which are indispensible during wildfire season in California, but its
I2C interface is not very well documented despite Adafruit providing full
library support for both Python and Arduino.

## Getting Started - Beaglebone

The physical wireup for this sensor is simple.  I used the Qwiic connector and a
[Qwiic JST SH 4-pin to male header cable](https://www.adafruit.com/product/4209)
to plug directly into the Beaglebone Black P9 header:

- Black (Ground) to P9\_45 (but any ground pin will work)
- Red (3.3V) to P9\_3
- Yellow (I2C SCL) to P9\_19 which is I2C bus 2's SCL
- Blue (I2C SDA) to P9\_20 which is I2C bus 2's SDA

{{ figure("bbb-pmsa300i.jpg", alt="PMSA300I wireup to Beaglebone Black") }}

The easiest way to verify that I2C is wired up and the sensor is working is to
use the Adafruit Python drivers which work fine on Beaglebone.  Make sure you
have `python3-venv` installed via apt, then

```
$ python3 -mvenv adafruit
$ . adafruit/bin/activate
(adafruit) $ pip install adafruit-blinka
(adafruit) $ pip install adafruit_bbio
(adafruit) $ pip install https://files.pythonhosted.org/packages/6d/b8/15436b3d9925ed29aeb8f67c1b18b708f37c95e2b4106da8c9585c9d810c/adafruit-circuitpython-pm25-2.1.4.tar.gz
```

To verify that the sensor works, use the example library bundled with the
adafruit-circuitpython-pm25 library:

```
(adafruit) $ wget https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_PM25/main/examples/pm25_simpletest.py
(adafruit) $ python3 pm25_simpletest.py
```

## Interacting with the sensor through I2C

The [PMSA300I datasheet][] documents how to interpret the contents of the I2C
registers, but `i2cdump` only gave me 0x42 for all register values.  Stay tuned
for more information on how to interact with this sensor directly through I2C.

[PMSA300I datasheet]: https://cdn-shop.adafruit.com/product-files/4632/4505_PMSA003I_series_data_manual_English_V2.6.pdf
