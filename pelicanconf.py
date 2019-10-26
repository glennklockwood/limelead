#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Glenn K. Lockwood'
SITENAME = 'Glenn K. Lockwood'
SITEURL = ''
TIMEZONE = 'America/Los_Angeles'
DEFAULT_LANG = 'en'

# Pelican configuration
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
DEFAULT_PAGINATION = False

# Site content configuration
PATH = 'content'
STATIC_PATHS = ['static']
PATH_METADATA = '((pages|static)\/)?(?P<path_no_ext>.*)\.(?P<path_ext>.*)'
PAGE_SAVE_AS = '{path_no_ext}.html'
PAGE_URL = '{path_no_ext}.html'
STATIC_SAVE_AS = '{path_no_ext}.{path_ext}'
STATIC_URL = '{path_no_ext}.{path_ext}'
DIRECT_TEMPLATES = ['index']

# Theme configuration
THEME = 'themes/molecular'
THEME_STATIC_DIR = '' # do not put static resources in a separate dir
SIDEBAR_ON_LEFT = False
BANNER = True
BANNER_ALL_PAGES = True

# Plugin configuration
PLUGINS = [
#   'limeleadlib.shortcodes',
    'limeleadlib.tables',
    'limeleadlib.index',
    'limeleadlib.maketoc',
    'limeleadlib.filters',
    'limeleadlib.defaultclasses',
    'limeleadlib.jinja2content',
#   'limeleadlib.sitemap',
#   'limeleadlib.debug',
]
#MD_EXTENSIONS = ['codehilite(noclasses=True, pygments_style=native)', 'extra']  # enable MD options

MARKDOWN = {
    'extensions': [
        'markdown.extensions.toc',
        'markdown.extensions.codehilite',
        'markdown.extensions.extra',
        'markdown.extensions.tables',
    ],
    "extension_configs": {
        "markdown.extensions.codehilite": {
            # this lets us highlight lines in arbitrary text (e.g., stdout)
            # without weird stuff being highlighted
            "guess_lang": False 
        },
    },
    'output_format': 'html5',
}
