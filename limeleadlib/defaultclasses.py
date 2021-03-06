import pelican
import bs4

def add_defaultclasses(html, tag, add_classes):
    """Correct problems in tables generated by Python-Markdown

    This method traverses the HTML generated by Python-Markdown and adds
    user-specified classes to the table object.

    Todo:
        1. Accept a dict that maps tags to classes so we can do a single-pass
           update of the HTML
        2. Add a flag to only modify tags that have no current class

    Args:
        html (str): The HTML generated by Python-Markdown
        tag (str): The HTML tag to which default classes should be applied
        add_classes: (list of str): Any classes that should be applied to
            all ``<table>`` tags encountered

    Returns:
        str: The input HTML with tables modified to reflect the aforementioned
        modifications.
    """
    changes = 0
    soup = bs4.BeautifulSoup(html, 'html.parser')
    for element in soup.find_all(tag):
        if add_classes:
            element['class'] = element.get('class', []) + add_classes
            changes += 1

    return str(soup), changes

def apply_defaultclass(pelican_obj):
    """Applies a default class to objects

    Note that the table tag is handled by limeleadlib.tables

    Args:
        pelican_obj: A pelican object (usually a page) that has a `_content`
        attribute containing rendered HTML

    Returns:
        str: HTML with default classes applied
    """
    html, changes = add_defaultclasses(pelican_obj._content, 'blockquote', ['blockquote', 'ml-4', 'p-2'])
    #if changes:
    #    print("Altered %d tag(s) in %s" % (changes, pelican_obj.source_path))

    return html

def apply_defaultclasses(content_object):
    if not content_object._content:
        return
    content_object._content = apply_defaultclass(content_object)

def register():
    pelican.signals.content_object_init.connect(apply_defaultclasses)
