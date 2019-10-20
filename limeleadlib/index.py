"""Builds indices for directories of pages
"""

import os
import glob

import yaml
import pelican

from .core import get_dir_metadata, get_page_metadata

def sourcepath2relpath(sourcepath, rootpath):
    """Converts an absolute path to a page's source to a relative path.

    Args:
        sourcepath (str): Full path to a page's source markdown or a directory in
            the page path (e.g.,
            ``/Users/glock/src/git/pelican-page/content/pages/data-intensive/hadoop``)
        rootpath (str): Absolute path to the root of the Pelican page path (e.g.,
            ``/Users/glock/src/git/pelican-page/content/pages``)

    Returns:
        str: Path to `rootpath` relative to the Pelican page path (e.g.,
        ``data-intensive/hadoop``)
    """
    return sourcepath[len(os.path.commonpath([rootpath, sourcepath]))+1:].lstrip("/")

def make_dir_index(pagesubdir, pagerootdir, siterootdir):
    """Creates a list of index entries for a directory

    Given a path, builds a list containing the metadata of each asset and a fully
    resolved link to it.  Output takes the form::

        [
            {
                "title": "Descriptive title",
                "url": "/path/to/file.html",
                "type": "file",
                ...
            },
            ...
        ]

    The descriptive title comes from the asset's metadata (the page metadata's
    ``title`` attribute as defined in its Markdown metadata or the directory's
    ``title`` attribute as defined in its _metadata.yml file, if present).

    Args:
        pagesubdir (str): Full path to a source directory for which an index
            should be created
        pagerootdir (str): Full path to the root directory of the page sources
        siterootdir (str): The SITEURL for the published site

    Returns:
        list: List of dictionaries, where each dictionary contains the metadata
        for a single asset that is a direct child of `pagesubdir`.  It will also
        contain the additional metadata keys:

        - ``url``, a fully resolved path to the published asset
        - ``type``, ``file`` or ``directory``
    """
    assets = []

    # inode is either a file or directory contained in pagesubdir
    for inode in sorted(glob.glob(os.path.join(pagesubdir, '*'))):
        relpath = sourcepath2relpath(sourcepath=inode, rootpath=pagerootdir)

        # if this file/dir is a file
        if os.path.isfile(inode) \
        and inode.endswith('.md') \
        and os.path.basename(inode) != "index.md":
            metadata = get_page_metadata(inode)
            metadata.update({
                "url": "%s/%s" % (siterootdir, relpath.rsplit('.', 1)[0] + ".html"),
                "type": "file",
            })
            assets.append(metadata)

        # if this file/dir is a dir
        elif os.path.isdir(inode):
            metadata = get_dir_metadata(inode)
            metadata.update({
                "url": "%s/%s" % (siterootdir, relpath.rstrip("/") + "/"),
                "type": "directory",
            })
            assets.append(metadata)
        else:
            # ignore non-file inodes
            pass

    # Sort assets
    def _sorter(record):
        return (record.get('order', 0), record.get('type', ''), record.get('title', ''))

    return sorted(assets, key=_sorter)

def make_index_html_ul(pagesubdir, pagerootdir, siterootdir, hlevel=2):
    """Creates an HTML unordered list for a directory

    Given a path, builds an index list (in HTML) describing the contents of that
    directory.

    Args:
        pagesubdir (str): Absolute path to a source file for which an index
            entry should be created
        pagerootdir (str): Full path to the root directory of the page sources
        siterootdir (str): The SITEURL for the published site
        hlevel (int): Which heading level to create the index heading.  If zero,
            do not draw heading.

    Returns:
        str: An HTML string that will generate a link to this file
    """

    # Draw heading and optional short description
    my_metadata = get_dir_metadata(pagesubdir)
    output = ""
    if hlevel:
        output += "<h%d>" % hlevel
        output += "%(title)s" % my_metadata
        output += "</h%d>\n" % hlevel
    if 'contentHtml' in my_metadata:
        output += my_metadata['contentHtml'] + "\n\n"

    # Draw bulleted list of contents
    output += "<ul>\n"
    for asset in make_dir_index(pagesubdir, pagerootdir, siterootdir):
        output += '  <li><a href="%(url)s">%(title)s</a></li>\n' % asset
    output += "</ul>\n"

    return output

def make_index_md(pagesubdir, pagerootdir, siterootdir):
    """Creates an index markdown for a directory

    Given a path, builds an index markdown file describing the contents of that
    directory.

    Args:
        pagesubdir (str): Full path to a source file for which an index entry
            should be created
        pagerootdir (str): Full path to the root directory of the page sources
        siterootdir (str): The SITEURL for the published site

    Returns:
        str: A Markdown string that will generate a link to this file
    """

    my_metadata = get_dir_metadata(pagesubdir).copy()
    output = ""
    if 'content' in my_metadata:
        output += my_metadata['content'] + "\n\n"
        # drop content from metadata in actual index since this is a giant blob of text
        del my_metadata['content']
    if 'contentHtml' in my_metadata:
        del my_metadata['contentHtml']

    for asset in make_dir_index(pagesubdir, pagerootdir, siterootdir):
        output += "- [%(title)s](%(url)s)\n" % asset
    output += "\n"

    # prepend metadata
    output = "---\n%s\n---\n" % yaml.dump(my_metadata).rstrip() + output
    return output

def make_md_indices(pelican_obj):
    """Walks the content tree and generates index.md files where missing
    """
    root_path = pelican_obj.settings['PATH']

    for rel_pagepath in pelican_obj.settings['PAGE_PATHS']:
        # pagepath = absolute path to the root dir of the md page sources
        pagepath = os.path.join(root_path, rel_pagepath)
        # dirpath = absolute path to a subdirectory of pagepath containing md sources
        for dirpath, _, filenames in os.walk(pagepath):
            # don't generate index if static html already exists or this is the
            # root index (Pelican owns that directly)
            if 'index.html' not in filenames and dirpath != pagepath:
                index_md = make_index_md(dirpath, pagepath, pelican_obj.settings['SITEURL'])
                index_md_file = os.path.join(dirpath, 'index.md')
                with open(index_md_file, 'wt') as index_md_fp:
                    index_md_fp.write(index_md)

def register_functions(pelican_obj):
    pelican_obj.env.globals.update({
        "make_index_html_ul": make_index_html_ul,
    })

def register():
    """Registers plugin"""
    pelican.signals.generator_init.connect(register_functions)
    pelican.signals.page_generator_init.connect(make_md_indices)
