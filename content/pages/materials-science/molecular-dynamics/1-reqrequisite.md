---
title: 1. Prerequisite Knowledge
shortTitle: Prerequisite Knowledge
order: 10
overrideLastMod: May 18, 2012
---

## Scientific Background

The research carried out at the Interfacial Molecular Science Laboratory (IMSL)
at Rutgers focuses on studying materials interfaces.  Beyond this broad
description, the scientific background prerequisite to your research project
should be provided by your advisor.  Particular references can typically be
looked up in databases such as the [ISI Web of Science](https://www.isiknowledge.com/), and if you know an
article's DOI, you can also directly access the online version via [doi.org](https://dx.doi.org/).
Many of IMSL's publications are also available on the [IMSL website](http://glass.rutgers.edu/resume.html).

## Understanding Computational Methods

The majority of the simulations we do at the IMSL use molecular dynamics (MD).
A good primer on the MD method can be found here:

[A molecular dynamics primer by Furio Ercolessi](ercolessi-1997.pdf)

Reading up to page 23 (up through section 3.4; up to "the caloric curve") will
provide a good idea of the sorts of parameters you will be changing in our MD
code.  

While Google is generally a good source of background information, be forewarned
that the type of molecular dynamics simulations carried out by many research
groups around the world are not quite like what we do.  The aforementioned
Ercolessi primer is quite close to our approach, but many other tutorials
online describe the sorts of MD done in the life sciences (drug discovery,
protein folding, etc.).  The details of such simulations are of limited
applicability here.

## Computer Proficiency

Although research at the Interfacial Molecular Science Laboratory focuses
largely on studying materials interfaces, understanding the computational
framework surrounding our research methods is as critical as understanding the
science motivating our work.  We have traditionally used UNIX-based computing
environments to conduct our simulations, and while it is possible to carry out
a research project here with only a cursory understanding of UNIX, having a
sound understanding of how to work in technical UNIX is much to your benefit.
Working _with_ the computing environment instead of _against_ it goes a long way
towards making your life easier and minimizing tedium, and since the majority
of scientific computing done today is carried out in similar UNIX-like systems,
the skills you develop here will be transferable to many other potential jobs
in the future.

Invest some time early on in ensuring you know how to use some of the core tools
supporting your research.  As free time presents itself, you are encouraged not
only to read scientific literature relevant to your project, but to review how
to work with our computational framework efficiently.  At the very minimum,
you should possess the following prerequisite knowledge before you begin this
tutorial:

- Understand how to move around the filesystem.  Ensure that you know the following:
    - what the `cd` and `ls` commands do
    - the concepts of directories (aka folders), subdirectories, and how to express specific directory locations
    - what the `.` and `..` directories are
    - what `~` represents when expressing directory locations
- Understand how to manipulate files.  In particular, know how to
    - copy (`cp`), move (`mv`), rename (`mv`), and delete (`rm`) files
    - make new directories (`mkdir`), delete directories (`rm -r`)
- Know how to use the vi text editor.  Open a terminal and type `vimtutor` to
  begin a very helpful tutorial and get you started.
    - While you can use other editors such as `pico` or `nano`, they are very
      limited in utility
    - The methods you use in vim (find, find and replace, quit, paging up/down)
      appear in many other UNIX/Linux commands (`sed`, `less`, `more`)
    - Excellent tutorials for learning vi can be found by Googling for "vi
      tutorial"
- Understand how to quickly view files using `cat`, `head`, and `tail`
- Know how to find help!
    - The man command displays online help for any command, e.g., `man ls`
    - There are thousands of books and websites devoted to learning Linux out
      there.  Don't be afraid to use Google.
    - If possible, work closely with your advisor or supervisor.  You can learn
      a lot by seeing what commands they use.

A few other computing skills will help make your life easier.  Some of them are covered in this tutorial, and all can be Googled.  For example,

- `grep` and `awk`
- FORTRAN 77
- pipes and redirects in bash
- UNIX file permissions (chmod, chown, chgrp)
- bash scripting (for loops, if-then-else, variables, arithmetic)

## Resources

### Scientific Background

- [A molecular dynamics primer by Furio Ercolessi](ercolessi-1997.pdf)

### Using UNIX/Linux

- [MAC OS X UNIX Toolbox: 1000+ Commands for the Mac OS X](https://www.oreilly.com/library/view/mac-os-x/9780470478363/)
  is a very good beginner's resource for quickly getting comfortable with UNIX.
  Although this book is geared towards Mac OS X, our Linux clusters and
  workstations use all of the same commands.

### Programming

- [Fortran 77 Tutorial (Stanford)](http://www.stanford.edu/class/me200c/tutorial_77/)
  is a good practical guide to getting started with FORTRAN 77.
- [A Summary of Fortran](http://www.math.utah.edu/~beebe/software/fortran-documentation/ftnsum.pdf)
  (pdf) is a much more detailed description of FORTRAN.  Recommended more for
  students with an existing background in other programming languages.
- Intel, Sun/Oracle, IBM, PGI, and GNU all release FORTRAN manuals for their
  compilers online.  Although they're written for each company's specific
  compiler, most of it is general to all FORTRAN.

---

Next page: [Overview of our MD code](2-our-code.html)
