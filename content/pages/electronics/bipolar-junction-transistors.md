---
date: "2016-10-24T20:45:00-07:00"
draft: false
last_mod: "October 24, 2016"
title: "Understanding bipolar junction transistors"
shortTitle: "Understanding bipolar junction transistors"
parentdirs: [ "electronics" ]
---

## Contents

- [Introduction](#introduction)
- [Building a test circuit](#building-a-test-circuit)
- [Experimenting with the test circuit](#experimenting-with-the-test-circuit)
    - [Identifying the different transistor modes](#1-identifying-the-different-transistor-modes)
    - [Identifying the threshold voltage](#2-identifying-the-threshold-voltage)
- [Characterizing PNP transistors](#characterizing-pnp-transistors)
- [Next steps](#next-steps)

## Introduction

Transistors are a fundamental component in digital electronics from which we
can build circuits that can perform logic.  At their core, they act like
on/off switches that can be manipulated electrically, and although this is a
simple concept, I had a hard time understanding exactly _how_ they worked in
the real world.  For example, in [a blog post I wrote about understanding a
roulette wheel kit][mk152 blog], I could not figure what a transistor would be
doing as resistor-capacitor series were in the process of charging; how close to
being fully charged would the capacitor be before the gate switched on?

A lot of websites explain what NPN transistors accomplish and how the collector,
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
me understand how I could use these transistors in actual circuits.  So for the
sake of developing my own understanding of transistors (specifically, bipolar
junction transistors, or BJTs), I set up some tests to characterize the behavior
of a [2N2222 NPN transistor][].

## Building a test circuit

To get a hands-on understanding of what these modes look like in practice, I
built a circuit with a 10K potentiometer plugged into the base so that I could
see at what point the transistor started conducting:

<div class="shortcode">
{{< figure src="2n2222-experiment-circuit.png" link="2n2222-experiment-circuit.png" alt="Transistor and potentiometer test circuit diagram" >}}
</div>

where

- `R1` pulls up the emitter voltage from ground (along with `R4`) so that we can
  demonstrate _cutoff mode_
- `R2` pulls down the collector voltage
- `R3` is a backstop to prevent the circuit from shorting when the potentiometer
  resistance goes to zero
- `R4` pulls up the emitter voltage from ground
- `R5` is a 10 K&Omega; potentiometer to test the effect of changing
  V<sub>base</sub> on V<sub>emitter</sub>

With this circuit, we can directly measure the three voltages that govern the
behavior of our NPN transistor by tapping into the circuit at three places:

<div class="shortcode">
{{< figure src="2n2222-experiment-circuit-taps.png" link="2n2222-experiment-circuit.png" alt="Transistor and potentiometer test circuit diagram taps" >}}
</div>

and then taking measurements as the potentiometer is swept from zero resistance
to the full 10 K&Omega;.  Using a simple multimeter is the most straightforward
way to carry out this experiment, if a bit tedious:

<div class="shortcode">
{{< figure src="2n2222-experiment-circuit-multimeter.jpg" link="2n2222-experiment-circuit-multimeter.jpg" alt="Transistor and potentiometer test circuit implemented with a multimeter" >}}
</div>

In the above photo, the black clamp is attached to ground, and the red clamp is
attached to the collector.

## Experimenting with the test circuit

By slowly turning the potentiometer and taking voltage measurements at the
collector, base, emitter, we can very clearly see what effect the voltage at
the base (V<sub>base</sub>) has on the emitter and collector.  Dialing in the
potentiometer to set V<sub>base</sub> to values ranging from 0 to 3.3 V in 0.1 V
and measuring the other voltages gives us the following:

<div class="shortcode">
{{< figure src="2n2222-voltage-plot.png" link="2n2222-voltage-plot.png" alt="Voltage at the collector, base, and emitter as base is changed" >}}
</div>

There is a lot of interesting data in this diagram, so let's look at a few
things it tells us about NPN transistors.

### 1. Identifying the different transistor modes

As discussed above, NPN transistors can operate in one of three modes:

Mode       | Criteria | Behavior
-----------|----------|---------
Saturation | V<sub>base</sub> &gt; V<sub>collector</sub><br>V<sub>base</sub> &gt; V<sub>emitter</sub> | Behaves like closed switch
Active     | V<sub>collector</sub> &gt; V<sub>base</sub> &gt; V<sub>emitter</sub> | V<sub>emitter</sub> proportional to V<sub>base</sub>
Cutoff     | V<sub>base</sub> &lt; V<sub>collector</sub><br>V<sub>base</sub> &lt; V<sub>emitter</sub> | Behaves like open switch

On our plot of measured data, these modes are laid out as shown:

<div class="shortcode">
{{< figure src="2n2222-voltage-plot-modes.png" link="2n2222-voltage-plot-modes.png" alt="Vbase, Vcollector, and Vemitter in different transistor modes" class="width-100" >}}
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

The behavior in all three regions is remarkably linear; as V<sub>base</sub> is
increased, the resulting change in the other two voltages is directly
proportional.  This is conveniently simple, because other digital componentry
(like RC series) do _not_ have simple linear behavior; it is good to know that
an NPN transistor does not further complicate that by introducing other
nonlinear behavior.

### 2. Identifying the cut-in voltage

One _practical_ aspect of how transistors work is the voltage range where it
_should_ be in active mode, but the transistor is still behaving as if it is in
cutoff mode--that is, V<sub>base</sub> &gt; V<sub>emitter</sub> but the
transistor is still actually not passing any current.  In our measured data,
this is happening between V<sub>base</sub> values of 0.6 V and 1.2 V:

<div class="shortcode">
{{< figure src="2n2222-voltage-plot-threshold.png" link="2n2222-voltage-plot-threshold.png" alt="Treshold voltage in the transistor active mode region" >}}
</div>

This minimum voltage to get any conductivity is called the _cut-in voltage_.
It turns out that when the difference between V<sub>base</sub> and
V<sub>emitter</sub> is below this 0.6 V cut-in voltage, the transistor
behaves as if it was still in cutoff mode.  This V<sub>BE</sub> &lt; 0.6 V
criteria is an intrinsic property of the transistor; even if
V<sub>collector</sub> is 5 V (or higher), this threshold of 0.6 V remains
constant.

This is a critical property of bipolar junction transistors since any source of
resistance you put after the emitter will pull up V<sub>emitter</sub> and
therefore increase the V</sub>base</sub> you need to supply in order for the
transistor to start conducting.  For example, attaching an LED to the emitter
in a 3.3 V circuit might not always work as desired--you've only got 0.7 V to
play with ahead of the collector after the 2.0 V drop from the LED and this
0.6 V cut-in voltage.

## Characterizing PNP transistors

PNP transistors can operate in one of three modes:

Mode       | Criteria | Behavior
-----------|----------|---------
Saturation | V<sub>base</sub> &lt; V<sub>collector</sub><br>V<sub>base</sub> &lt; V<sub>emitter</sub> | Behaves like closed switch
Active     | V<sub>emitter</sub> &gt; V<sub>base</sub> &gt; V<sub>collector</sub> | V<sub>emitter</sub> proportional to V<sub>base</sub>
Cutoff     | V<sub>base</sub> &gt; V<sub>collector</sub><br>V<sub>base</sub> &gt; V<sub>emitter</sub> | Behaves like open switch

which, when compared to the table for NPN transistors, represents almost the
entire opposite of NPN modes.  And if we plug a PNP resistor (like a 2N2907)
into our test circuit as-is and run the experiment, we get very strange results:

<div class="shortcode">
{{< figure src="2n2907-voltage-plot-naive.png" link="2n2907-voltage-plot-naive.png" alt="Voltage at the collector, base, and emitter as base is changed on a PNP transistor" >}}
</div>

According to the above table, just about all values of V<sub>base</sub> we
tested is occurring in a fourth mode which is called **reverse-active mode**,
where V<sub>emitter</sub> &lt; V<sub>base</sub> &lt; V<sub>collector</sub>.
This happens because the _current flows from the emitter to the collector_ in PNP
transistors; we've just run our PNP transistor backwards!

To apply the experimentation technique that we used to characterize NPN
transistors on PNP transistors, there there are a few changes we should make to
our test circuit:

1. We have to replace the NPN 2N2222 with a PNP 2N2907 and _reverse the
   polarity_ so that the emitter is at a higher voltage than the collector.
2. `R1` should be connected _after_ `R2` now.  In our NPN test circuit, `R1`'s
   job was to pull up the voltage on the low side of the transistor so that we
   could observe cutoff mode where V<sub>base</sub> was lower than
   V<sub>emitter</sub>.  In this PNP test circuit, cutoff mode will be observed
   when V<sub>base</sub> is higher than V<sub>emitter</sub>, so moving `R1` will
   pull down V<sub>emitter</sub> from our +3.3 V source.
3. `R2` should be replaced with a lower resistance so that we can observe
   saturation mode.  In the NPN test circuit, `R2`'s job was to pull
   V<sub>collector</sub> down below V<sub>base</sub>, where V<sub>base</sub>
   was governed (in part) by `R3`.  Saturation mode in this PNP case requires
   that V<sub>emitter</sub> be _higher_ than V<sub>base</sub> (again, governed
   in part by `R3`), so `R2` should not be larger than `R3`.

Applying these three changes results in a circuit that looks like this:

<div class="shortcode">
{{< figure src="2n2907-experiment-circuit-taps.png" link="2n2907-experiment-circuit-taps.png" alt="Transistor and potentiometer test circuit diagram for PNP transistor" >}}
</div>

Note that because the emitter and collector are physically reversed, we must
take care not to forget which transistor lead we are measuring with our
multimeter!

This PNP transistor test circuit demonstrates the following relationships
between V<sub>collector</sub>, V<sub>base</sub>, and V<sub>emitter</sub>:

<div class="shortcode">
{{< figure src="2n2907-voltage-plot.png" link="2n2907-voltage-plot.png" alt="Voltage at the collector, base, and emitter as base is changed on a PNP transistor" >}}
</div>

At a glance, this may look quite different from the NPN transistor voltage plot
from the previous section.  However, if you look at it upside down, you may be
able to see how similar PNP and NPN transistors are.  All of the same modes
are present, as is the cut-in voltage:

<div class="shortcode">
{{< figure src="2n2907-voltage-plot-modes.png" link="2n2907-voltage-plot-modes.png" alt="Voltage at the collector, base, and emitter as base is changed on a PNP transistor" class="width-100" >}}
</div>

The only difference, as any textbook will tell you, is that PNP transistors
are "on" when the base voltage is low.

## Next steps

These experiments are elucidating, but they are also very tedious to carry out
with a mechanical potentiometer and a handheld multimeter.  To perform this
sort of characterization on more elaborate circuits such as logic gates, we
need a more efficient way of varying voltage and taking measurements.  To this
end, I've written on a page on [how to use a digital potentiometer (digipot)
and an analog-digital converter (ADC) along with Raspberry Pi to automate these
experiments][my digipot page].

[mk152 blog]: https://glennklockwood.blogspot.com/2016/10/learning-electronics-with-roulette.html
[sparkfun transistor page]: https://learn.sparkfun.com/tutorials/transistors#operation-modes
[2N2222 NPN transistor]: https://en.wikipedia.org/wiki/2N2222
[my digipot page]: digipots.html
