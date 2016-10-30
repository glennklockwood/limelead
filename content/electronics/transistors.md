---
date: "2016-10-24T20:45:00-07:00"
draft: false
last_mod: "October 24, 2016"
title: "Experimenting with transistors and Raspberry Pi"
shortTitle: "Experimenting with transistors"
parentdirs: [ "electronics" ]
---

## Contents

- [Introduction](#introduction)
- [Building a test circuit](#building-a-test-circuit)
- [Experimenting with the test circuit](#experimenting-with-the-test-circuit)
    - [Identifying the different transistor modes](#1-identifying-the-different-transistor-modes)
    - [Identifying the threshold voltage](#2-identifying-the-threshold-voltage)
- [Automating the experiment on Raspberry Pi](#automating-the-experiment-on-raspberry-pi)
    - [Digital Potentiometers](#digital-potentiometers)
    - [Analog-to-Digital Converters](#analog-to-digital-converters)
    - [All-digital transistor test circuit](#all-digital-transistor-test-circuit)
- [Going forward](#going-forward)

## Introduction

Transistors are a fundamental component in digital electronics from which we
can build circuits that can perform logic.  At their core, they act like
on/off switches that can be manipulated electrically, and although this is a
simple concept, I had a hard time understanding exactly _how_ they worked in
the context of analog components.  For example, in [a blog post I wrote about
understanding a roulette wheel kit][mk152 blog], I could not figure out exactly
when a resistor-capacitor series that was charging or discharging would switch
a gate on or off.

A lot of websites explain what transistors accomplish and how the collector,
base, and emitter, are related to this behavior.  For example, [Sparkfun's
transistor page][sparkfun transistor page] breaks down the _operating modes_ of
your standard NPN transistor into the following:

- **saturation mode** happens when the voltage at the base (with respect to
  ground; V<sub>base</sub>) is higher than both the voltage at the emitter
  and collector (again, with respect to ground; V<sub>emitter</sub> and
  V<sub>collector</sub>)
- **active mode** happens when the base voltage (V<sub>base</sub>) is higher
  than the emitter V<sub>emitter</sub> but lower than the collector
  V<sub>collector</sub>
- **cutoff mode** happens when the base voltage (V<sub>base</sub>) is lower than
  both the collector (V<sub>collector</sub>) and emitter (V<sub>emitter</sub>)

But just having these relationships and a few equations weren't enough to help
me understand how I could use these transistors in actual circuits.

## Building a test circuit

To get a hands-on understanding of what these modes look like in practice, I
built a circuit with a 10K potentiometer plugged into the base so that I could
see at what point the transistor started conducting:

<div class="shortcode">
{{< figure src="2n2222-experiment-circuit.png" link="2n2222-experiment-circuit.png" alt="Transistor and potentiometer test circuit diagram" >}}
</div>

where

- R1 pulls up the emitter voltage from ground (along with R4) so that we can
  demonstrate _cutoff mode_
- R2 pulls down the collector voltage
- R3 is a backstop to prevent the circuit from shorting when the potentiometer
  resistance goes to zero
- R4 pulls up the emitter voltage from ground
- R5 is a 10 K&Omega; potentiometer to test the effect of changing
  V<sub>base</sub> on V<sub>emitter</sub>

With this circuit, we can directly measure the three voltages that govern the
behavior of our NPN transistor by tapping into the circuit at three places:

<div class="shortcode">
{{< figure src="2n2222-experiment-circuit-taps.png" link="2n2222-experiment-circuit.png" alt="Transistor and potentiometer test circuit diagram taps" >}}
</div>

and then taking measurements as the potentiometer is swept from zero resistance
to the full 10 K&Omega;.  Using a simple multimeter is probably the most
straightforward way to carry out this experiment:

<div class="shortcode">
{{< figure src="2n2222-experiment-circuit-multimeter.jpg" link="2n2222-experiment-circuit-multimeter.jpg" alt="Transistor and potentiometer test circuit implemented with a multimeter" >}}
</div>

In the above photo, the black clamp is attached to ground, and the red clamp is
attached to the collector of a 2N2222 transistor.

## Experimenting with the test circuit

By slowly turning the potentiometer and taking voltage measurements at the
collector, base, emitter, we can very clearly see what effect the voltage at
the base (V<sub>base</sub>) has on the emitter and collector.  The results are
as follows:

<div class="shortcode">
{{< figure src="2n2222-voltage-plot.png" link="2n2222-voltage-plot.png" alt="Voltage at the collector, base, and emitter as base is changed"  class="width-100" >}}
</div>

There is a ton of interesting data in this diagram.  Let's look at a few of
them.

### 1. Identifying the different transistor modes

Transistors can operate in one of three modes as discussed above:

Mode       | Criteria | Behavior
-----------|----------|---------
Saturation | V<sub>base</sub> &gt; V<sub>collector</sub><br>V<sub>base</sub> &gt; V<sub>emitter</sub> | Behaves like closed switch
Active     | V<sub>collector</sub> &gt; V<sub>base</sub> &gt; V<sub>emitter</sub> | V<sub>emitter</sub> proportional to V<sub>base</sub>
Cutoff     | V<sub>base</sub> &lt; V<sub>collector</sub><br>V<sub>base</sub> &lt; V<sub>emitter</sub> | Behaves like open switch

On our plot of measured data, these modes are laid out as shown:

<div class="shortcode">
{{< figure src="2n2222-voltage-plot-modes.png" link="2n2222-voltage-plot-modes.png" alt="Vbase, Vcollector, and Vemitter in different transistor modes"  class="width-100" >}}
</div>

And indeed, we can see that

- in <span style="color:#1b9e77; font-weight:bolder">cutoff mode</span>,
  the collector remains at a constant, high voltage while the emitter remains
  at a constant low voltage
- in <span style="color:#7570b3; font-weight:bolder">saturation mode</span>,
  the collector is at the _same_ voltage as the emitter and acts like a short
  circuit
- in <span style="color:#d95f02; font-weight:bolder">active mode</span>,
  the collector-emitter voltage difference decreases as the base voltage
  increases

### 2. Identifying the threshold voltage

One _practical_ aspect of how transistors work is the voltage range where it
_should_ be in active mode, but the transistor is still behaving as if it is in
cutoff mode--that is, V<sub>base</sub> &gt; V<sub>emitter</sub> but the
transistor is still actually not passing any current.  In our measured data,
this is happening between V<sub>base</sub> values of 0.6 V and 1.2 V:

<div class="shortcode">
{{< figure src="2n2222-voltage-plot-threshold.png" link="2n2222-voltage-plot-threshold.png" alt="Treshold voltage in the transistor active mode region"  class="width-100" >}}
</div>

I don't know that this region has a formal name, but let's call it the threshold
voltage.  It turns out that when the difference between V<sub>base</sub> and
V<sub>emitter</sub> is below this 0.6 V threshold voltage, the transistor
behaves as if it was still in cutoff mode.  This V<sub>BE</sub> &lt; 0.6 V
criteria is an intrinsic property of the transistor; even if
V<sub>collector</sub> is 5 V (or higher), this threshold of 0.6 V remains
constant.

This is a pretty critical property of bipolar junction transistors since any
source of resistance you put after the emitter will pull up V<sub>emitter</sub>
and therefore increase the V</sub>base</sub> you need to supply in order for
the transistor to start conducting.

## Automating the experiment on Raspberry Pi

There are two aspects to this experiment which are very tedious: (1) turning
the potentiometer to measure V<sub>collector</sub> and V<sub>emitter</sub> for
different V<sub>base</sub> values, and (2) clipping the voltmeter to different
leads and taking down measurements repeatedly.

With the Raspberry Pi's GPIO, a few simple integrated circuits, and a little
Python, it's actually quite simple to automate this entire experiment.
Specifically, we can replace

1. the **mechanical potentiometer** with a **digital potentiometer** such as the
   [MCP41010 digital potentiometer chip][]
2. the **digital multimeter** with a **analog-to-digital converter** such as
   the [MCP3008 analog-to-digital converter chip][]

### Digital Potentiometers

The digital potentiometer is a very simple IC that behaves exactly like a
regular (mechanical) potentiometer in that it has two terminals (usually
connected to a voltage source and ground) with a wiper terminal in between
(which outputs the variable voltage).  The MCP41010 that I use is pinned as
follows:

<div class="shortcode">
{{< figure src="mcp41010-pinout.png" link="mcp41010-pinout.png" alt="Pinout of the MCP41010 digital potentiometer chip" >}}
</div>

Pins 5, 6, and 7 are connected exactly the same way as the three pins on a
regular potentiometer, and V<sub>SS</dub> and V<sub>DD</sub> are connected to
ground and the 3.3 V source on the Raspberry Pi GPIO pins.

To program the MCP41010 (that is, to set the resistance you want it to have),
you send it 16-bit SPI packets not unlike I discuss on [my MAX7219 page][].
These packets have the format:

<div class="shortcode">
{{< figure src="mcp41010-packet.png" link="mcp41010-packet.png" alt="Depiction of the MCP4101 command packet" class="width-100" >}}
</div>

where

- **Command** is
    - `0001` to set a new resistance value
    - `0010` to put the chip in shutdown mode
- **Channel** determines which wiper to modify.  Since the MCP41010 has only one
  channel, this value should always be `0001`.
- **Value** is the 8-bit to use as the resistance.  Since my MCP41010 was a 10
  K&Omega; potentiometer,
    - `00000000` (0) = 0 ohms
    - `11111111` (255) = 10,000 ohms
    - `00010011` (19) = 19 / 255 &#215; 10,000 = 745 ohms

So for example, setting a resistance value of 745 ohms would involve

1. Pulling CS low to initiate a transmission
2. Pull MOSI low, then CLK high, then CLK low to send a zero (this is the most
   significant bit).  Repeat two times to send the first three bits of the
   Command packet (`000`)
3. Pull MOSI high, CLK high, CLK low to send the 4th bit of the Command packet
4. Continue to send the Channel portion, `0001`, as we did in steps #2 and #3
   above
5. Continue to send the value (`00010011`)
6. Pull CS back high to end transmission

After CS is raised high again, the wiper pin should demonstrate a resistance of
745 Ohms.

### Analog-to-Digital Converters

Analog-to-digital converters (ADCs) are essentially voltmeters that can report
what the voltage is between a sensor pin and a reference voltage.  The MCP3008
chip we'll use measures the voltage with reference to V<sub>SS</sub> (ground)
with 10 bits of accuracy, and it has eight channels that provide independent
sensor pins.

[Adafruit has a great tutorial on the MCP3008][Adafruit MCP3008 tutorial],
so rather than repeat it here, I'll just say that I also wrote a simple
[MCP3008 Python class][] (also built upon [my SPI class][]) that will take
readings off of the MCP3008's channels and return a voltage measurement.

### All-digital transistor test circuit

With the MCP3008 and MCP41010, it's quite simple to fully digitize this test
circuit.

<div class="shortcode">
{{< figure src="2n2222-experiment-circuit-rpi.jpg" link="2n2222-experiment-circuit-rpi.jpg" alt="Transistor and potentiometer digital test circuit" >}}
</div>

In the above photo, the MCP3008 ADC is in the top half of the breadboard, and
it has red/orange/yellow/green cables connecting it to the Raspberry Pi for
SPI on its right side.  On its left side are red/white/blue sensor cables that
connect to the 2N2222's emitter, base, and collector; the short orange cables
are just grounding the remaining un-used sensor pins.

The bottom half of the breadboard contains the MCP41010 digital potentiometer
instead of the blue rotary potentiometer, but is otherwise the same.  There are
a patch of new cables (blue/purple/grey/white) that connect to the Raspberry Pi
for SPI control of the MCP41010, and instead of red/black alligator clips, we
now have sensor cables that connect to the MCP3008.

Once this is all wired up, re-running our experiment is a rather straightforward
matter of

1. setting the digital potentiometer
2. reading the values off of each channel of the analog-digital converter

In Python and using my basic SPI library, it would look something like this:

<script src="https://gist.github.com/glennklockwood/15a2740cf5a83e1e281c278fa8128c2e.js"></script>

Not only is this _much_ faster than turning a potentiometer by hand and reading
off a voltmeter, it gives much more precise data:

<div class="shortcode">
{{< figure src="2n2222-voltage-plot-digital.png" link="2n2222-voltage-plot-digital.png" alt="Voltage at the collector, base, and emitter as base is changed, measured using digital means"  class="width-100" >}}
</div>

The above plot represents measurements for all 256 possible resistivities that
the MCP41010 can provide.  The linear relationship between the voltages is
clearly shown with very little noise in the data, showing that using an ADC and
digital potentiometer with Raspberry Pi is a very precise way to characterize
the behavior of transistors.

## Going forward

Combining a digital potentiometer and an analog-digital converter with Raspberry
Pi provides a pretty precise way of experimenting with transistors.  With a
little bit of Python, we were able to change the input going into what could've
been a black box, and could then measure its effect on other outputs.  While we
did this for a simple NPN transistor in this experiment, the same technique and
software can be used to examine more complicated circuits like logic gates and
pulse shaping circuits.

I wrote a very simple [MCP41010 Python class][], based on [my SPI class][],
that simplifies the process of setting resistance values for the MCP41010 chip.
I also wrote a [more sophisticated version of this transistor
test][transistor_experiment.py] to show how little code is really necessary to
get meaningful insight with an ADC, a digital potentiometer, and a Raspberry Pi.

[mk152 blog]: https://glennklockwood.blogspot.com/2016/10/learning-electronics-with-roulette.html
[sparkfun transistor page]: https://learn.sparkfun.com/tutorials/transistors#operation-modes
[MCP41010 digital potentiometer chip]: http://www.microchip.com/wwwproducts/en/en010494
[MCP3008 analog-to-digital converter chip]: https://www.adafruit.com/product/856
[Adafruit MCP3008 tutorial]: https://learn.adafruit.com/reading-a-analog-in-and-controlling-audio-volume-with-the-raspberry-pi/connecting-the-cobbler-to-a-mcp3008
[my MAX7219 page]: max7219.html#communicating-with-max7219cng-via-spi
[MCP41010 Python class]: https://github.com/glennklockwood/raspberrypi/blob/d5666c408a35a98eea373b32ef166d1acb4909c6/spi/mcp41010.py
[MCP3008 Python class]: https://github.com/glennklockwood/raspberrypi/blob/d5666c408a35a98eea373b32ef166d1acb4909c6/spi/mcp3008.py
[my SPI class]: https://github.com/glennklockwood/raspberrypi/blob/d5666c408a35a98eea373b32ef166d1acb4909c6/spi/spi.py
[transistor_experiment.py]: https://github.com/glennklockwood/raspberrypi/blob/aea32c162cbb37d0a413b328077bfdddf789c408/transistor_experiment.py
