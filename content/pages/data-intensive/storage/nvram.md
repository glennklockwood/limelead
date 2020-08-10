---
title: Principles of Non-volatile RAM
shortTitle: Non-volatile RAM
overrideLastMod: February 1, 2016
---

## Introduction

The information on this page has been compiled based on notes I've taken during
various (public) vendor presentations and meetings.  I am by no means an expert
in nonvolatile storage, so if you find any factual errors or information that
is out of date, please do contact me and let me know.

## NAND-based Flash Storage

NAND-based flash storage encompasses the solid-state storage media found in
products ranging from consumer SD cards and cell phones to enterprise-grade
NVMe devices.

To make the most of the following notes, it is important to distinguish NAND
drives, which are the individual NAND chips purchased by integrators, from
flash devices, which contain multiple NAND chips and a NVM controller in a nice
package (2.5" drive, PCIe card, etc).  There are only a few companies
manufacturing NAND chips (e.g., Toshiba, Samsung, and Micron) because
doing so requires multi-billion dollar fabs; far more companies buy NAND chips
and integrate them into drives (e.g., Kingston and Seagate) that consumers and
enterprises purchase.

### Hardware Technologies

Commercial NAND flash storage chips come in two flavors:

- **floating gate** cells store data on a second floating gate on a
  transistor.  This floating gate is a conductor and is electrically isolated
  from the transistor using a relatively thick insulator.  Floating gate NAND
  has historically been the technology of choice in planar (2D) NAND devices.

- **charge trap** cells also store data on a floating gate on a transistor.
  Unlike floating gate cells though, this gate is effectively a pure insulator
  so that electrons that are stuck there stay there forever.  Charge trap is
  the preferred technology for 3D NAND devices.

These NAND cells are programmed (that is, data is saved to them) by sparking
the gap between the insulating floating gate and its transistor.  This
sparking process, called _hot carrier injection_, causes physical damage to
the transistor, and this is why flash storage can be written ("programmed") a
certain number of times (its characteristic endurance, often expressed in units
of drive writes per day, or DWPD).

The effects of this damage are different in floating gate and charge trap;
because floating gate stores its electrons on a conductive floating gate, any
short circuit that forms as a result of damage will cause the entire cell to
become useless.  Conversely, charge trap cells are unable to fully drain in
the presence of a small short circuit and are therefore more durable.  However,
charge trap cells are more expensive to manufacture than floating gate cells.

Modern 2D NAND relies on roughly 80 electrons trapped on the floating gate to
store its data--a 1 or 0 value.  Leaky gates can cause data loss over years as
these electrons tunnel out of the floating gate.

There are different cells with different bit densities on the market today and
in the near future:

- **SLC flash** stores 1 bit per cell and has only two electronic levels (1 or
  0) that must be measured to read its contents.
- **MLC flash** stores 2 bits per cell and has four electronic levels
  (corresponding `0b00`, `0b01, `0b10, and `0b11` states) that must be
  measured to read its contents.
- **TLC flash** stores 4 bits per cell and has eight electronic levels
  (a level for each state between `0b000` and `0b111`)
- **QLC flash** stores 8 bits per cell and has sixteen electronic levels
  (a level for each state between `0b0000 and 0b1111`)

As more electronic levels are required to store the state of each cell,
three general trends dominate:

1. The read/write performance of the cell goes down because the flash
   controller has to do a lot more work to ensure that what it is reading
   or writing is completely correct
2. The endurance of the cell goes down because the cells have to be
   crammed closer together to allow sparks of very precise power levels
   to be used to program all of the different states a cell can take.
3. The cost per bit goes down because the bit density per cell increases
   at a rate far in excess of the cost to manufacture more precise cells.

Because data loss in flash is caused by tunneling and tunneling gets easier as
NAND cells shrink in dimensions, flash performance and endurance has been
getting _worse_ as lithographic processes shrink.  The error rates and stability
of planar (2D) NAND are scale down so poorly that 2D NAND is simply not
economical below 16 nm lithographic processes.  However the move to 3D NAND
has allowed larger lithographic feature sizes to be used, improving the
performance and endurance of 3D NAND relative to state-of-the art planar NAND.

### Flash Translation Layer

NAND chips are designed in a way that means data cannot be modified in place; a
cell must be erased to a known state before it can be re-written.  Furthermore,
individual bytes cannot be be written; flash devices must write entire _pages_
of data at once, where a page is typically 16 KiB (as of 1Q2016).  To
complicate things, erasing data must be done in entire _blocks_, where a typical
block is 512 KiB (in 1Q2016).  Thus, to write a page, the flash controller must
already know where a fully erased page is, or erase an entire block to create an
erased page.  If a block must be erased, its valid pages must first moved to
other empty pages before the erasure.  This logic is implemented in the SSD's
**flash translation layer (FTL)**.

To improve the response time of writes, SSDs will perform background **garbage
collection** to ensure that a reserve of empty pages are always available for
incoming writes.  Flash garbage collectors have their own I/O stream that
operates in parallel with user-generated I/O; as a user writes data to an SSD,
those writes are constantly appended to anywhere they will fit.  Meanwhile, the
garbage collector is constantly looking for erase blocks that have a minimal
number of valid pages; when it finds one, it copies those pages to blocks that
are already mostly full, then erases the old block.  This process of copying
valid pages out of the way of a block erasure causes **write amplification**,
since NAND cells are still worn out by this copying, but the copy is occurring
without any new user data actually arriving on the device.

It should be obvious that the process of programming NAND is logically
complicated.  To deal with the logic required to juggle empty pages, partially
filled blocks, and garbage collection, modern SSDs contain spare NAND to make
the process of finding empty pages easier, and the flash controllers embedded
within the SSDs are often multi-core CPUs that contain their own DRAM and,
effectively, are a self-contained computer in their own right.  Enterprise SSDs
may also RAID data across different NAND chips within the drive, and all SSDs
encode extensive ECC protection (both on the data at rest, as well as in all
of the data paths inside the device) to counteract the effect of leaky gates.

### Additional Information

The following resources contain more detail about the topics discussed above:

* [Understanding Flash][flashdba tutorial series] is a fantastic series of posts
  that explain many of the important technological considerations surrounding
  using flash.
* [Micron, Samsung in Flash Battle][eetimes micron samsung article] highlights
  the differences between floating gate and charge trap NAND cells.
* [How It's Built: Micron/Intel 3D NAND][micron 3d nand] is an interesting piece
  on how Micron's 3D NAND differs from other manufacturers who were first to
  market with 3D NAND.

## Storage Class Memory and Phase-change Memory

The following information is derived from public disclosures and public
conversations I've had with company representatives at Flash Memory Summit 2016.
None of this information was shared with me in confidence.

### 3D XPoint / Intel Optane / Micron QuantX

Intel and Micron have been cagey about their 3D XPoint non-volatile,
byte-addressable memory technology.  Although there is lots of speculation about
the actual materials technology under the hood, it sounds like it is based on
a phase-change memory (PCM) technology.  It uses [chalcogenides][3dxpoint uses chalcogenides]
but, unlike other "conductive-bridge" or "filamentary" PCM technologies, it uses
a bulk switching phenomenon to store its data.  In principle, this would
increase the endurance of the cells.

It is more energy efficient than DRAM due to its nonvolatility, and Intel has
stated that it consumes between 0.3 and 0.5 pJ per bit to move data, which I
believe is ~2x less power than standard DRAM.  Also unlike DRAM, 3D XPoint is
also purported to be truly byte addressable and not require that an entire page
of DRAM be powered to read a single byte.  However, its latency to the CPU is
substantially higher than DRAM, with public numbers for 3D XPoint reflecting
about 4 &mu;sec at the hardware level, compared to 0.1 &mu;sec for DRAM.

3D XPoint is manufactured using a 20 nm lithographic process, but because it
does not rely on electrons to store state, it can be scaled down beyond the
breakdown point of conventional NAND.

### Crossbar

Crossbar is a filamentary PCM technology where each cell, built on a 40 nm
lithographic process of "CMOS-friendly" (but proprietary) materials, has a 1
or 0 state depending on the presence of a 5 nm metal filament that is grown
or destroyed through an &alpha;-Si crystal.  Its signal-to-noise ratio improves
as the lithography is scaled down, unlike NAND, so process shrinks below today's
40 nm process gives the technology runway.

[flashdba tutorial series]: https://flashdba.com/category/storage-for-dbas/understanding-flash/
[eetimes micron samsung article]: http://www.eetimes.com/document.asp?doc_id=1328874
[micron 3d nand]: http://www.eejournal.com/archives/articles/20160201-micron/
[3dxpoint uses chalcogenides]: http://www.eetimes.com/document.asp?doc_id=1328682
