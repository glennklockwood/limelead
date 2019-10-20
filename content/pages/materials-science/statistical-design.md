---
title: Statistical Design using Orthogonal Arrays
shortTitle: Statistical Design
---

Statistical design is an alternative to the scientific method of checking one
variable while all others are held constant that saves time in multivariable
systems.  Given a system where all variables (called _factors_) can be
considered independent of each other, an orthogonal array can be set up that
reduces the number of trials in a seven-factor system with three different
values (called _levels_) for each factor from 3<sup>7</sup> trials (if every
combination is tested) to around twenty trials.  Consider the following example
of chemical vapor deposition (CVD) for a polysilica film:

Factor          | 1       | 2          | 3
:--------------:|:-------:|:----------:|:--------------:
Temperature (A) | T - 25  | T          | T + 25
Pressure (B)    | P - 200 | P          | P + 200
Set Time &#40;C)    | t       | t + 8      | t + 16
Cleaning (D)    | None    | Chemical 1 | Chemical 2

We first set up an orthogonal array where each factor is combined with each
level of each factor compared with another factor of another level only once.
In the following matrix, A-B-C-D represent the four _factors_ in the experiment
(temperature, pressure, set time, and cleaning chemical) and 1-2-3 are the
different _levels_ for each of these factors.

 Trial | A   | B   | C   | D   | Result<br>(signal/noise)
:-----:|:---:|:---:|:---:|:---:|:------------------------:
 #1    | 1   | 1   | 1   | 1   | -20
 #2    | 1   | 2   | 2   | 2   | -10
 #3    | 1   | 3   | 3   | 3   | -30
 #4    | 2   | 1   | 2   | 3   | -25
 #5    | 2   | 2   | 3   | 1   | -45
 #6    | 2   | 3   | 1   | 2   | -65
 #7    | 3   | 1   | 3   | 2   | -45
 #8    | 3   | 2   | 1   | 3   | -65
 #9    | 3   | 3   | 2   | 1   | -70
  
Once results of each trial is obtained (which we just call the _signal/noise
ratio_ above), a table of the averaged values of each factor and level must be
constructed:

 Factor |  1  |  2  |  3
:------:|:---:|:---:|:---:
 A      | -20 | -45 | -60
 B      | -30 | -40 | -55
 C      | -50 | -35 | -40
 D      | -45 | -40 | -40

Each cell in the above table is an average of the results of the three trials
which contain its row and column.  For example, cell A1's value (-20) was
obtained by averaging the result of trials #1, #2, and #3 since all three of
those trials had factor A (temperature) set at level 1 (T - 25).

If a less negative (higher) signal/noise ratio is preferable, one can just
select the least negative values for each factor from this last table.
Clearly, for factor A's optimal value occurred under level 1 conditions;
factor B's optimal value was reached while at level 1; C's at level 2; D's at
2 or 3.  Thus, the optimal experimental conditions would be

<p style="text-align:center">
A = 1, B = 1, C = 2, D = 2
</p>

<p style="text-align:center">
or
</p>

<p style="text-align:center">
A = 1, B = 1, C = 2, D = 3
</p>

Notice that this combination of levels was not an experiment actually conducted;
the ideal conditions were inferred using this method of statistical design.
Furthermore, these conditions were determined after only nine experiments as
opposed to the eighty-one (3<sup>4</sup>) required if the exhaustive approach
was taken.

The result of these optimal conditions can also be estimated using the relationship:

<p style="text-align:center">
optimal signal/noise = m + (m<sub>A</sub> - m) + (m<sub>B</sub> - m) + (m<sub>C</sub> - m) + (m<sub>D</sub> - m)
</p>

<p style="text-align:center">
or
</p>

<p style="text-align:center">
optimal signal/noise = m + (m<sub>A</sub> - m) + (m<sub>B</sub> - m)
</p>

where m is the mean of all results, mA is the optimal value of factor A,
m<sub>B</sub> is the optimal value of factor B, and so on.  To be truest to the
statistics behind this model, terms involving small values of (m<sub>X</sub> -
m) are ignored and are considered as error; otherwise, the optimal value will
inaccurately high.

Other analyses that can be done with these results include examining the
standard deviation of each factor in the third table above; this is an
indication of which variables are least and most sensitive to change.  Various
plots can express this sensitivity to variability.  These factor-averages can
also be compared with each other to determine if they interact to any degree
and whether this correlation (if any) is synergistic or antisynergistic.

For more in-depth information on this topic, you may wish to read [Quality
Engineering Using Robust Design by M.S. Phadke][Phadke 1989].  The third chapter
of that book details statistical design using orthogonal arrays. 

[Phadke 1989]: https://www.amazon.com/Quality-Engineering-Using-Robust-Design/dp/0137451679
