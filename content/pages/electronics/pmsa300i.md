---
title: Using the PMSA300I Air Quality Sensor
shortTitle: Using the PMSA300I Air Quality Sensor
mathjax: True
---

The [Adafruit PMSA003I Air Quality Breakout][] is a sensor that measures and
reports the amount of particulates in ambient air.  This Plantower PMSA003I
sensor is essentially the same devices used in [PurpleAir sensors][] which
every Californian relies on to tell how safe it is to go outside during wildfire
season.

The PMSA003I exposes an I2C interface, but it is not very well documented
outside of the Adafruit libraries that support it.  It also took me a while to
figure out how the readings from this sensor relate to the AQI reported by
PurpleAir.  What follows are my notes on how all of this works.

## Getting Started - Beaglebone

The physical wireup for this sensor to a Beaglebone Black is simple.  I used
the Qwiic connector and a [Qwiic JST SH 4-pin to male header cable][] to plug
directly into the Beaglebone Black P9 header:

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

## Reading via I2C

The [PMSA300I datasheet][] documents how to interpret the contents of the I2C
registers, but `i2cdump` only gave me 0x42 for all register values.  Stay tuned
for more information on how to interact with this sensor directly through I2C.

## Interpreting sensor readings

The sensor exposes the following measurements via I2C:

1. PM1.0 concentration in units of micrograms per cubic meter (&mu;g/m<sup>3</sup>) - _standard particle_ version
2. PM2.5 concentration in &mu;g/m<sup>3</sup> - _standard particle/CF=1_ version
3. PM10 concentration in &mu;g/m<sup>3</sup> - _standard particle/CF=1_ version
4. PM1.0 concentration in &mu;g/m<sup>3</sup> - _atmospheric environment/CF=atm_ version
5. PM2.5 concentration in &mu;g/m<sup>3</sup> - _atmospheric environment/CF=atm_ version
6. PM10 concentration in &mu;g/m<sup>3</sup> - _atmospheric environment/CF=atm_ version
7. Number of particles of size &gt; 0.3 microns in units of particles per decileter
8. Number of particles of size &gt; 0.5 microns in units of particles per decileter
9. Number of particles of size &gt; 1.0 microns in units of particles per decileter
10. Number of particles of size &gt; 2.5 microns in units of particles per decileter
11. Number of particles of size &gt; 5.0 microns in units of particles per decileter
12. Number of particles of size &gt; 10 microns in units of particles per decileter

This all sounds great, but what does it _mean_?  I noticed two big mysteries
immediately:

1. I don't know what "standard particle" or "atmospheric environment" means in
   the context of the PM2.5 measurements.
2. None of these are AQI!  How do I get an AQI from these?

### Standard PM vs. Environment PM

It turns out that nobody appears to know what the difference between these two
measurements are.  There are only two hints as to which one to use.

The [PMSA300I datasheet][] simple says "CF = 1 should be used in the factory
environment" at the very bottom which suggests it is only meant to be used for
factory calibration and the _atmospheric environment_ metrics are the ones we
should use in real life.

However a number of [slides presented by researchers at the US Environmental
Protection Agency][EPA PurpleAir slides] used the _standard particle_ reading
despite the datasheet and point out that it is consistently lower than the
_atmospheric environment_ reading.  They point out that PurpleAir uses the CF=1
for indoor sensors and CF=atm for outdoor sensors, but I get the impression that
nobody but the Plantower folks who manufacture this sensor really know.

### Calculating AQI

I found that AQI is a rather mysterious metric because it is unitless, not
well-defined mathematically, and has different mathematical definitions in
different countries (and even the same country at different times!).  In
the USA, the EPA defines the AQI using a set of linear functions that each
correspond to one of eight ranges of unhealthiness.  These eight ranges are
defined using "breakpoints," and for example, the EPA defines the breakpoints
for the PM2.5 AQI as follows:

AQI Category            | Lower AQI | Upper AQI | Low Breakpoint | High Breakpoint
------------------------|-----------|-----------|----------------|--------------
Good                    |         0 |        50 |            0.0 |         12.0
Moderate                |        51 |       100 |           12.1 |         35.4
Unhealthy for sensitive |       101 |       150 |           35.5 |         55.4
Unhealthy               |       151 |       200 |           55.5 |        150.4
Very unhealthy          |       201 |       300 |          150.5 |        250.4
Hazardous               |       301 |       400 |          250.5 |        350.4
Hazardous               |       401 |       500 |          350.5 |        500.4
Hazardous               |       501 |       999 |          500.5 |      99999.9

These are up-to-date as of August 2021 and are ripped straight from the [EPA AQI
breakpoints][EPA AQI breakpoints] page.  The formula is

$ {AQI}(C) = \frac{ {AQI}\_{high} - {AQI}\_{low} } { {Breakpoint}\_{high} - {Breakpoint}\_{low} } (C - C\_{low}) + {AQI}\_{low} $

where $ C $ is the observed PM2.5 concentration from the sensor (either CF=1 or
CF=atm; your choice) and the other values come from the AQI breakpoints table.

It's probably easier to illustrate how to calculate the AQI in Python.  For
example, calculating the PM2.5 AQI from the PM2.5 concentration (`conc`) looks
something like this:

```python
AQI_BREAKPOINTS = [
    ( 50,    12.0),
    (100,    35.4),
    (150,    55.4),
    (200,   150.4),
    (300,   250.4),
    (400,   350.4),
    (500,   500.4),
    (999, 99999.9),
]

def calculate_aqi(conc):
    breakp_low, conc_low = (0, 0.0)
    for breakp_hi, conc_hi in AQI_BREAKPOINTS:
        if breakp_hi is None or conc <= conc_hi:
            break
        breakp_low, conc_low = (breakp_hi, conc_hi)

    aqi = (conc - conc_low) / (conc_hi - conc_low) * (breakp_hi - breakp_low) + breakp_low
    return aqi
```

[PMSA300I datasheet]: https://cdn-shop.adafruit.com/product-files/4632/4505_PMSA003I_series_data_manual_English_V2.6.pdf
[Adafruit PMSA003I Air Quality Breakout]: https://www.adafruit.com/product/4632
[PurpleAir sensors]: https://purpleair.com
[Qwiic JST SH 4-pin to male header cable]: https://www.adafruit.com/product/4209
[EPA PurpleAir slides]: https://www.epa.gov/sites/default/files/2021-04/documents/wildfires_and_air_quality_part_1_-_airnow_maps_and_sensors_for_communities_tribal_experience_with_the_tools.pdf
[EPA AQI breakpoints]: https://aqs.epa.gov/aqsweb/documents/codetables/aqi_breakpoints.html
