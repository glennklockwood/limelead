"""Process Markdown contents through Jinja2 before rendering HTML instead of
after rendering HTML.  Used to allow Jinja2 expansion in Markdown documents.

This is modified from the jinja2content plugin included in 

    https://github.com/getpelican/pelican-plugins.

It falls under the GNU Affero General Public License v3.0.

Modified to automatically inject Jinja2 macros specific to the theme used for
limelead.
"""

import os
import tempfile
import functools

import jinja2
import pelican

from .filters import FILTERS, FUNCTIONS

def hack_contents(text):
    """Manipulates the contents of a source file

    This manipulates the contents of a source file before it is processed by
    Jinja2 and the reader.  Useful for injecting code into every page,
    find-and-replacing text, etc.  Since the source file is converted into
    HTML after this, you can spike in, for example, Markdown at this point.

    Args:
        text (str): The contents to be rendered

    Returns:
        str: The manipulated version of `text`
    """
    return "{% from 'macros.html' import figure, inset, alert %}" + text

class JinjaContentMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # will look first in 'JINJA2CONTENT_TEMPLATES', by default the
        # content root path, then in the theme's templates
        local_dirs = self.settings.get('JINJA2CONTENT_TEMPLATES', ['.'])
        local_dirs = [os.path.join(self.settings['PATH'], folder)
                      for folder in local_dirs]
        theme_dir = os.path.join(self.settings['THEME'], 'templates')

        loaders = [jinja2.FileSystemLoader(_dir) for _dir
                   in local_dirs + [theme_dir]]
        if 'JINJA_ENVIRONMENT' in self.settings: # pelican 3.7
            jinja_environment = self.settings['JINJA_ENVIRONMENT']
        else:
            jinja_environment = {
                'trim_blocks': True,
                'lstrip_blocks': True,
                'extensions': self.settings['JINJA_EXTENSIONS']
            }
        self.env = jinja2.Environment(
            loader=jinja2.ChoiceLoader(loaders),
            **jinja_environment)

        # add in all the filters from limeleadlib.filters so we can use them in Markdown
        self.env.filters.update(FILTERS)
        self.env.globals.update(FUNCTIONS)

        # hack up the special markdown renderer so we can render Markdown in
        # Jinja2 in Markdown using the global Pelican markdown settings (phew!)
        if 'md2html' in self.env.filters:
            self.env.filters.update({
                'md2html': functools.partial(self.env.filters['md2html'], settings=self.settings)
            })


    def read(self, source_path):
        # note we call hack_contents here to manipulate the input before passing
        # it to Jinja2/Markdown
        with pelican.utils.pelican_open(source_path) as text:
            text = hack_contents(text)
            # print("=" * 80)
            # print("Unrendered text")
            # print("=" * 80)
            # print(text)
            text = self.env.from_string(text).render()
            # print("=" * 80)
            # print("Rendered text")
            # print("=" * 80)
            # print(text)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(text.encode())
            f.close()
            content, metadata = super().read(f.name)
            os.unlink(f.name)
            return content, metadata


class JinjaMarkdownReader(JinjaContentMixin, pelican.readers.MarkdownReader):
    pass

class JinjaRstReader(JinjaContentMixin, pelican.readers.RstReader):
    pass

class JinjaHTMLReader(JinjaContentMixin, pelican.readers.HTMLReader):
    pass

def add_reader(readers):
    for reader in [JinjaMarkdownReader, JinjaRstReader, JinjaHTMLReader]:
        for ext in reader.file_extensions:
            readers.reader_classes[ext] = reader

def register():
    pelican.signals.readers_init.connect(add_reader)
