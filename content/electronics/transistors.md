---
date: "2016-10-24T20:45:00-07:00"
draft: false
last_mod: "October 24, 2016"
title: "Experimenting with transistors and Raspberry Pi"
shortTitle: "Experimenting with transistors"
parentdirs: [ "electronics" ]
---

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

- *saturation mode* happens when the voltage at the base (with respect to
  ground; V<sub>base</sub>) is higher than both the voltage at the emitter
  and collector (again, with respect to ground; V<sub>emitter</sub> and
  V<sub>collector</sub>)
- *active mode* happens when the base voltage (V<sub>base</sub>) is higher
  than the emitter V<sub>emitter</sub> but lower than the collector
  V<sub>collector</sub>
- *cutoff mode* happens when the base voltage (V<sub>base</sub>) is lower than
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
straightforward way to carry out this experiment, but I thought it would be
more fun to use a Raspberry Pi and an MCP3008 analog-digital converter chip.

<div class="shortcode">
{{< figure src="2n2222-experiment-circuit-rpi.jpg" link="2n2222-experiment-circuit-rpi.jpg" alt="Transistor and potentiometer test circuit implemented in Raspberry Pi" >}}
</div>

In the above photo, the red, white, and blue jumper cables are taps that feed
into pins 1-3 (channels 1-3) on the MCP3008 ADC, and they are connected to the
2N2222 collector, base, and emitter, respectively.

### Experimenting with the test circuit

Knowing that the input voltage from the Raspberry Pi is 3.3 volts, it's easy
to take voltage measurements as the potentiometer is swept.  I used my [MCP3008
polling script][poll_mcp3008.py] to print out V<sub>base</sub>,
V<sub>collector</sub>, and V<sub>emitter</sub> every second, and then slowly
turned the potentiometer.  The results are as follows:

<div class="shortcode">
{{< figure src="2n2222-voltage-plot.png" link="2n2222-voltage-plot.png" alt="Voltage at the collector, base, and emitter as base is changed"  class="width-100" >}}
</div>

There is a ton of interesting data in this diagram.  Let's look at a few of
them.

### 1. Identifying the different transistor modes


[mk152 blog]: https://glennklockwood.blogspot.com/2016/10/learning-electronics-with-roulette.html
[sparkfun transistor page]: https://learn.sparkfun.com/tutorials/transistors#operation-modes
[poll_mcp3008.py]: https://github.com/glennklockwood/raspberrypi/blob/89cb8fb3240d475dde438f0509467932628a7734/poll_mcp3008.py
