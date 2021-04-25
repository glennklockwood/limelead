---
title: Getting Started with elbencho
shortTitle: elbencho
---

[elbencho][] is an I/O benchmarking tool developed by the illustrious Sven
Breuner to combine the best aspects of fio and IOR into a modern, flexible
I/O testing tool.

{% call alert(type="info") %}
This page is a work in progress; I update it as I experiment with elbencho and
learn more.
{% endcall %}

## Getting Started - Single Client

To do an fio-like write bandwidth test, I do something like this:

```bash
mkdir elbencho.seq.1M
./bin/elbencho ./elbencho.seq.1M \
    --threads 8 \
    --size 1M \
    --block 1M \
    --blockvaralgo fast \
    --blockvarpct 0 \
    --sync \
    --mkdirs \
    --write \
    --delfiles \
    --deldirs \
    --nolive
```

where all of the arguments fall into one of several groups that affect what the
benchmark actually does.

The following define the general parameters of the benchmark:

- `--threads 8` uses eight I/O threads
- `--size 1M` generates files that are 1M (1,048,576 bytes) large
- `--block 1M` performs writes using 1M (1,048,576 bytes) transfers
- `--blockvaralgo fast` uses the "fast" algorithm for filling the write I/O buffers with randomized data
- `--blockvarpct 0` generates new random data in 0% of the write blocks (i.e., every write will contain the same randomized data)
- `--sync` calls sync after every step of the test to ensure that we capture the performance of writing data down to persistent media

The following define what tests to actually run:

- `--mkdirs` creates a directory in which each thread creates files
- `--write` performs a write test
- `--delfiles` deletes the files created during the `--write` phase
- `--deldirs` deletes the directories created during the `--mkdirs` phase

The following affects what information is actually presented to you:

- `--nolive` disables a curses-like live update screen that pops up for long-running test phases

The order of these options is not important.  elbencho will always order the
tests in the sensible way (create dirs, create files, write files, delete files,
delete dirs).

[elbencho]: https://github.com/breuner/elbencho
