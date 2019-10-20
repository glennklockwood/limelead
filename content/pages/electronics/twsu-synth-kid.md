---
date: "2017-10-15T19:14:00-07:00"
draft: false
last_mod: "October 15, 2017"
title: "Understanding the TWSU Synth Kit"
shortTitle: "TWSU Synth Kit"
parentdirs: [ "electronics" ]
---

<div class="shortcode">
{{% alertbox warning %}}
This page is still a work in progress.
{{% /alertbox %}}
</div>

I received an [electronic synth kit developed by Technology Will Save
Us][twsu kit] as a gift.  It comes in very nice packaging and has enough
components to build three slightly different electronics projects, all
centered around an NE556 timer chip and an analog speaker.

<div class="shortcode">
{{< figure src="twsu-synth-kit.jpg" link="twsu-synth-kit.jpg" alt="TWSU Synth Kit" >}}
</div>

Unfortunately, the kit itself doesn't come with any printed instructions--you've
got to go to [a website whose URL is included in the box][insert url] and click
through a [rather clunky web interface][twsu manual] to figure out what to do
with all of the components.  The instructions themselves are quite frustrating
in that they only serve to explain how to plug the components together--not
why these parts are being connected in the way that they are, or what each
component is doing.  No mention is made of what role the integrated circuit
chip plays (the answer: it's two 555 timers in a single package and converts
the RC series into fixed-frequency digital signals) and doesn't even mention
it by name (it's an NE556), so for all intents and purposes, this kit presents
itself to learners as a black box.  Not very helpful.

The final major flaw in this kit that really irked me was a notable absence of
any circuit diagrams.  Perhaps I've been spoiled by [comparable yet cheaper and
thoroughly documented kits][velleman kit], but I couldn't wrap my head around
what these synth projects were doing until I sat down and constructed circuit
diagrams of each build.

## Stutter Synth

I haven't quite figured this one out yet, but here is what I gathered the
circuit diagram looks like based on the circuit board layout.

<div class="shortcode">
{{< figure src="twsu-stutter-synth.jpg" link="twsu-stutter-synth.jpg" alt="TWSU stutter synth diagram" >}}
</div>

## Atari Punk Console

It turns out this circuit is quite famous, so much so that [it has its own
Wikipedia page][atari punk console wikipedia].  Here is the circuit as I
understand it.

<div class="shortcode">
{{< figure src="twsu-atari-punk-console.jpg" link="twsu-atari-punk-console.jpg" alt="TWSU Atari punk console diagram" >}}
</div>

The rest of the Internet can explain this circuit better than me, and there are
two resources I particularly liked:

- [An explanation of how the Atari Punk Console works by Forrest Mimms][forrest mimms atari punk console explanation],
  inventor of the circuit
- [A video of Collin Cunningham explaining the basics of the Atari Punk Console][collin cunningham atari punk console explanation]
  and building a project enclosure for it

## Dub Siren Synth

I don't really get this circuit either.

<div class="shortcode">
{{< figure src="twsu-dub-siren-synth.jpg" link="twsu-dub-siren-synth.jpg" alt="TWSU siren synth diagram" >}}
</div>

Apparently "[dub sirens][]" are a thing, but I couldn't really tell what this
was supposed to sound like.

[twsu kit]: https://www.techwillsaveus.com/shop/synth-kit/
[insert url]: https://make.techwillsaveus.com/synth-kit/?utm_source=Insert
[twsu manual]: https://make.techwillsaveus.com/synth-kit/manual/
[velleman kit]: https://www.vellemanusa.com/products/view/?id=350680
[atari punk console wikipedia]: https://en.wikipedia.org/wiki/Atari_Punk_Console
[forrest mimms atari punk console explanation]: https://en.wikipedia.org/wiki/Atari_Punk_Console
[collin cunningham atari punk console explanation]: https://www.youtube.com/watch?v=jzs2Zo_mc4c
[dub sirens]: https://en.wikipedia.org/wiki/Dub_siren
