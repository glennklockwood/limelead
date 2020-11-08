import os

import pelican
import bs4

def set_card_meta(pelican_obj):
    """Set image and description metadata

    Sets the 'image' and 'description' keys in page metadata based on the
    content of the page.  Intent for use with templates that contain twitter
    cards or Open Graph metadata tags.

    Args:
        pelican_obj: A pelican object (usually a page) that has a `_content`
            attribute containing rendered HTML
    """
    soup = bs4.BeautifulSoup(pelican_obj._content, 'html.parser')

    description, image = None, None

    # find a description
    metadata = pelican_obj.metadata
    element = soup.find('p')
    if not metadata.get('description') and element:
        description = element.get_text()
        description = ' '.join([x.strip() for x in description.splitlines()])
        if len(description) > 197:
            description = description[:197].rstrip(' .') + "..."
        pelican_obj.metadata['description'] = description

    # find an image
    element = soup.find('img')
    if not metadata.get('image') and element and element.get("src"):
        pelican_obj.metadata['image'] = os.path.dirname(pelican_obj.path_no_ext) + "/" + element.get("src")

def set_card_metas(page_generator_write_page, content):
    if not content._content:
        return
    set_card_meta(content)

def register():
    pelican.signals.page_generator_write_page.connect(set_card_metas)
