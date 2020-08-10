---
title: 7. Extracting Data from Output with grep
shortTitle: Extracting Data with grep
order: 70
---

It is admittedly tedious and repetitive to scan through output files for every
completed job, and this reality is what usually gives way to corner-cutting
and the inevitable instance where a routine simulation goes horribly wrong but
remains undetected. Fortunately, UNIX-like systems come with tools to
streamline the processing of simulation output.

`grep` is a standard UNIX utility that searches files for instances of a
phrase and prints them to the screen. It is arguably the most useful tool for
quickly digesting simulation output, as it can extract and summarize the data
you want while skipping over everything else. For example, if your simulation
output is in a file called `out.300`, you can quickly look at how the system
temperature evolved over the course of that simulation by grepping for the
phrase "temperature" by issuing `grep temperature out.300` in same directory
as your output:

```
$ grep 'temperature' out.300
old reference temperature = 0.20000D+04
new reference temperature = 0.30000D+03
temperature 0.32738174E+03 std dev 0.18819916E+03
temperature 0.30000000E+03
velocities scaled to temperature of 300.000 after 2000 iterations
old temperature was 0.30502881E+03
temperature 0.30001813E+03 std dev 0.44833240E+01
temperature 0.30000000E+03
...
temperature 0.34382206E+03 std dev 0.51213221E+01
temperature 0.34598132E+03
temperature 0.34646638E+03 std dev 0.49272970E+01
temperature 0.35067531E+03
index <temperature> <poten. energy> <pressure> <total energy>
```

This quickly reveals a wealth of information relevant directly to the
temperature of the simulation. However, each print contains both the average
and instantaneous temperature. To extract only the average temperature, you
can refine the phrase for which you grep:

```
$ grep 'temperature.*std' out.300
temperature 0.32738174E+03 std dev 0.18819916E+03
temperature 0.30001813E+03 std dev 0.44833240E+01
temperature 0.29998880E+03 std dev 0.38058309E+01
...
temperature 0.34382206E+03 std dev 0.51213221E+01
temperature 0.34646638E+03 std dev 0.49272970E+01
```

This refined search phrase `temperature.*std` returns any line that contains
both `temperature` and `std` separated by any text (`.*`). To extract only the
instantaneous temperature, you can pipe the results of one grep to another:

```
$ grep 'temperature   ' out.300 | grep –v 'std'
temperature 0.30000000E+03
temperature 0.30000000E+03
temperature 0.30000000E+03
...
temperature 0.34143007E+03
temperature 0.34598132E+03
temperature 0.35067531E+03
```

The first grep searches for instances of the phrase `temperature` followed by at
least three spaces, and the results of this search are then grepped for lines
that do not include (`-v`) the phrase `std`. Sometimes refining the extraction
of certain data requires a degree of cleverness. For example, try grepping for
instantaneous temperatures as above, but don't include the extra spaces after
`temperature`.

It is very common to save the results of such greps to a file so the data can
be plotted. Redirecting grep's output is a simple matter of using the output
redirect (`&gt;`) operator:

```
$ grep 'temperature.*std' out.300 > avgtemp.300
$ grep 'temperature ' out.300 | grep –v 'std' > insttemp.300
```

Using grep and redirecting output are standard features of any UNIX-like system.
Googling for "grep" and "redirect stdout" will reveal a wealth of information
and tutorials. You can also play with `egrep` and `awk`, which are capable of
much more sophisticated data extraction.

You can also quickly visualize this data using gnuplot.  This is covered in the
next section.

---
Next page: [Plotting Data with gnuplot](8-gnuplot.html)
