"""
Plugin to deal with the Hugo shortcodes that were used in the Hugo version of my
website.  Also a good template for a generic find-and-replace Pelican plugin.

Note that this specific implementation clashes with the limelead.jinja2content
plugin since that will error on any shortcodes before this plugin gets run
unless this plugin is given _last_ in pelicanconf.py.
"""
import re
import pelican

FIGURE_SHORTCODE = re.compile(r'(\{\{\<\s*figure[\s\n]+.*?\>\}\})', re.DOTALL)

def figure_shortcode(input_str):
    """Replaces instances of the figure shortcode with HTML

    Scans ``input_str`` for all instances of the Hugo {{< figure >}} shortcode
    and replaces it with the HTML that Hugo would have generated.

    Args:
        input_str (str): Markdown that may contain Hugo shortcodes

    Returns:
        str: The same Markdown as input by ``input_str`` except with the
            relevant Hugo shortcodes replaced.
    """

    match = FIGURE_SHORTCODE.search(input_str)

    while match:
        match_str = match.group(1)
        src_match = re.search(r'src=[\'"](.*?)[\'"]', match_str)
        link_match = re.search(r'link=[\'"](.*?)[\'"]', match_str)
        alt_match = re.search(r'alt=[\'"](.*?)[\'"]', match_str)
        caption_match = re.search(r'caption=[\'"](.*?)[\'"]', match_str)

        img_tag = ""
        caption_tag = ""
        link_tag = ""
        replace_str = ""
        if src_match:
            img_tag = '<img src="%s">' % src_match.group(1)
        if caption_match:
            caption_tag = '<figcaption>%s</figcaption>' % caption_match.group(1)
        if link_match:
            link_tag = '<a href="%s">%%s</a>' % link_match.group(1)
        if link_tag:
            img_tag = link_tag % img_tag

        if img_tag or caption_tag:
            replace_str = "<figure>%s%s</figure>" % (img_tag, caption_tag)

        input_str = input_str.replace(match_str, replace_str)

        match = FIGURE_SHORTCODE.search(input_str)

    return input_str

def process_shortcodes(content_object):
    """Call individual find-and-replace functions

    Calls find-and-replace functions that do string substitutions, then uses
    their outputs to hack the internal state of content objects before they're
    processed.

    Args:
        content_object (contents.Content): Content object to be processed
    """
    if not content_object._content:
        return
    # call the find-and-replace function and hack the internal state
    content_object._content = figure_shortcode(content_object._content)

def register():
    pelican.signals.content_object_init.connect(process_shortcodes)

################################################################################

TEST_STRS = [
"""
{{< figure >}}
""",
"""
## Experimental Setup

The following figure shows my test circuit.

<div class="shortcode">
{{< figure
    src="tlc555-experiment-test2.jpg"
    link="tlc555-experiment-test2.jpg"
    alt="555 testing circuit"
    caption="555 testing circuit"
>}}
</div>

Of note,
""",
"""
<div class="shortcode">
{{< figure   
    src="tlc555-experiment-test2.jpg"
    alt="555 testing circuit"
>}}
</div>
""",

]

def test_shortcode():
    """Test shortcode replacement of the figure shortcodes
    """
    def test_one_input(input_str):
        fixed_str = figure_shortcode(test_str)
        assert fixed_str != test_str

    for test_no, test_str in enumerate(TEST_STRS):
        func = figure_shortcode
        func.description = "figure shortcode #%d" % (test_no+1)
        yield func, test_str
