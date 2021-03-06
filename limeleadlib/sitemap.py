"""Generates representations of the sitemap

Useful for generating

- Full sitemap
- Nav bar
"""
import os
import sys
import json

import pelican
from . import debug

NAVBAR_TEMPLATE_FILENAME = 'container-navbar.html'

def dirtree(root):
    """Returns directory structure as a dictionary.

    Walks a directory tree and builds a dictionary that mimics the directory
    tree and files.  Assumes all inodes are either directories or files; does
    not understand anything more complicated like symbolic links.

    Args:
        root (str): Path to base of tree to walk

    Returns:
        dict: Full directory tree represented as a dictionary
    """
    structure = {}
    for dirpath, dirnames, filenames in os.walk(root):
        parents = dirpath.split(os.sep)
        _pointer = structure
        for parent in parents:
            if parent not in _pointer:
                _pointer[parent] = {}
            _pointer = _pointer[parent]
        for filename in filenames:
            _pointer[filename] = None

    return structure

def find_first_branch(tree):
    """Returns first dictionary with more than one key

    Walks a dictionary of dictionaries and returns the first dictionary that
    contains more than one key.  Does not return its key though.  Does not
    return a copy either.

    Args:
        tree (dict): A dictionary of dictionaries

    Returns:
        dict: Dictionary pointing to the first sub-dictionary within tree
        that contains more than one key.
    """
    if len(tree) > 1:
        return tree
    else:
        tree = find_first_branch(list(tree.values())[0])
        return tree

class NavBar(object):
    """Generic class to build an HTML navigation bar for the site.

    Args:
        tree (dict): Dictionary structure of the site's content as generated by
            the ``dirtree()`` function.
    """
    def __init__(self, tree):
        self.root = find_first_branch(tree)
        self._init_output()
        self.output = self.recurse_tree(self.root, None, self.output)
        self._finalize_output()

    def __str__(self):
        return self.output

    @classmethod
    def from_path(cls, path):
        """Generates a NavBar object from a file path 

        Given a path to the website's content directory, generates the NavBar
        object.

        Args:
            path (str): Path to the directory structure containing markdown
                files
        """
        return cls(dirtree(path))

    def _init_output(self):
        self.output = ""

    def _finalize_output(self):
        self.output += ""

    def recurse_tree(self, value, parents, navbar):
        """Builds a textual representation of the directory tree

        Walks a dictionary containing the markdown files and directories
        comprising the site and builds a string based on its contents.  The
        actual string being built are determined by

        - md_text()
        - dir_text()
        - dir_text_finalize()

        Args:
            value (dict or scalar): A node in the dictionary tree or a scalar
                value indicating a leaf (file) in the tree.
            parents (list): A list of all of the parent nodes that led to
                ``value``.  If ``value`` is scalar, this is a list describing
                the full path to a file.
            navbar (str): The string being built to represent the tree.

        Returns:
            str: The partially completed `navbar` string.
        """
        depth = len(parents) if parents else 0
        # if value is a dict, descend into that directory
        if isinstance(value, dict):
            if parents:
                navbar += self.dir_text(parents, depth)
            for _key, _value in value.items():
                _parents = parents.copy() if parents else []
                navbar = self.recurse_tree(_value, _parents + [_key], navbar)
            if parents:
                navbar += self.dir_text_finalize(parents, depth)
            return navbar

        # if value is not a dict, then parents contains the full path
        if parents[-1].endswith('.md'):
            return navbar + self.md_text(parents, depth)
        return navbar

    @staticmethod
    def md_text(parents, depth=None):
        """Generates a textual representation of a leaf node (file)

        Args:
            parents (list): List of all elements that build up to the leaf
            depth (int): The number of parents the leaf has.  Equivalent to
                ``len(parents)``; calculated as such if not specified.
        """
        if depth is None:
            depth = len(parents) if parents else 0
        return "\n%s (depth %d)\n%s\n" % (parents[-1], depth, "-" * len(parents[-1]))

    @staticmethod
    def dir_text(parents, depth=None):
        """Generates a textual representation of a directory

        Args:
            parents (list): List of all elements that build up to the leaf
            depth (int): The number of parents the leaf has.  Equivalent to
                ``len(parents)``; calculated as such if not specified.
        """
        if depth is None:
            depth = len(parents) if parents else 0
        return os.path.join(*parents) + " (depth %d)\n" % (depth - 1)

    @staticmethod
    def dir_text_finalize(parents, depth=None):
        """Generates any required text after a directory's children have all
        been generated.

        Args:
            parents (list): List of all elements that build up to the leaf
            depth (int): The number of parents the leaf has.  Equivalent to
                ``len(parents)``; calculated as such if not specified.
        """
        if depth is None:
            depth = len(parents) if parents else 0
        return ""

class NavBarBootstrap4(NavBar):
    """Renders a Bootstrap navbar with dropdowns

    Builds a Bootstrap 4.0 navbar when given a path to the contents directory.
    Was done as a proof of concept, but is not production ready.  Missing a
    number of features:

    1. Current document is not highlighted
    2. Does not resolve proper page titles

    Also flattens directory structure beyond the first subdirectory, which
    results in some very long dropdowns for deeply nested directories.
    """
    def _init_output(self):
        self.output = """
<nav class="navbar navbar-expand-lg navbar-light bg-light">
  <a class="navbar-brand" href="#">Navbar</a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNavDropdown" aria-controls="navbarNavDropdown" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>
  <div class="collapse navbar-collapse" id="navbarNavDropdown">
    <ul class="navbar-nav">"""

    def _finalize_output(self):
        self.output += "</ul>\n</div>\n</nav>\n"

    @staticmethod
    def md_text(parents, depth=None):
        """Generates a textual representation of a leaf node (file)

        Args:
            parents (list): List of all elements that build up to the leaf
            depth (int): The number of parents the leaf has.  Equivalent to
                ``len(parents)``; calculated as such if not specified.
        """
        if depth is None:
            depth = len(parents) if parents else 0
        fullpath = os.path.join(*parents)
        if depth == 0:
            return '<li class="nav-item"><a class="nav-link" href="{{ SITEURL }}/%s">%s</a></li>\n' % (fullpath.rsplit('.', 1)[0] + '.html', '%s (%d)' % (parents[-1], depth))
        return '<a class="dropdown-item" href="{{ SITEURL }}/%s">%s</a>\n' % (
            fullpath.rsplit('.', 1)[0] + '.html',
            '%s (%d)' % (parents[-1].rsplit('.', 1)[0], depth))

    @staticmethod
    def dir_text(parents, depth=None):
        """Generates a textual representation of a directory

        Args:
            parents (list): List of all elements that build up to the leaf
            depth (int): The number of parents the leaf has.  Equivalent to
                ``len(parents)``; calculated as such if not specified.
        """
        if depth is None:
            depth = len(parents) if parents else 0
        if depth == 1:
            output = """
<li class="nav-item dropdown">
  <a class="nav-link dropdown-toggle" href="#" id="navbarDropdownMenuLink" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
    %s (%d)
  </a>
  <div class="dropdown-menu" aria-labelledby="navbarDropdownMenuLink">\n""" % (os.path.join(*parents), depth)
        else:
            output = '<div class="dropdown-divider"></div>\n<a class="dropdown-item" href="#">%s (%d)</a>\n' % (os.path.join(*parents), depth)
        return output

    @staticmethod
    def dir_text_finalize(parents, depth=None):
        """Generates any required text after a directory's children have all
        been generated.

        Args:
            parents (list): List of all elements that build up to the leaf
            depth (int): The number of parents the leaf has.  Equivalent to
                ``len(parents)``; calculated as such if not specified.
        """
        if depth is None:
            depth = len(parents) if parents else 0
        if depth == 1:
            return "  </div>\n</li>\n"
        return ""

def make_bootstrap4_navbar(pelican_obj):
    """Generates the html for a Bootstrap 4 navbar
    """
    output_filename = os.path.join(pelican_obj.settings['THEME'], "templates", NAVBAR_TEMPLATE_FILENAME)

    rel_input_path = pelican_obj.settings['PATH'][len(os.getcwd()):].lstrip(os.sep)
    input_tree = find_first_branch(dirtree(rel_input_path))
    non_page_dirs = []
    for dirname in input_tree.keys():
        if dirname not in pelican_obj.settings['PAGE_PATHS']:
            non_page_dirs.append(dirname)

    for dirname in non_page_dirs:
        del input_tree[dirname]

    navbar = NavBarBootstrap4(input_tree)
    with open(output_filename, 'w') as output_file:
        output_file.write(str(navbar))

def register():
    pelican.signals.page_generator_init.connect(make_bootstrap4_navbar)
