"""Provides additional filters and functions to Jinja2

This module provides additional filters and functions to the Jinja2 rendering
environment.  All such filters and functions must be pure (no side effects) or
depend implicitly on Pelican since they are also made available by the
limeleadlib.jinja2content plugin where there is no Pelican context explicitly
available during rendering.
"""
import os
import datetime

import pelican
import markdown

from .core import get_dir_metadata, pagepath2sourcepath, get_git_mtime

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
    "includefile": lambda x: open(x, 'r').read(),
}
