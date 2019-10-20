---
title: Working with Jupyter and Matplotlib
shortTitle: Jupyter and Matplotlib
---
Here are some notes I've taken about using Jupyter Lab and its integrations with
matplotlib.

## Matplotlib Configuration

There are two mechanisms for having matplotlib render directly inside a
Jupyterlab window:

    % matplotlib inline

or

    % matplotlib widget

The `inline` backend generally just works, and what you see is what you will get
when you `savefig()`.  The `widget` backend is interactive, but is extremely
resource hungry, slow, and prone to all manner of problems that I don't like to
deal with.  Sadly, the `inline` backend has a cryptic configuration interface.

### inline backend

In general you can change parameters in `$PWD/matplotlibrc`.  However, there are
a set of seemingly arbitrary [matplotlib configuration parameters which are
_not_ honored](https://stackoverflow.com/questions/42656668/matplotlibrc-rcparams-modified-for-jupyter-inline-plots).

For example, changing font size requires

    $ ipython profile create
    $ vim ~/.ipython/profile_default/ipython_config.py

and then explicitly addding

    :::python
    c.InlineBackend.rc.update({"font.size": 16})

There may not be a commented-out version of this in the template created by
`ipython profile create`.
