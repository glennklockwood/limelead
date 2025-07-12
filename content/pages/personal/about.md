---
title: About Me
---

## Short version

Here's a few vignettes I've had to write for different speaking engagements and
proposals.  I put them here so I don't have to write them from scratch every
time I'm asked, and hopefully they're up to date.

### Biosketch

Here's a biosketch as of April 2024:

> Glenn K. Lockwood is a Principal Engineer at Microsoft, where he is
> responsible for supporting Microsoft’s largest AI supercomputers through
> workload-driven systems design. His work has focused on applied research and
> development in extreme-scale and parallel computing systems for
> high-performance computing, and he has specific expertise in scalable
> architectures, performance modeling, and emerging technologies for I/O and
> storage. Prior to joining Microsoft, Glenn led the design of several
> large-scale storage systems, including the world’s first 30+ PB all-NVMe
> Lustre file system for the Perlmutter supercomputer at NERSC. He holds a Ph.D.
> in Materials Science.

### Research statement

The SC conference asked for my research statement (ostensibly) to match me to
paper submissions as a technical program committee referee. I don't actually do
research, so it's mostly a restatement of my biosketch.

> Glenn K. Lockwood's research interests lie in the intersection of artificial
> intelligence and supercomputing infrastructure, with a specific focus on
> workload-driven system architecture design. His previous work focused on
> applied research and development in extreme-scale and parallel computing
> systems for high-performance computing, and he has specific expertise in
> scalable architectures, performance modeling, and emerging technologies for
> I/O and storage. His current work has pivoted towards holistic system design
> specifically for AI training and inferencing workloads and understanding how
> to map the needs of specific AI applications to different compute, network,
> storage, and infrastructure technologies.

## Long version

Here's the story of my professional life. I try to keep it up to date.

### Early Life and Education

I was born in Hawaii and moved to the mainland when I was quite young.  I grew
up in the suburbs of central New Jersey, just off of 8A on the turnpike.  After
completing high school, I attended the [School of Engineering at Rutgers
University][ru engineering] where I majored in ceramic engineering and spent a
year and change doing research using molecular simulation at the [Interfacial
Molecular Science Lab][imsl].  I graduated in the final class of ceramic
engineers at Rutgers; the program was replaced by one in materials science and
engineering in the following year.

Ceramic science is a fascinating one, but a field trip to a local glass factory
in my final year as an undergraduate made me realize that I really did not want
to be an engineer when I grew up.  To defer having to go out into the real world
to make a living, I opted to go to graduate school instead and enrolled in the
materials engineering program at Lehigh University in Bethlehem, Pennsylvania.
My hope was to become an electron microscopist, as Lehigh had some of the 
world's most [sophisticated aberration-corrected scanning transmission electron
microscopes][camn] at the time (supercomputers of the microscope world, in a
sense).

Those plans did not pan out, and after a semester in Pennsylvania, I returned to
Rutgers to continue doing research with molecular dynamics simulations.

### Getting into Supercomputing

In the four years I was doing my Ph.D. work at Rutgers, I started collecting old
UNIX workstations.  In the course of playing with them all, I began benchmarking
my molecular dynamics codes on them, and this gave me an appreciation for the
nuances and performance features of various old RISC architectures.  I had also
started getting involved in the HPC community online, and I credit my friends
(now colleagues) on IRC and Twitter with providing the inspiration and knowledge
to consider HPC as a career rather than a mere hobby.

During graduate school I also married my wife (and spent two months doing
research out of her father's tractor shop on the Canadian prairie--an
interesting experience!).  When I finally completed [my
dissertation][my dissertation], I made the decision to change careers and
pursue my interest in HPC full-time.  And, since I had also forced my wife to
live with me in [suburban New Jersey][highland park] for four years, I looked
for jobs in places that were most un-like suburban New Jersey.  Much to my
great fortune, the [San Diego Supercomputer Center][sdsc] had an open position
in user services, and I was able to trick them into thinking I knew enough
about HPC to be employable.

SDSC provided me with access to the resources, expertise, and support to develop
a strong foundation in high-performance computing, and my role in user services
put me in a position to solve challenging issues in a variety of scientific
domains.  Most notably, the next-generation sequencing industry (largely
centered in San Diego) began growing into the realm of HPC at that time, and my
understanding of the intricacies of [SDSC's exotic data-intensive
supercomputer][gordon] led me to a number of [consulting projects in
sequencing][janssen slides].

My [analyses of the computational requirements demanded by DNA
sequencing][sequencing cost blog] caught the attention of a few companies who
were technologically ahead of the curve.  I was eventually extended a unique
opportunity to join an [early-stage sequencing startup][10xtech] that was
developing a revolutionary new product, and my desire to experience the startup
life and be a part of such a rapidly growing industry lured me away from SDSC.

### Foray into Genomics

After eighteen months in San Diego, I moved up to Oakland and joined [10x 
Genomics][10x genomics] as a DevOps Engineer (a job which I had no idea how to
do).  My job involved running a small cluster, maintaining a couple hundred
terabytes of storage, and integrating 10x's software product with HPC
infrastructure and cutting-edge DNA sequencers.

My heart never left supercomputing though, and shortly after my one-year anniversary at 10x, I
returned to the world of supercomputing at the [National Energy Research
Scientific Computing Center][nersc] (NERSC) at the [Lawrence Berkeley National
Laboratory][lbl.gov] (LBNL).
Although I only worked there thirteen months, working at 10x was the experience
of a lifetime. 
I had the honor of working with some of the most exceptional people I've ever encountered in my
professional life, and I learned skills and perspective that have benefitted me
tremendously in my career since.

### Storage and I/O at NERSC

At NERSC, I joined the [Advanced Technologies Group][nersc atg] where I helped 
with systems design and procurement to ensure that the next generation of
supercomputers will be able to keep pace with the demands of future scientific
research.  I was one of the resident experts in parallel I/O and new storage
technologies, and the emphasis of my work was on parallel I/O system
architectures.  This included understanding the [low-level hardware details of
non-volatile storage media][nvme page], new software technologies for
[high-performance I/O transport][io forwarding page], optimization points
for various parallel storage systems including Lustre, Spectrum Scale, and
[object stores][object stores page], and where all of these technologies were
going.

In late 2019, I was asked to lead NERSC's [Storage Systems Group][nersc ssg]
which is responsible for managing most of the center's production storage
systems totalling over 200 PB of tape and 120 PB of disk.
I was responsible for managing eight storage engineers and a significant capital
budget, and during my tenure we brought in two new staff and procuring and
deploying a 60 PB Spectrum Scale file system.
However, the challenges of being a first-time manager amidst a global pandemic
and the loss of the technical responsibilities led me to step down from this
acting position a year later and return to the Advanced Technologies Group at
NERSC.

After returning to Advanced Technologies, my role was still predominantly
storage-focused and composed of three major responsibilities:

1. Staying abreast of new technologies, coordinating relationships with storage
   vendors, and evaluating new technologies as they may pertain to future HPC
   systems.
2. Advocating for NERSC externally (whether it be to other HPC facilities, the
   vendor community, or the public at large) to ensure that the great work we
   do, the great systems we deploy, and the unique workload requirements we face
   are well represented across the HPC community.
3. Shepherding cross-team projects and providing technical accountability for
   the purposes of procurement, contracting, external oversight, and project
   management.

My role had me oversee increasingly larger projects.  Once the 35 PB all-flash
Lustre file system I oversaw was delivered and accepted as part of the
Perlmutter system, I moved on to overseeing the overall technology integration
strategy and program surrounding NERSC's follow-on system, NERSC-10.  I
[struggled to settle into this role][life and leaving nersc] and ultimately
left NERSC in May 2022.

### Moving to the cloud

In June 2022, I joined Microsoft as a Principal Product Manager in the Azure
Storage organization.  I was designated Azure's go-to expert in HPC storage, and
I was tasked with developing an overall product strategy for HPC storage across
Azure's first-party and marketplace services. In practice, this meant helping
Azure's own storage product teams (like the [Blob][] and [Azure Managed Lustre][])
define the performance and features required by HPC workloads. I also worked
with external HPC storage companies to figure out ways their products could
complement Azure's own storage offerings.

Over the course of eighteen months as an Azure Storage product manager though, I
learned that there is a huge difference between being an _HPC person in a
storage organization_ and being a _storage person in an HPC organization_. I
also learned that HPC, not storage, is what gets me out of the bed in the
morning, and I don't make a great product manager.  These epiphanies led me to
realize that being a product manager in a storage organization was not what I
wanted to do for the rest of my life.

So, in January 2024, I changed roles within Microsoft. I moved laterally along
two dimensions:

1. I went from the product management discipline into the engineering
   discipline. This brought me closer to the familiar world of being hands-on
   with HPC technologies.
2. I left the Azure Storage organization and joined the Azure Specialized
   Workloads organization. Azure Specialized is the umbrella under which all
   the compute infrastructure that isn't general-purpose (like GPUs and
   InfiniBand) falls.

I became a Principal Software Engineer supporting the HPC infrastructure used by
Microsoft's largest AI customers. My responsibility was to understand what
massive-scale AI workloads would need to accomplish in the coming years, how
those workloads plan to approach those problems from a software standpoint, and
how that workload-centric view should steer the overall system architecture of
next-generation supercomputers.

[ru engineering]: http://soe.rutgers.edu
[imsl]: http://glass.rutgers.edu/
[lehigh]: http://www.lehigh.edu/matsci/
[camn]: http://www.lehigh.edu/%7Einano/emf_facility.html
[my dissertation]: http://dx.doi.org/doi:10.7282/T3B856T3
[highland park]: http://www.hpboro.com/
[sdsc]: http://www.sdsc.edu/
[gordon]: http://www.sdsc.edu/services/hpc/hpc_systems.html#gordon
[janssen slides]: http://www.slideshare.net/glennklockwood/janssen-presentation
[sequencing cost blog]: http://blog.glennklockwood.com/2014/01/the-1000-genome-computational.html
[10xtech]: https://web.archive.org/web/20140321154310/http://www.10xtechnologies.com/
[ilmn stocks]: https://www.google.com/finance?q=NASDAQ:ILMN
[nersc]: http://www.nersc.gov/
[lbl.gov]: http://www.lbl.gov/
[nersc atg]: http://www.nersc.gov/about/groups/advanced-technologies-group/
[10x genomics]: http://www.10xgenomics.com/
[nvme page]: ../data-intensive/storage/nvram.html
[io forwarding page]: ../data-intensive/storage/io-forwarding.html
[object stores page]: ../data-intensive/storage/object-storage.html
[nersc ssg]: https://www.nersc.gov/about/nersc-staff/storage-systems-group/
[life and leaving nersc]: https://blog.glennklockwood.com/2022/05/life-and-leaving-nersc.html
[Blob]: https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-overview
[Azure Managed Lustre]: https://learn.microsoft.com/en-us/azure/azure-managed-lustre/amlfs-overview
