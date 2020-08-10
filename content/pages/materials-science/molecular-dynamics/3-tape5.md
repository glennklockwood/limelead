---
title: 3. Editing tape5
shortTitle: Editing tape5
order: 30
---

## The Important Parts

The `tape5` file is the core of the simulation since it specifies exactly what
you want to do with the atoms you've got in your `knite12`. Most of the values
you will be commonly changing can be found about halfway down the file and look
something like this:

```
         3=ntype   )        10=jread   )        10=icheck  )     20000=iequil
      1000=istore  )      1000=isave   )     40000=istop   )      1000=iprint
     300.0=temp    )  5.50d-08=rc      )        20=lupdt   )   1.0d-15=deltim
        1 =ilabel  )        1 = isurf  )      2000=ieqct   )        1 = ipara
     0000 =istill  )      000 =nsur    )       100=nbin    ) 1.2 )  5.1 )
)6.6180d+22=redens)  5.5d-07=cte)  5=ilx)  5=ily)  6=ilz)  5=icry)
 +4.000d+00=z1      ) 28.090d+00=mass1   )
 -2.000d+00=z2      ) 16.000d+00=mass2   )
 +3.000d+00=z3      ) 26.989d+00=mass3   )
```

One of the most important things to remember when editing `tape5` is that this
file is a _fixed-format file_. Be sure that you never change the spacing of the
various fields and don't change the positions of the equal signs. The simulation
code expects input values to reside at very specific parts of the file. For
example, the value for `ntype` must be displayed between the 2nd and 10th
character in the line. If you accidentally add or remove spaces, you may shift
your intended value for `ntype` out of this region, and the simulation will
either crash (if it detects non-numeric characters where it expects a number) or
misbehave (it may equate an empty `ntype` field as being 0 instead of the
intended 3).

Bearing this in mind, you will probably find yourself editing many of the values
in this part of the `tape5` file. Here is a brief rundown of what each parameter
does:

- `ntype` determines the starting configuration of your system. Set to 3 if
  you want to use an existing `knite12`, or set to 1 if you want the MD code to
  generate a crystal based on `ilx`, `ily`, `ilz`, and `icry` (see below).
- `jread` is maximum possible ltypes (elements) for the simulation. This should
  always be 10.
- `icheck` controls the granularity of secondary calculations during the
  simulation. You shouldn't need to change this.
- `iequil` is the amount of time (in iterations) you want the system's
  temperature to be actively maintained at the beginning of the simulation. Set
  this to 0 for a purely NVE run, set it to a large number (`iequil` > `icalc`)
  for a purely NVT run, or something in between for an NVE run with time for
  equilibration.
- `istore` is the frequency (in iterations) with which the `knite9` file is
  updated. If `istore` = 5000, the simulation will save its configuration to
  `knite9` every 5000th step.
- `isave` determines how often the system's configuration will be added to the
  `knite1`. If `isave` = 5000, the `knite1` file will contain the system
  configuration at every 5000th iteration.
- `istop` is how many iterations you'd like the simulation to go through before
  halting.
- `iprint` is the frequency (in iterations) with which diagnostic data and
  system averages are printed to the simulation output.
- `temp` is the temperature (in Kelvin) at which you would like to keep the
  system during equilibration.
- `rc` is the radial cutoff distance (in cm) for the interaction potential. Do
  not change this.
- `lupdt` is the frequency (in iterations) with which the simulation's neighbor
  lists are updated. Do not change this.
- `deltim` is the time step for the numerical integration, or how much time
  passes between consecutive iterations of the system. You will typically not
  have to change this.
- `ilabel` =0 to relabel all atoms according to their z position at the
  beginning of the simulation. Otherwise, keep this as 1.
- `isurf` =0 if you want to disable the periodic boundary in z. Use in
  conjunction with icall = 2 to simulate surfaces.
- `ieqct` is the frequency (in iterations) with which diagnostic data from the
  thermostat is printed to the simulation output.
- `ipara` does not need to be changed.
- `istill` is the number of atoms to freeze for a simulation. This is typically
  used in conjunction with `ilabel` = 0.
- `nsur` does not need to be changed.
- `nbin` does not need to be changed.
- The "1.2" and "5.1" parameters do not need to be changed.
- `redens` is the intended density (in atoms/cc) of the simulation. If this is
  specified, the system will be rescaled in size to take this density. If it
  is zero, the density of the starting configuration is unchanged.
- `cte` is the coefficient of thermal expansion. This term also rescales the
  starting configuration relative to 300 K if the temp parameter is not 300 K.
- `ilx`, ily, and ilz specify the size of the crystal to be built when `ntype`
  = 1. These parameters have no function when `ntype` = 3.
- `icry` is the type of crystal to be built when `ntype` = 1. It has no function
  when `ntype` = 3.

The lines immediately following define the ten types of atoms (since `jtype` =
10) that the simulation can use in terms of their charge (`z`) and mass
(`mass`).  The first line (`z1` and `mass1`) describe atoms of `ltype` = 1,
where "`ltype`" is how the code distinguishes different elements from each
other. In virtually all our simulation work, `ltype` = 1 represents Si, `ltype`
= 2 represents O, `ltype` = 3 represents Al, and `ltype` = 4 represents Ca.
ltypes 5-10 vary in their definition.

## The Rest

The remaining information stored in the `tape5` is relatively unimportant for
the beginner.  The only possible exception to this is the very first line of
`tape5`:

```
      0=izero ,      1=icall ,  00010=idepot,      0=ladd  ,    300=ndpmax.
```

If `izero` = 1, the code will zero out all of the time derivatives of all of the
atoms in your system before the simulation starts.  This has been found to cause
problems when used in conjunction with our thermostat because it produces
velocity distributions that deviate significantly from the Maxwell-Boltzmann
distribution.  This should always be 0 unless specifically told otherwise.

The `icall` option controls the "type" of simulation.  `icall` = 1 runs a
normal "bulk" simulation where periodic boundaries are maintained in three
dimensions, and when `icall` = 1, ensure that `isurf` = 1 as well.  `icall` = 2
runs a "surface" simulation where the periodic boundary in z is broken, 1 nm of
vacuum is added above `zl`, and a reflective boundary is placed at z = 0 and z
= `zl` + 1.0 nm (= `zreft`).  When `icall` = 2, always set isurf = 0.

The rest of the `tape5` are just the empirical parameters for the interatomic
potentials we use.  The following information is provided purely for future
reference.  Do not worry about them if this is your first time reading through
this tutorial.

The three-body parameters appear near the top of `tape5`:

```
***Three-body potentials parameters ***
   rlc(i) in cm,  lam(i) in erg,    gam(i) in cm
    2.600000d-08    1.000000d-11    2.000000d-08
    3.000000d-08   24.000000d-11    2.800000d-08
    3.000000d-08   24.000000d-11    2.800000d-08
```

Each line contains the parameters for a single j-i-k triplet.  `rlc` is what we
call the `r0` parameter in publications; lam is λ, and gam is γ.  The `θ0`
parameters are hard-coded and cannot be changed via `tape5`.  Knowing which
line corresponds to which j-i-k triplet is not intuitive; in short, you have
to look at the MD source code (specifically `table.f`).  It is often easier to
ask your advisor.

The huge blocks of numbers everywhere else are the two-body parameters.  Just
below the redens line and ltype definitions are the BMH potential parameters:

```
***Born-Mayer-Huggins parameters :aij in ergs ***
)0.18770d-08=11)0.29620d-08=12)0.25230d-08=13)2.21500d-09=14)0.12890d-08=15)
)0.17200d-08=16)0.20000d-08=17)0.20010d-08=18)0.25610d-08=19)0.12890d-08=10)
)0.29620d-08=21)0.07250d-08=22)0.24900d-08=23)5.70000d-09=24)0.35500d-08=25)
)0.33000d-08=26)0.14000d-08=27)0.31950d-08=28)0.40900d-08=29)0.35500d-08=20)
)0.25230d-08=31)0.24900d-08=32)0.05000d-08=33)0.24200d-08=34)0.06000d-08=35)
```

Although this probably looks intimidating, it's quite simple.  The heading
(`Born-Mayer-Huggins parameters :aij in ergs`) tells us what the following
block of numbers represents (the BMH A<sub>ij</sub> terms).  Look at the first
field:

```
)0.18770d-08=11
```

This means that the A<sub>ij</sub> for the 1-1 pair (`ltype`=1 and `ltype`=1,
or Si-Si interactions) is 0.18770 x 10<sup>-8</sup> ergs.  The next field,
`=12`, describes the Si-O interactions.  `ltype` = 10 is represented by 0 in
these input lines, so the `=30` field is the interaction between `ltype` 3 and
`ltype` 10.

An important point to notice is that i-j interactions are equivalent to j-i
interactions (e.g., A<sub>ij</sub> for Si-O pairs is the same as it is for
O-Si pairs), but there are still two fields in `tape5` for each one (`=12` and
`=21`).  As a result, **only half of the pair parameters are actually used.  The
code only uses i-j parameters for i &le; j.**  So in the case of Si-O
interactions, you can have

```
)0.45500d-08=12
```

and

```
)0.29620d-08=21
```

Since i &le; j for the `=21` field, that is the value that will be used for all
Si-O and O-Si interactions.  The value entered in the `=12` field
(`0.45500d-08`) is simply discarded.

---

Next page: [Making a Glass](4-making-glass.html)
