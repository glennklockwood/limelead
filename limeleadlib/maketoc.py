import re
import os

import bs4
import pelican
import markdown.extensions.toc

RE_HEADING = re.compile('^h[1-6]$')

def make_anchor(text, anchors):
    """Creates an anchor from heading text

    Produces the same behavior of Python-Markdown's TOC extension so that we can
    generate the same tags that it does.  Sadly this means that it is possible
    to have degenerate anchors since Markdown does not prevent this.

    Args:
        text (str): Text of the heading
        anchors (set): Existing anchors already in use in the document.  Used to
            ensure that degenerate anchors are not created.
    """

    anchor = markdown.extensions.toc.slugify(text, '-')
    while anchor in anchors:
        anchor += "-0"
    return anchor

def make_toc(content):
    if isinstance(content, pelican.contents.Static):
        return

    soup = bs4.BeautifulSoup(content._content, 'html.parser')

    min_level = 99999
    anchors = set([])
    toc = []
    for heading in soup.find_all(RE_HEADING):
        level = int(heading.name[1:])
        text = heading.get_text()
        anchor = make_anchor(text, anchors)

        toc.append({
            "level": level,
            "text": text,
            "anchor": anchor,
        })

        anchors |= anchors
        min_level = min(min_level, level)

        # >>> print(heading, type(heading))
        # <h2 id="introduction">Introduction</h2> <class 'bs4.element.Tag'>
        # >>> print(heading.__dict__, type(heading))
        # {
        #   'parser_class': <class 'bs4.BeautifulSoup'>,
        #   'name': 'h4',
        #   'namespace': None,
        #   'prefix': None,
        #   'known_xml': False,
        #   'attrs': {'id': 'environment-variables'},
        #   'contents': ['Environment Variables'],
        #   'parent': ...

    for toc_entry in toc:
        toc_entry['level'] -= min_level - 1
    content.toc = toc

def draw_toc_2level(toc, maxlevel=2):
    if not toc:
        return ""

    html = []
    lastlevel = None
    open_tags = []
    for index, entry in enumerate(toc):
        thislevel = entry['level']
        if thislevel > maxlevel:
            continue

        if lastlevel is None:
            html.append('<ul class="section-nav">')
            open_tags.append('ul')
        elif lastlevel < thislevel:
            if lastlevel == 1:
                html[-1] = html[-1][:-5] # trim off </li>
                html[-1] += '\n<ul>'
                open_tags.append('li')
                open_tags.append('ul')
        elif lastlevel > thislevel:
            if thislevel == 1:
                html[-1] += '\n</ul>\n'
                open_tags.pop()
            html[-1] += "</li>"
            try:
                open_tags.pop()
            except IndexError as e:
                raise TypeError("maketoc found unmatched tags - html syntax error?") from e

        html.append('<li class="toc-entry"><a href="#%s">%s</a></li>' % (
            entry['anchor'],
            entry['text']))

        lastlevel = thislevel

    for tag in open_tags[::-1]:
        html.append("</%s>" % tag)

    return "\n".join(html)

def draw_toc_list(toc):
    output = ""
    lastlevel = None
    for entry in toc:
        if lastlevel is None:
            output += '<ol class="navbar-nav">\n'
        elif entry['level'] > lastlevel:
            output += "<ol>\n"
        elif entry['level'] < lastlevel:
            output += '</ol>\n</li class="nav-item">'
        else:
            output += "</li>\n"

        output += '<li class="nav-item"><a class="nav-link" href="#%s">%s</a>' % (
            entry['anchor'],
            entry['text'])
        lastlevel = entry['level']

    output += "</li>\n</ol>\n"

    return output

def draw_toc_filter(pelican_obj):
    pelican_obj.env.filters.update({
        'drawtoc': draw_toc_2level,
    })

def register():
    pelican.signals.content_object_init.connect(make_toc)
    pelican.signals.generator_init.connect(draw_toc_filter)
