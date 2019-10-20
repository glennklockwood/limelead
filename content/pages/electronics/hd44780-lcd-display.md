---
title: Programming the HD44780 LCD Display with Raspberry Pi
shortTitle: Programming HD44780 LCD Display
---

## Introduction

The HD44780 is a chip that drives simple 16x2 LCD character displays.

{{ figure("hd44780.gif", alt="HD44780 in action") }}

They are extremely inexpensive, and a fully integrated [HD44780 and LCD display
can be purchased for under $4][oddwires page].  They provide an 8-bit parallel
interface to the outside world which is used to both issue configuration
commands and program the display registers, and there appears to be pretty good
drivers for Arduino out there.

However there is much less information available on how to program these
displays with Raspberry Pi, and although [Adafruit provides an HD44780 driver
for Raspberry Pi][adafruit driver], it is not thoroughly documented.  [The
datasheet][] is also a bit opaque, and there are a couple of subtleties that
are not clearly documented anywhere; as a result, I struggled a bit in figuring
out exactly how to make this display work.

I did ultimately sort through all the issues, and what follows are some of the
notes I took while getting there.

## Basic physical interface

The HD44780 display that I bought and used has sixteen interface pins; five
provide power, ground, and contrast control, and eleven are used to program
the device:

{{ figure("hd44780-wiring.jpg", alt="HD44780 wiring example") }}

There are plenty of wiring guides around (e.g., the [Adafruit Character LCD
guide][]) which are mostly complete.  However, there are a few additional points
to make:

**The `E` (or `EN`) pin is _extremely_ sensitive to outside interference.**  I
had to install a bypass capacitor between the `EN` pin and ground to suppress
spurious command signals that were triggered as I waved my hand near some of
my breadboard wires.  I used a 10 &mu;F capacitor out of convenience, but
a smaller capacitance is probably better since it will allow you to issue
commands to the HD44780 controller at a higher frequency.  My bypass capacitor
is visible in the above photo.

**If you want to use the 8-bit command interface** (using eight GPIO pins
instead of four), just wire `D0` through `D3` to additional GPIO ports.  The
8-bit interface is conceptually simpler and is very convenient if you attach
an 8-bit shift register to the display.

## Basic command structure

The HD44780 provides a parallel I/O interface where pins `D0` - `D7`, `RW`, and
`RS` are set either high or low, and a clock pulse is set to the `EN` pin to
tell the controller to read the state of all pins and act on them.  The most
important pins are

- `RS`, which indicates if you are sending a command (0) or updating the display
  (1)
- `RW`, which indicates if you want to use `D0`-`D7` to write (0) or read (1).
  Most guides just keep this pin grounded (always write, never read) but you
  can use the memory on the display controller to write and read arbitrary
  data if you want.
- `D0`-`D7` are used to encode the command you wish to issue to the controller
- `E` (or `EN`) is used to tell the controller to either read the state of the
  aforementioned pins and act (when `RS` is low), or populate them with the
  state saved on the controller (when `RS` is high)

The controller takes time to actually process commands whenever `EN` is pulsed,
so **pulsing `EN` too quickly can cause major problems**.  It follows that
commands should not be issued less than a millisecond apart--or longer, if
you are using a high-capacitance bypass capacitor.

The HD44780 controller supports both an 8-bit interface, where all eight `D`
pins are used simultaneously to issue an 8-bit command, as well as a 4-bit
interface, where only pins `D4`-`D7` are used, and an additional pulse of `EN`
is used to send the four most significant bits of the 8-bit command separately
from the four least significant bits.

When operating in 4-bit mode, the process to issue a command is

1. Set `RS` to high (which means we want to display the data we are sending over
   the `D` pins) or low (we are sending a command to the chip)
2. Set `D4`, `D5`, `D6`, `D7` to the 4th, 3rd, 2nd, and 1st most significant
   bits
3. Pulse the `EN` pin by setting it low, high, then low
4. Set the `D4`, `D5`, `D6`, and `D7` to the least significant bit, 2nd least,
   3rd, and 4th
5. Pulse the `EN` pin

Programmatically, a function that issues a command might look like

    :::python
    def write8_4bitmode(command, rs_value):
        GPIO.output(PIN_RS, rs_value)

        time.sleep(1e-3)

        GPIO.output(PIN_D[4], GPIO.HIGH if ((command >> 4) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[5], GPIO.HIGH if ((command >> 5) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[6], GPIO.HIGH if ((command >> 6) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[7], GPIO.HIGH if ((command >> 7) & 1) > 0 else GPIO.LOW)
        clock_pulse()

        GPIO.output(PIN_D[4], GPIO.HIGH if ((command >> 0) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[5], GPIO.HIGH if ((command >> 1) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[6], GPIO.HIGH if ((command >> 2) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[7], GPIO.HIGH if ((command >> 3) & 1) > 0 else GPIO.LOW)
        clock_pulse()

Pulsing the clock (`EN`) is not entirely straightforward, because the `EN` pin
is triggered by a rising edge, but cannot be pulsed too quickly since the
command it triggers takes dozens of microseconds to complete.  The process
looks like

1. Pull `EN` low
2. Waiting a microsecond (> 450 ns); may need to be longer depending on your
   bypass capacitor's capacitance
3. Pull `EN` high
4. Waiting a microsecond (> 450 ns)
5. Pull `EN` low
6. Wait 37 microsecond; commands can take 37 &mu;s to execute, per Table 6
   in [the datasheet][]

The `clock_pulse()` function may look something like

    :::python
    def pulse_clock(delay=1e-3):
        time.sleep(delay)
        GPIO.output(PIN_EN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(PIN_EN, GPIO.LOW)
        time.sleep(delay)

where the `delay` is critical to ensure that successive commands are not lost
due to excessively high frequency.

When using 8-bit mode and pins `D0`-`D7` are all wired, the command sequence
is a little simpler.  The corresponding code would look like

    :::python
    def write8_8bitmode(command, rs_value):
        GPIO.output(PIN_RS, rs_value)

        time.sleep(1e-3)

        GPIO.output(PIN_D[0], GPIO.HIGH if ((command >> 0) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[1], GPIO.HIGH if ((command >> 1) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[2], GPIO.HIGH if ((command >> 2) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[3], GPIO.HIGH if ((command >> 3) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[4], GPIO.HIGH if ((command >> 4) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[5], GPIO.HIGH if ((command >> 5) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[6], GPIO.HIGH if ((command >> 6) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[7], GPIO.HIGH if ((command >> 7) & 1) > 0 else GPIO.LOW)
        pulse_clock()

## Initialization

The chip must be initialized into either 4-bit or 8-bit mode before it will
receive any commands.  The chip will auto-initialize into 4-bit mode when it is
powered by up to 5 V, but if you are using 3.3 V _or_ if you need to switch from
4-bit to 8-bit modes after the initial power-up, you will have to
(re-)initialize the chip manually.

At a high level, initializing the chip is described in Figures 23 and 24 in
[the datasheet][] and involves five steps:

1. Issuing the magical reset sequence, which includes declaring whether you will
   use either the 4-bit or 8-bit command interface
2. Configuring the "function set" options
3. Configuring the "display on/off control" options
4. Clearing the display
5. Configuring the "entry mode set" options

Although not documented, steps #3, #4, and #5 are not strictly required,
although they do explicitly define behavior that may otherwise cause your chip
and display to behave unpredictably.  In addition, steps #3 to #5 can be
executed in any order.

An example of the code that would initialize the chip in 4-bit mode would look
like this:

    :::python
    def init_4bitmode():
        ### initialization magic sequence
        write4(int("0011", 2))
        write4(int("0011", 2))
        write4(int("0011", 2))
        write4(int("0010", 2))

        ### send the "function set" command to configure display dimensions
        write8_4bitmode(int("00101100",2), rs_value=GPIO.LOW)

        ### send the "display on/off control" command (1000) to power on the
        ### display (0100), enable cursor (0010), and enable cursor blink (0001)
        write8_4bitmode(int("00001111",2), rs_value=GPIO.LOW)

        ### clear the display
        write8_4bitmode(int("00000001",2), rs_value=GPIO.LOW)

        ### send the "entry mode set" command to set left-to-right printing (110)
        write8_4bitmode(int("00000110",2), rs_value=GPIO.LOW)

The following sections provide more detail about the steps in this process.

### The magical reset sequence

To reset or initialize the chip:

- Enter `0011----` _three_ times in a row to reset into 8-bit mode
- Enter `0011----` _three_ times in a row followed by `0010----` _once_ to reset
  into 4-bit mode

Specifically, this involves

1. Pulling `RS` low to indicate that we are sending a command, not a character
   to display
2. Pulling `D7` and `D6` low, `D5` high, and `D4` either low (4-bit mode) or
   high (8-bit mode)
3. Ensuring `EN` is low, then raising it high (to trigger a clock signal, which
   is triggered on the rising edge), then lowering it again
4. Repeating #2 and #3 the requisite number of additional times

Note that this sequence simply leaves the low-order bits floating:

:::python
    def write4(value):
        """
        special function to send only the four highest-order bits; low-order bits
        remain floating
        """
        GPIO.output(PIN_RS, GPIO.LOW)

        time.sleep(1e-3)

        GPIO.output(PIN_D[4], GPIO.HIGH if ((value >> 0) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[5], GPIO.HIGH if ((value >> 1) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[6], GPIO.HIGH if ((value >> 2) & 1) > 0 else GPIO.LOW)
        GPIO.output(PIN_D[7], GPIO.HIGH if ((value >> 3) & 1) > 0 else GPIO.LOW)
        pulse_clock()

This magic reset sequence is the only time this 4-bit write is ever used.  And
in fact, it is not strictly necessary to use a special 4-bit write function;
the magic reset sequence to initialize 4-bit mode is actually designed in a
way that allows you to issue two 8-bit commands in 4-bit mode to emulate the
same sequence.  That is,

    :::python
    def init_4bitmode():
        """
        initialize chip into 4-bit interface mode using a special 4-bit write
        function
        """
        write4(int("0011", 2))
        write4(int("0011", 2))
        write4(int("0011", 2))
        write4(int("0010", 2))

is functionally identical to

    :::python
    def init_4bitmode():
        """
        initialize chip into 4-bit interface mode using 8-bit sequences written
        in 4-bit mode
        """
        write8_4bitmode(int("00110011", 2))
        write8_4bitmode(int("00110010", 2))

When initializing into 8-bit mode, you can simply issue regular 8-bit writes
using `D0` through `D7`:

    :::python
    def init_8bitmode():
        """initialize chip into 8-bit interface mode"""
        write8_8bitmode(int("00110000", 2))
        write8_8bitmode(int("00110000", 2))
        write8_8bitmode(int("00110000", 2))

In this case, the low-order bits (`D0` - `D3`) are "don't care" bits and can
have any value.

### Configuring the "function set" options

The "function set" command has the following form:

<table class="table table-sm table-striped table-bordered" style="width: initial; margin-left: auto; margin-right: auto">
<thead>
<tr>
<th style="text-align: center;"><code>D7</code></th>
<th style="text-align: center;"><code>D6</code></th>
<th style="text-align: center;"><code>D5</code></th>
<th style="text-align: center;"><code>D4</code></th>
<th style="text-align: center;"><code>D3</code></th>
<th style="text-align: center;"><code>D2</code></th>
<th style="text-align: center;"><code>D1</code></th>
<th style="text-align: center;"><code>D0</code></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;"><em>DL</em></td>
<td style="text-align: center;"><em>N</em></td>
<td style="text-align: center;"><em>F</em></td>
<td style="text-align: center;">-</td>
<td style="text-align: center;">-</td>
</tr>
</tbody>
</table>

where

- `DL` is 1 for 8-bit interface, 0 for 4-bit.  You _must_ use the same setting
  here as you used for the magical reset sequence; if you don't, you will get
  scrambled commands.
- `N` = 1 for a two-line display; = 0 for a one-line display
- `F` = 1 to use the 5x10 dot character set; = 0 for the 5x8 dot character set

A reasonable command may be

    :::python
    ### send the "function set" command to configure display dimensions
    write8_4bitmode(int("00101100",2), rs_value=GPIO.LOW)

### Configuring "display on/off control" options

The "display on/off control" command has the following form:

<table class="table table-sm table-striped table-bordered" style="width: initial; margin-left: auto; margin-right: auto">
<thead>
<tr>
<th style="text-align: center;"><code>D7</code></th>
<th style="text-align: center;"><code>D6</code></th>
<th style="text-align: center;"><code>D5</code></th>
<th style="text-align: center;"><code>D4</code></th>
<th style="text-align: center;"><code>D3</code></th>
<th style="text-align: center;"><code>D2</code></th>
<th style="text-align: center;"><code>D1</code></th>
<th style="text-align: center;"><code>D0</code></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;"><em>D</em></td>
<td style="text-align: center;"><em>C</em></td>
<td style="text-align: center;"><em>B</em></td>
</tr>
</tbody>
</table>

where

- `D` = 1 turns on the display; = 0 turns it off
- `C` = 1 enables the display of the cursor; = 0 hides the cursor.  Having the
  cursor enabled is great for debugging display issues, but is probably annoying
  for production use.
- `B` = 1 makes the cursor blink; = 0 makes the cursor not blink

A reasonable command may be

    :::python
    ### send the "display on/off control" command (1000) to power on the
    ### display (100), enable cursor (010), and enable cursor blink (001)
    write8_4bitmode(int("00001111",2), rs_value=GPIO.LOW)

Although not strictly required to get the chip to a usable state, the chip does
default to a state where the display is off (`00001000`).  Thus, the display
won't actually show anything until you explicitly issue this command and set the
_D_ bit to 1.

### Clearing the display

Clearing the display is a matter of sending a single least-significant bit with
all others set to zero:

<table class="table table-sm table-striped table-bordered" style="width: initial; margin-left: auto; margin-right: auto">
<thead>
<tr>
<th style="text-align: center;"><code>D7</code></th>
<th style="text-align: center;"><code>D6</code></th>
<th style="text-align: center;"><code>D5</code></th>
<th style="text-align: center;"><code>D4</code></th>
<th style="text-align: center;"><code>D3</code></th>
<th style="text-align: center;"><code>D2</code></th>
<th style="text-align: center;"><code>D1</code></th>
<th style="text-align: center;"><code>D0</code></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">1</td>
</tr>
</tbody>
</table>

This also resets the cursor position to the first register so that subsequent
characters are printed to the freshly cleared screen.  It would appear as

    :::python
    ### clear the display
    write8_4bitmode(int("00000001",2), rs_value=GPIO.LOW)

This is not strictly necessary to get the chip to a usable state, but it does
make life easier.

### Configuring the "entry mode set" options

The "entry mode set" command has the following form:

<table class="table table-sm table-striped table-bordered" style="width: initial; margin-left: auto; margin-right: auto">
<thead>
<tr>
<th style="text-align: center;"><code>D7</code></th>
<th style="text-align: center;"><code>D6</code></th>
<th style="text-align: center;"><code>D5</code></th>
<th style="text-align: center;"><code>D4</code></th>
<th style="text-align: center;"><code>D3</code></th>
<th style="text-align: center;"><code>D2</code></th>
<th style="text-align: center;"><code>D1</code></th>
<th style="text-align: center;"><code>D0</code></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;"><em>I/D</em></td>
<td style="text-align: center;"><em>S</em></td>
</tr>
</tbody>
</table>

where

- `I/D` = 1 sets the mode where the cursor moves to the _right_ by one after a
  new character is displayed; = 0 moves the cursor to the _left_
- `S` = 1 shifts the display along with the above cursor movement; = 0 does
  not shift the display

A reasonable command would be

    :::python
    ### send the "entry mode set" command to set left-to-right printing (110)
    write8_4bitmode(int("00000110",2), rs_value=GPIO.LOW)

Issuing this command is not strictly required to initialize the chip though.

## Writing a message

Write one character at a time by pulling `RS` high and then sending the 8-bit
ASCII representation of the character via `D0` through `D7`.  Pulsing `EN` then
displays this character on the LCD display:

    :::python
    def printmsg(msg):
        """write the message one character at a time"""
        for c in msg:
            write8_4bitmode(ord(c), rs_value=GPIO.HIGH)

Printing a character on the display also moves the cursor (position where
the next character will appear) over.

It is worth pointing out that the HD44780 chip is capable of driving an LCD
display that is 40 characters (columns) long.  Most actual LCD displays appear
to be only 16 characters long though, so the characters for columns 17-40 never
appear anywhere despite being settable.  This has two interesting implications:

1. You can use the registers for characters #17 through #40 as memory to store
   whatever values you want.  They aren't displayed, and if you wire the `RW`
   pin of the chip, you can read the contents of these registers back out.
2. To print characters to the second row of the LCD display, you must either
   fill up columns 17-40 with nonsense to get the cursor to wrap around, or
   explicitly set the cursor position using the "Set DDRAM address" command,
   which is detailed in the following section.

## Setting the cursor position

As described in the above section, the HD44780 addresses its characters in two
rows, each with 40 columns.  To set the position of the input cursor, issue
the "Set DDRAM address" command, which has the form

<table class="table table-sm table-striped table-bordered" style="width: initial; margin-left: auto; margin-right: auto">
<thead>
<tr>
<th style="text-align: center;"><code>D7</code></th>
<th style="text-align: center;"><code>D6</code></th>
<th style="text-align: center;"><code>D5</code></th>
<th style="text-align: center;"><code>D4</code></th>
<th style="text-align: center;"><code>D3</code></th>
<th style="text-align: center;"><code>D2</code></th>
<th style="text-align: center;"><code>D1</code></th>
<th style="text-align: center;"><code>D0</code></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: center;">1</td>
<td style="text-align: center;"><em>ADD</em></td>
<td style="text-align: center;"><em>ADD</em></td>
<td style="text-align: center;"><em>ADD</em></td>
<td style="text-align: center;"><em>ADD</em></td>
<td style="text-align: center;"><em>ADD</em></td>
<td style="text-align: center;"><em>ADD</em></td>
<td style="text-align: center;"><em>ADD</em></td>
</tr>
</tbody>
</table>

where `ADD` bits encode the position (1-40 for the first row, 41-80 for the
second).  Enabling the cursor makes it a lot easier to experiment with this
command, and recall that on a 2x16 LCD display, characters 17-40 are not
visible.

## Other commands

Table 6 in [the datasheet][] describes all of the available commands.  The
command being sent is a function of the highest-order bit:

- `00000001` = clear display
- `0000001-` = reset the cursor position to 0
- `000001a1` = set cursor move direction (a)
- `00001abc` = display on/off (a), cursor on/off (b), cursor blinking on/off (c)
- `0001ab--` = when new characters are displayed, move cursor (a=0) or shift
   the whole screen (a=1), and move/shift to the right (b=1) or left (b=0)
- `001abc--` = set interface length (a), number of lines (b), font (c)
    - a = 1 for 8-bit, 0 for 4-bit
    - b = 1 for 2 lines, 0 for 1 line
    - c = 1 for 5x10 dots, 0 for 5x8 dots
- `01000000` = set CGRAM address (6 bits)
- `10000000` = set display position (DDRAM address; 7 bits)

## Further experimenting

I've written a [test script that demonstrates how to interface with the HD44780
chip][my test script] and perform basic commands using just the Raspberry Pi
GPIO library.  It either prints a message if passed no options, or allows you
to manually pass 8-bit commands using both the 4-bit and 8-bit interfaces.

[oddwires page]: http://www.oddwires.com/16x2-1602-blue-lcd-display-module-with-free-10k-trimmer/
[adafruit driver]: https://github.com/adafruit/Adafruit_Python_CharLCD/blob/master/Adafruit_CharLCD/Adafruit_CharLCD.py
[Adafruit Character LCD guide]: https://learn.adafruit.com/character-lcd-with-raspberry-pi-or-beaglebone-black/wiring
[the datasheet]: https://www.sparkfun.com/datasheets/LCD/HD44780.pdf
[my test script]: https://github.com/glennklockwood/raspberrypi/blob/dbede26970973adae809e4c09cc672a75ebb67fb/test_hd44780.py
