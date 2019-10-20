"""
Plugin used to debug the plugin interfaces exposed by Pelican

See http://docs.getpelican.com/en/stable/plugins.html#list-of-signals for the
list of entrypoints
"""
import os
import pprint
import pelican

def print_interface(*args, **kwargs):
    pp = pprint.PrettyPrinter(indent=4)
    for index, arg in enumerate(args):
        print("================================================================================")
        print("Positional argument %d" % index)
        print("Type: %s" % type(arg))
        print("================================================================================")
        pp.pprint(arg.__dict__)

    for key, value in kwargs.items():
        print("================================================================================")
        pp.pprint(key)
        print("Type: %s" % type(value))
        print("================================================================================")
        pp.pprint(value)
 
def print_context_page(*args):
    pp = pprint.PrettyPrinter(indent=4)
    for index, arg in enumerate(args):
        print("================================================================================")
        print("Positional argument %d" % index)
        print("Type: %s" % type(arg.context['pages']))
        print("================================================================================")
        pp.pprint(arg.context['pages'][0].__dict__)

def register():
#   pelican.signals.initialized.connect(print_interface)
#   pelican.signals.generator_init.connect(print_interface)
#   pelican.signals.page_generator_context.connect(print_interface)
    pelican.signals.page_generator_init.connect(print_interface)
#   pelican.signals.page_generator_finalized.connect(print_interface)
#   pelican.signals.page_generator_finalized.connect(print_context_page)
#   pelican.signals.page_generator_write_page.connect(print_interface)
#   pelican.signals.static_generator_finalized.connect(print_interface)
#   pelican.signals.static_generator_preread.connect(print_interface)
#   pelican.signals.static_generator_context.connect(print_interface)
#   pelican.signals.content_object_init.connect(print_interface)
