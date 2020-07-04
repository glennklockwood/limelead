---
title: Programming the BMC2835 SOC
---

## Introduction

Raspberry Pi is a fully featured computer that can run Linux, but it is also an
embedded hardware platform with a feature-rich Broadcom BCM2835 system-on-a-chip
(SOC) with attached gadgets that can be programmed pretty easily without any
need to run Linux on it.

This page has my notes on manipulating the GPIO pins on a Raspberry Pi by
writing assembly directly to the Broadcom SOC rather than booting it into
Linux.  I started down this path by working through the
[Baking Pi OS Development][] tutorial online, but found it lacking a lot of the
details of what was actually happening.

## Prerequisites

I used a Raspberry Pi 4 as my development platform where I wrote code, compiled,
and flashed SD cards, and I used the BCM2835 SOC on a Raspberry Pi 1 model B+ as
the target of my code.

{{ figure("rpi-soc-testing-setup.jpg", alt="Raspberry Pi SOC Testing Setup") }}

The Raspberry Pi 1 model B+ on the left is the target, and the Raspberry Pi 4
on the right is where I did development.  The micro SD reader is required on the
development system because we'll be compiling code that needs to be copied to
the SD card that the target will load.

On the development platform, you must first install the ARM compiler toolchain
that allows you to compile directly to the Broadcom SOC:

    # apt install gcc-arm-none-eabi

I also used the "OS Template" mentioned in the [Baking Pi OS Development][] [OK01 module][]
to provide the appropriate Makefile and linker file.  My version of the
Makefile and source code is [on GitHub](https://github.com/glennklockwood/raspberrypi/tree/master/bmc2835).

## Turning on the LED

Raspberry Pi boards have an LED that's hard-wired to a GPIO pin that is an easy
way to show how to manipulate GPIO without needing to wire up a separate
breadboard.  The Baking Pi tutorial calls this the OK LED, but it's labeled
ACT on newer Raspberry Pis.  It's the green LED that normally blinks when
there's I/O activity when the board is booted to Linux:

{{ figure("rpi-soc-testing-leds.jpg", alt="ACT LED on Raspberry Pi", caption="The green ACT LED is what we will be manipulating.") }}

It turns out that this blink-on-activity behavior is not hard-coded anywhere;
it's a behavior programmed by Linux.  When there's no Linux, you are free to do
whatever you'd like with this LED, which is exactly what we will do.

## How to manipulate the LED conceptually

The ACT LED is hard-wired to GPIO pin 47 on the BCM2835 SOC.  Manipulating
whether it's on or off requires communicating with the BCM2835's GPIO
controller, which is documented in the [BCM2835 Datasheet][] starting on
page 89.  In many ways, programming this GPIO controller is just like
programming other little integrated circuits like the [HD44780 LCD Display][]
in that there is a set of registers it exposes to which you can write, and you
issue a combination of commands through these reigsters to cause the GPIO
controller to change its behavior.

{% call alert("info") %}
NOTE: The Baking Pi tutorial states that the ACT/OK LED is wired to GPIO pin 16
and must be cleared to turn on the LED, but that was only true for the original
Raspberry Pi.  All modern Raspberry Pis now have it wired to pin 47, so the
instructions below will operate on 47 and reflect the behavior in Raspberry Pi
1 model B+ and newer.
{% endcall %}

The [BCM2835 Datasheet][] describes exactly how this GPIO controller works; to
manipulate our ACT LED, we need to turn on GPIO 47.  This involves two steps:

1. Selecting the function of GPIO pin 47 to be an output pin
2. Modifying the state of GPIO pin 47 to reflect the output we want

Each step involves writing specific control sequences to specific registers on
the GPIO controller.

According to the datasheet, the GPIO controller exposes 42 registers, each 32
bits wide, that the ARM core sees as starting at memory address `0x20200000`.
It also describes that

1. Selecting the function of a GPIO pin involves manipulating the `GPFSEL`
   registers, and we need to issue the `001` command ("pin is an output") to
   the part of the correct `GPFSEL` register corresponding to pin 47.
2. Modifying the state of a GPIO pin involves manipulating the `GPCLR` and/or
   `GPSET` registers.  Specifically to turning on our LED, we need to use
   `GPSET` to make the LED turn on.

There are multiple `GPFSEL` and `GPSET` registers though, since each register is
only 32 bits but there are 54 GPIO pins that need to be controlled.  The datasheet 
indicates that the mapping of pins to registers for `GPFSEL` and `GPSET` are:

Register Number | Register Name | Description             | Controls pins
----------------|---------------|-------------------------|--------------------
Register 00     | GPFSEL0       | GPIO Function Select 0  | pins 0-9
Register 01     | GPFSEL1       | GPIO Function Select 1  | pins 10-19
Register 02     | GPFSEL2       | GPIO Function Select 2  | pins 20-29
Register 03     | GPFSEL3       | GPIO Function Select 3  | pins 30-39
Register 04     | GPFSEL4       | GPIO Function Select 4  | pins 40-49
Register 05     | GPFSEL5       | GPIO Function Select 5  | pins 50-54

and

Register Number | Register Name | Description             | Controls pins
----------------|---------------|-------------------------|--------------------
Register 10     | GPCLR0        | GPIO Pin Output Clear 0 | pins 0-31
Register 11     | GPCLR1        | GPIO Pin Output Clear 1 | pins 32-54

So to enable the LED, we need to

1. Write `001` to the offset within the 32-bit `GPFSEL4` register corresponding
   to the 8th pin (so pin 47, since `GPFSEL4` starts at pin 40) to designate
   the pin as an output pin, and
2. Flip the bit in `GPCLR1` register corresponding to pin 47.  Since `GPCLR1`
   controls pins 32-53, this will be the 16th bit in this reigster (the 1st 
   bit controls pin 32, so the 16th bit will control pin 47).


## How to manipulate the LED in practice

Now that we know what we must do conceptually, the rest is a matter of writing
some basic assembly code.  Our code has to start with some boilerplate:

```
.section .init
.globl _start
_start:
```

The GPIO controller's registers are mapped into the ARM core's memory at
`0x20200000`, so let's just store that in a register so we can reference its
registers relative to an offset:

```
ldr r0, =0x20200000
```

Now we're ready to begin fiddling with the GPIO controller registers.

### Step 1: Setting the GPIO pin function

To set the function of GPIO pin 47, we have to build the `001` command that
configures a GPIO pin as an output:

```
#!text
mov r1, #1
lsl r1, #21
str r1, [r0, #16]
```

These above lines do the following:

**Line 1** set the contents of register `r1` to be 1.  Since this is a 32-bit
(4-byte) register, it then looks like this:

```
MSB                             LSB
00000000 00000000 00000000 00000001
```

where MSB and LSB signify the most- and least-significant bits.

**Line 2** does a _logical shift left_ of `r1` by 21 bits.  Thus, `r1` then
contains:

```
MSB                             LSB
00000000 00100000 00000000 00000000
```

If you mentally overlay the bits of this register with our knowledge that this
register encodes a series of three-bit fields corresponding to GPIO pins 40-47
according to the datasheet, you see that

<pre>
MSB                             LSB
<span style="color:#888888">00</span>000<span style="color:red">000</span> 001<span style="color:red">000</span>00 0<span style="color:red">000</span>000<span style="color:red">0 00</span>000<span style="color: red">000</span>
 |  |  |   |  |                |  |
 |  |  |   |  |       ...      |  '- <span style="color: red">GPIO pin 40 (000)</span>
 |  |  |   |  |                '- GPIO pin 41 (000)
 |  |  |   |  '- <span style="color: red">GPIO pin 46 (000)</span>
 |  |  |   '- GPIO pin 47 (001)
 |  |  '- <span style="color:red">GPIO pin 48 (000)</span>
 |  '- GPIO pin 49 (000)
 '- <span style="color:#888888">Unused</span>
</pre>

We see that the three bits corresponding to Pin 47 is set to `001` and all other
pins are `000`.

**Line 3** stores the contents of `r1` (the above command code) into a memory
location given by the contents of `r0` + 16 bytes.  Recall that `r0` is the base
address for the GPIO controller's registers, and 16 bytes is the width of four
32-bit registers.  Here's a table adapated from the BCM2835 datasheet:

Register Number | Memory Address  | Register Name | Controls pins
----------------|-----------------|---------------|--------------
Register 00     | `r0` +  0 bytes | GPFSEL0       | pins 0-9
Register 01     | `r0` +  4 bytes | GPFSEL1       | pins 10-19
Register 02     | `r0` +  8 bytes | GPFSEL2       | pins 20-29
Register 03     | `r0` + 12 bytes | GPFSEL3       | pins 30-39
Register 04     | `r0` + 16 bytes | GPFSEL4       | pins 40-49
Register 05     | `r0` + 20 bytes | GPFSEL5       | pins 50-54

So, given the base address at `r0` is our `GPFSEL0` register,
`r0` + 16 bytes puts us at the `GPFSEL4` register which controls pins 40-49,
and our command code modifies the 8th pin in that register (pin 47).

### Step 2: Modifying the state of the GPIO pin

Next we want to issue the `GPSET` command by flipping a bit in the appropriate
`GPSET` register.  Whereas `GPFSEL` registers represents each pin's
function configuration using three bits, `GPSET` (and `GPCLR`) only use one bit
for each pin.  Thus, `GPSET0` lets you set a pin high (`1`) for pins 0-31, and
`GPSET1` does the same for pins 32-53.  Since we want to turn on pin 47, we
need to just flip the 15th bit (recall: the 0th bit corresponds to pin 32) in
the `GPSET1` register.

So, we do that using the following assembly:

```
#!text
mov r1, #1
lsl r1, #15
str r1, [r0, #44]
```

This is very similar to the code we used to manipulate the `GPFSEL` register.

**Line 1** sets the contents of register `r1` to

```
MSB                             LSB
00000000 00000000 00000000 00000001 
```

**Line 2** does a _logical shift left_ by 15 bits, giving us

```
MSB                             LSB
00000000 00000000 10000000 00000000 
                |        |        |
17th bit -------'        |        |
(GPIO pin 48)            |        |
                         |        |
9th bit (GPIO pin 40) ---'        |
1st bit (GPIO pin 32) ------------'
```

We can now see that the 15th bit is 1 while all others are 0, causing pin 47 to
be set while pins 32-46 and 48-53 are left unmodified.

**Line 3** then writes this state into the register that is offset by 32 bytes
from the base register `r0`.  Consulting our handy table adapted from the
datasheet,

Register Number | Memory Address  | Register Name | Controls pins
----------------|-----------------|---------------|--------------
Register 07     | `r0` + 28 bytes | GPSET0        | pins 0-31
Register 08     | `r0` + 32 bytes | GPSET1        | pins 32-53

### Keeping the SOC looping

At the end of its instruction stream, the SOC will have nothing to do and halt.
Since we want our LED to stay on in perpetuity (or at least until we unplug the
Raspberry Pi), we just need to add an infinite loop at the end of our code:

```text
loop$:
b loop$
```

This simply creates a label (`loop$`) and then branches (`b`) to it and repeating.


## Loading the code into the SOC

The overall code looks like this:

```
#!text
.section .init
.globl _start
_start:

ldr r0, =0x20200000 /* store base offset address in r0 */

mov r1, #1          /* r1 = 00000000 00000000 00000000 00000001 */
lsl r1, #21         /* r1 = 00000000 00100000 00000000 00000000 */
str r1, [r0, #16]   /* write contents of r1 into address given by r0 + 16 (GPFSEL4) */

mov r1, #1          /* r1 = 00000000 00000000 00000000 00000001 */
lsl r1, #15         /* r1 = 00000000 00000000 10000000 00000000 */
str r1, [r0, #32]   /* write contents of r1 into address given by r0 + 32 (GPSET1) */

loop$:
b loop$ /* loop infinitely */
```

We then compile it using our embedded ARM toolchain.  Assuming this source is in
`main.s` and we have the [`kernel.ld` linker script](https://github.com/glennklockwood/raspberrypi/blob/7b04fb9d975cb631627b6aaa939fa9fc8521d8c2/bmc2835/kernel.ld)
provided by the [Baking Pi OS Development][] build setup, building our code is
just three commands:

```
arm-none-eabi-as main.s -o main.o
arm-none-eabi-ld --no-undefined main.o -o output.elf -T kernel.ld
arm-none-eabi-objcopy output.elf -O binary kernel.img
```

This results in a file called `kernel.img` which is a magical file to the
BMC2835 SOC.  Copy this file into the boot partition of an SD card that's
formatted to load Raspberry Pi OS, plug that SD card into the Raspberry Pi,
and connect the Raspberry Pi to power.

Once the Raspberry Pi gets power, it goes through the following process to
execute user code:

1. The BMC2835 SOC (specifically, the VideoCore IV GPU in it) loads the _stage 1_ boot loader from an on-chip ROM
2. The _stage 1_ loader knows how to talk to the SD card controller and read FAT16/FAT32 file systems.  It looks for a file called `bootcode.bin` on the first partition of the SD card, and loads it.  `bootcode.bin` is the _stage 2_ boot loader.
3. The _stage 2_ loader loads `start.elf` from the SD card's first partition.  This is the _stage 3_ boot loader.
4. The _stage 3_ loader then
    1. reads `config.txt` which acts a bit like a BIOS configuration
    2. configures the GPU and ARM processor
    3. loads `kernel.img` and releases the ARM processor to begin executing it

So, by swapping the `kernel.img` provided by Raspberry Pi OS with your own
binary, the ARM processor executes the code we just wrote instead of the
Linux kernel.  This whole process is analogous to flashing new code on to
a microcontroller-based board such as Arduino; instead of using a special
USB-based programmer though, you get to copy your image as a regular file into
a FAT file system on a removable SD card that the BMC2835 knows how to read and
load.

## Blinking the LED

The [OK02 module][] of the [Baking Pi OS Development][] course explains how to make
the ACT LED blink instead of just turn on and stay on; this is the true hello
world of electronics, so let's work through it.

Conceptually, we are adding a few more steps on to the code we wrote in the
previous section:

1. Selecting the function of GPIO pin 47 to be an output pin (same as before)
2. Modifying the state of GPIO pin 47 to reflect the output we want (same as before)
3. Waiting some amount of time
4. Modifying the state of GPIO pin 47 to reflect a new output state we want
5. Waiting some amount of time
6. Going back to step 2

We already know how to modify the state of GPIO pins using the `GPSET` register,
and the `GPCLR` register works in exactly the same way except that it unsets
GPIO pins instead of setting them.  We also know how to establish an infinite
loop, so the only thing we don't know how to do is waste some amount of time.

Per the [OK02 module][], we can waste time by doing some simple math:

```
#!text
mov r2, #0x3F0000
wait1$:
sub r2, #1
cmp r2, #0
bne wait1$
```

1. Line 1 puts a big number (0x3F0000, or 4,128,768) into register `r2`
2. Line 2 labels the start of a loop `wait1$`
3. Line 3 subtracts from `r2` the value 1
4. Line 4 compares the contents of `r2` to the value 0.  The result of this comparison is implicitly stored in the _current processor status register_.
5. Line 5 `b`ranches to label `wait1$` if the contents of the _current processor
   status register_ is `ne` (not equal).  Since the _current processor status
   register_ was just populated by `comp r2, #0`, this means that we will go to
   `wait1$` if `r2` is not equal to 0.

So this loop just repeats 4,128,768 times before not repeating.  The exact time
it takes for this loop to repeat that many times is a function of the clock
frequency of the ARM core, which is nominally 700 MHz in our Raspberry Pi.

Incorporating this into a fully functional program, we can start with the same
code as we had previously.  Rather than have our infinite loop be empty though,
we want to manipulate `GPSET`, waste some time, manipulate `GPCLR`, and waste
more time inside our `loop$` body.  Here's what I came up with:

```
#!text
.section .init
.globl _start
_start:

ldr r0, =0x20200000 /* store base offset address in r0 */

mov r1, #1          /* r1 = 00000000 00000000 00000000 00000001 */
lsl r1, #21         /* r1 = 00000000 00100000 00000000 00000000 */
str r1, [r0, #16]   /* write contents of r1 into address given by r0 + 16 (GPFSEL4) */

loop$:

mov r1, #1          /* r1 = 00000000 00000000 00000000 00000001 */
lsl r1, #15         /* r1 = 00000000 00000000 10000000 00000000 */
str r1, [r0, #32]   /* write contents of r1 into address given by r0 + 32 (GPSET1) */

mov r2, #0x3F0000
wait1$:
sub r2, #1
cmp r2, #0
bne wait1$

mov r1, #1          /* r1 = 00000000 00000000 00000000 00000001 */
lsl r1, #15         /* r1 = 00000000 00000000 10000000 00000000 */
str r1, [r0, #44]   /* write contents of r1 into address given by r0 + 44 (GPCLR1) */

mov r2, #0x3F0000
wait2$:
sub r2, #1
cmp r2, #0
bne wait2$

b loop$             /* loop infinitely */
```

- Lines 1-9 are the same as before
- Lines 13-15 set GPIO pin 47 (turn LED on), the same as before
- Lines 17-21 waste time
- Lines 23-25 clear GPIO pin 47 (turn LED off).  The syntax for manipulating
  these `GPCLR` registers is identical to that of the `GPSET` registers; `GPCLR`
  just does the inverse operation on the designated GPIO pin(s).
- Lines 27-31 waste more time
- Line 33 goes back up to line 11, where the LED is turned back on again.

Once you compile this code and load the resulting `kernel.img` on to the SD card
and the BMC2835 loads it, you should get a blinking ACT light:

{{ figure("rpi-soc-testing-blink.gif", alt="Blinking ACT LED on Raspberry Pi") }}

[Baking Pi OS Development]: https://www.cl.cam.ac.uk/projects/raspberrypi/tutorials/os/index.html
[BCM2835 Datasheet]: https://www.raspberrypi.org/documentation/hardware/raspberrypi/bcm2835/BCM2835-ARM-Peripherals.pdf
[HD44780 LCD Display]: {filename}hd44780-lcd-display.md
[OK01 module]: https://www.cl.cam.ac.uk/projects/raspberrypi/tutorials/os/ok01.html
[OK02 module]: https://www.cl.cam.ac.uk/projects/raspberrypi/tutorials/os/ok02.html
