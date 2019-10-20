import os
import datetime
import warnings
import subprocess

import yaml

DIR_METADATA = {}
PAGE_METADATA = {}

def pagepath2sourcepath(path_no_ext, pelican_obj, source_ext='md'):
    """Converts a final page or directory path into the source file that
    generated it.

    This is used when a template requires metadata from another page or
    directory.

    Args:
        pelican_obj: Some Pelican object passed by the plugin hook
        path (str): Path to a final generated file (e.g., ``path_no_ext = electronics/555``)
        source_ext (str): Look for source files that match path_no_ext's
            filename but have this extension instead.

    Returns:
        str: Path to the file that resulted in path
    """
    if path_no_ext.startswith(pelican_obj.settings['SITEURL']):
        path_no_ext = path_no_ext[len(pelican_obj.settings['SITEURL']):]
    debug_str = ""
    path_no_ext = path_no_ext.lstrip(os.sep)

    # if we are looking for a file that has already been generated, then we can
    # get its definitive source path
    if 'context' in pelican_obj.__dict__:
        for rel_source_path, page_obj in pelican_obj.context.get('generated_content', {}).items():
            debug_str += "  checking %s == %s\n" % (page_obj.path_no_ext, path_no_ext)
            if page_obj.path_no_ext == path_no_ext:
                return rel_source_path
    debug_str += "did not find using generated_content\n"

    # if the file has not been generated, or it is a directory, we have to try
    # to find a file that looks like what Pelican might've used to generate it
    for page_path in pelican_obj.settings['PAGE_PATHS']:
        # try finding a matching directory
        # path_no_ext = sysadmin-howtos
        # test_path = /Users/glock/src/git/pelican-page/content/pages by scanning directories
        test_path = os.path.join(pelican_obj.settings['PATH'], page_path, path_no_ext)
        debug_str += "  checking %s == %s\n" % (path_no_ext, test_path)
        if os.path.exists(test_path):
            return test_path

        # try finding a matching markdown file
        test_path = os.path.join(pelican_obj.settings['PATH'], page_path, path_no_ext + "." + source_ext)
        debug_str += "  checking %s == %s\n" % (path_no_ext, test_path)
        if os.path.isfile(test_path):
            return test_path

    raise FileNotFoundError("Heuristics could not find source file for %s\n%s" % (path_no_ext, debug_str))

def get_dir_metadata(path, key=None):
    """Returns directory metadata for given path

    Either loads a directory's metadata and returns it, or reads it from a
    global cache.

    Args:
        path (str): Path to the directory, relative to the Pelican content
            (PATH), for example, ``pages/data-intensive/hadoop``.
        key (str or list): If present, return the metadata attribute
            corresponding to this key.  If a list, search multiple keys and
            return the first that exists.

    Returns:
        dict: Metadata as loaded from the directory's _metadata.yml file
    """
    global DIR_METADATA
    if path not in DIR_METADATA:
        DIR_METADATA[path] = load_dir_metadata(path)

    if isinstance(key, list):
        for _key in key:
            if _key in DIR_METADATA[path]:
                return DIR_METADATA[path].get(_key)
        return None
    elif key:
        return DIR_METADATA[path].get(key)

    return DIR_METADATA[path]

def load_dir_metadata(path):
    """Extracts metadata from a directory

    Extends page metadata into directories by looking for a yaml file called _metadata.yml in a directory

    Args:
        path (str): Path for which index should be built

    Returns:
        Whatever structure is prescribed in the Markdown's metadata header
    """
    meta_file = os.path.join(path, '_metadata.yml')
    if os.path.isfile(meta_file):
        meta = yaml.load(open(meta_file, 'r'), Loader=yaml.SafeLoader)
    else:
        meta = {
            'title': os.path.basename(path).replace('_', ' ').replace('-', ' ').title()
        }

    return meta

def get_page_metadata(path, key=None):
    """Returns page's metadata for given page path

    Either loads a page's metadata and returns it, or reads it from a global
    cache.

    Args:
        path (str): Path to the source markdown file relative to the Pelican
            content (PATH), for example, ``pages/data-intensive/hadoop/on-hpc.md``.
        key (str or list): If present, return the metadata attribute
            corresponding to this key.  If a list, search multiple keys and
            return the first that exists.

    Returns:
        dict: Metadata as loaded from the page's markdown header
    """
    global PAGE_METADATA
    if path not in PAGE_METADATA:
        PAGE_METADATA[path] = load_page_metadata(path)

    if isinstance(key, list):
        for _key in key:
            if _key in PAGE_METADATA[path]:
                return PAGE_METADATA[path].get(_key)
        return None
    elif key:
        return PAGE_METADATA[path].get(key)

    return PAGE_METADATA[path]

def load_page_metadata(path):
    """Extracts metadata from a markdown page

    Reads the header from a Pelican-formatted Markdown file.  Currently only
    supports the case where this metadata is written in YAML; should eventually
    use the Pelican built-in metadata extractor, but doing so requires figuring
    out where we can access the instantiated Pelican object.

    Args:
        path (str): Path for which index should be built

    Returns:
        Whatever structure is prescribed in the Markdown's metadata header
    """
    if not os.path.isfile(path):
        return {}

    metadata_str = None
    for line in open(path, 'r'):
        if line.strip() == "---":
            if metadata_str is not None:
                break
            metadata_str = ""
        elif metadata_str is not None:
            metadata_str += line
    if not metadata_str:
        warnings.warn("No metadata found in " + path)
        metadata_str = "title: %s" % os.path.basename(path[:-3]).replace('-', ' ').title()

    return yaml.load(metadata_str, Loader=yaml.SafeLoader)

def get_git_mtime(path):
    def _scrape_date(lines):
        for line in lines.decode().splitlines():
            if line.startswith('Date'):
                date_str = line.split(None, 1)[-1]
                return datetime.datetime.strptime(date_str, "%c %z")
        return None

    ret = None
    if path is not None:
        try:
            ret = _scrape_date(subprocess.check_output(['git', 'log', path]))
        except subprocess.CalledProcessError:
            pass

    if not ret:
        ret = _scrape_date(subprocess.check_output(['git', 'log']))

    return ret
