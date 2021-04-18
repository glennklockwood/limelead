"""Provides additional filters and functions to Jinja2

This module provides additional filters and functions to the Jinja2 rendering
environment.  All such filters and functions must be pure (no side effects) or
depend implicitly on Pelican since they are also made available by the
limeleadlib.jinja2content plugin where there is no Pelican context explicitly
available during rendering.
"""
import os
import yaml
import datetime

import pelican
import markdown
import pandas
import tabulate

from .core import get_dir_metadata, pagepath2sourcepath, get_git_mtime, \
                  flatten_results
from .tables import fix_md_table, DEFAULT_TABLE_CLASSES

def md2html(md_content, settings):
    """Converts arbitrary Markdown to HTML

    Args:
        md_content (str): Text encoded as Markdown
        settings (dict): Dictionary containing the Pelican MARKDOWN variable's 
            contents

    Returns:
        str: HTML representation of md_content
    """
    _md = markdown.Markdown(**settings)
    return _md.convert(md_content)



def json2table(*args, **kwargs):
    return yaml2table(*args, **kwargs)

def yaml2table(datafile, show_cols, tablefmt='html'):
    """Converts contents of a JSON data file into an ASCII table

    Takes a JSON encoded list of dictionaries, converts it into a Pandas
    DataFrame, then converts that DataFrame into an ASCII table using the
    ``tabulate`` library.  The datafile should contain JSON of the form::

        [
            {
                "col1: val1,
                "col2": val2,
                ...
            },
            ...
        ]

    Args:
        datafile (str): Absolute path to a JSON data file
        show_cols (list): List of tuples where first element contains column
            names in _datafile_ that should be rendered in the ASCII table and
            whose second elements are the column names to be rendered
        tablefmt (str): ASCII format to render table; passed directly to the
            ``tabulate.tabulate()`` function

    Returns:
        str: HTML representation of _datafile_ in the given ASCII encoding
    """
    from_dict = yaml.load(open(datafile, 'r'))

    dataframe = pandas.DataFrame.from_dict(flatten_results(from_dict)).fillna(value="")

    show_cols_keys = [x[0] for x in show_cols if x[0] in dataframe.columns]

    html = tabulate.tabulate(
        dataframe[show_cols_keys],
        tablefmt=tablefmt,
        headers=[x[1] for x in show_cols if x[0] in show_cols_keys],
        showindex=False)
    html, _ = fix_md_table(html, add_table_classes=DEFAULT_TABLE_CLASSES + ["table-responsive-md"])
    return html

def add_filters(pelican_obj):
    pelican_obj.env.filters.update(FILTERS)

def register_functions(pelican_obj):
    pelican_obj.env.globals.update(FUNCTIONS)

def register():
    pelican.signals.generator_init.connect(add_filters)
    pelican.signals.generator_init.connect(register_functions)

FILTERS = {
    'basename': os.path.basename,
    'attributes': lambda x: x.__dict__,
    'dir_metadata': get_dir_metadata,
    'sourcepath': pagepath2sourcepath,
    'getmtime': lambda x: datetime.datetime.fromtimestamp(os.path.getmtime(x)),
    'getmtime_git': get_git_mtime,
    'md2html': md2html,
    'rstrip': lambda x: (x).rstrip(' .'),
}

FUNCTIONS = {
    "json2table": json2table,
    "includefile": lambda x: open(x, 'r').read(),
    "yaml2table": json2table,
}
