"""Main entry point for the documentation build process."""

import json
import logging
import os
import subprocess
import textwrap
from pathlib import Path
from typing import Literal, Optional

import requests
import yaml

# Debugging output - useful for diagnosing CI build issues
print('loading ./docs/main.py...')

logging.getLogger('openapidocs').setLevel(logging.ERROR)

# Print out some useful debugging information
# Ref: https://docs.readthedocs.io/en/stable/reference/environment-variables.html
for key in [
    'GITHUB_ACTIONS',
    'GITHUB_REF',
    'READTHEDOCS',
    'READTHEDOCS_GIT_IDENTIFIER',
    'READTHEDOCS_GIT_CLONE_URL',
    'READTHEDOCS_GIT_COMMIT_HASH',
    'READTHEDOCS_PROJECT',
    'READTHEDOCS_VERSION',
    'READTHEDOCS_VERSION_NAME',
    'READTHEDOCS_VERSION_TYPE',
]:
    val = os.environ.get(key, None) or '-- MISSING --'
    print(f' - {key}: {val}')

# Cached settings dict values
global GLOBAL_SETTINGS
global USER_SETTINGS
global TAGS
global FILTERS
global REPORT_CONTEXT

# Read in the InvenTree settings file
here = Path(__file__).parent

gen_base = here.joinpath('generated')

# File where we expect to find the settings definitions
settings_file = gen_base.joinpath('inventree_settings.json')

# File where we will *store* information on the settings we have observed
observed_settings_file = gen_base.joinpath('observed_settings.json')

# Overwrite the observed settings file
with open(observed_settings_file, 'w', encoding='utf-8') as f:
    data = {'global': {}, 'user': {}}

    # Write an empty dict to the file
    # This is used to track which settings we have observed during the build process
    f.write(json.dumps(data, indent=4))

with open(settings_file, encoding='utf-8') as sf:
    settings = json.load(sf)

    GLOBAL_SETTINGS = settings['global']
    USER_SETTINGS = settings['user']

# Tags
with open(gen_base.joinpath('inventree_tags.yml'), encoding='utf-8') as f:
    TAGS = yaml.load(f, yaml.BaseLoader)
# Filters
with open(gen_base.joinpath('inventree_filters.yml'), encoding='utf-8') as f:
    FILTERS = yaml.load(f, yaml.BaseLoader)
# Report context
with open(gen_base.joinpath('inventree_report_context.json'), encoding='utf-8') as f:
    REPORT_CONTEXT = json.load(f)


def get_repo_url(raw=False):
    """Return the repository URL for the current project."""
    mkdocs_yml = here.joinpath('mkdocs.yml')

    with open(mkdocs_yml, encoding='utf-8') as f:
        mkdocs_config = yaml.load(f, yaml.BaseLoader)
        repo_name = mkdocs_config['repo_name']

    if raw:
        return f'https://raw.githubusercontent.com/{repo_name}'
    else:
        return f'https://github.com/{repo_name}'


def check_link(url) -> bool:
    """Check that a provided URL is valid.

    We allow a number attempts and a lengthy timeout,
    as we do not want false negatives.
    """
    CACHE_FILE = gen_base.joinpath('url_cache.txt')

    # Keep a local cache file of URLs we have already checked
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding='utf-8') as f:
            cache = f.read().splitlines()

        if url in cache:
            return True

    attempts = 5

    while attempts > 0:
        response = requests.head(url, timeout=5000)

        # Ensure GH is not causing issues
        if response.status_code in (200, 429):
            # Update the cache file
            with open(CACHE_FILE, 'a', encoding='utf-8') as f:
                f.write(f'{url}\n')

            return True

        attempts -= 1

        print(f'URL check failed with status code {response.status_code}')

    return False


def get_build_environment() -> str:
    """Returns the branch we are currently building on, based on the environment variables of the various CI platforms."""
    # Check if we are in ReadTheDocs
    if os.environ.get('READTHEDOCS') == 'True':
        for var in ['READTHEDOCS_GIT_COMMIT_HASH', 'READTHEDOCS_GIT_IDENTIFIER']:
            if val := os.environ.get(var):
                return val
    # We are in GitHub Actions
    elif os.environ.get('GITHUB_ACTIONS') == 'true':
        return os.environ.get('GITHUB_REF')

    # Default to 'master' branch
    return 'master'


def define_env(env):
    """Define custom environment variables for the documentation build process."""
    config = env.config
    assets_dir = config.get('assets_dir', None)

    if assets_dir is None:
        # Construct the assets directory based on the current build environment
        rtd_version = os.environ.get('READTHEDOCS_VERSION')
        rtd_language = os.environ.get('READTHEDOCS_LANGUAGE')

        if rtd_version and rtd_language:
            assets_dir = f'/{rtd_language}/{rtd_version}/assets'
        else:
            assets_dir = '/assets'

    @env.macro
    def sourcedir(dirname: str, branch=None):
        """Return a link to a directory within the source code repository.

        Arguments:
            dirname: The name of the directory to link to (relative to the top-level directory)
            branch: The branch of the repository to link to (defaults to the current build environment)

        Returns:
            A fully qualified URL to the source code directory on GitHub

        Raises:
            FileNotFoundError: If the directory does not exist, or the generated URL is invalid
        """
        if branch == None:
            branch = get_build_environment()

        if dirname.startswith('/'):
            dirname = dirname[1:]

        # This file exists at ./docs/main.py, so any directory we link to must be relative to the top-level directory
        directory = here.parent.joinpath(dirname)
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f'Source directory {dirname} does not exist.')

        repo_url = get_repo_url()

        url = f'{repo_url}/tree/{branch}/{dirname}'

        # Check that the URL exists before returning it
        if not check_link(url):
            raise FileNotFoundError(f'URL {url} does not exist.')

        return url

    @env.macro
    def sourcefile(filename, branch=None, raw=False):
        """Return a link to a file within the source code repository.

        Arguments:
            filename: The name of the file to link to (relative to the top-level directory)
            branch: The branch of the repository to link to (defaults to the current build environment)
            raw: If True, return the raw URL to the file (defaults to False)

        Returns:
            A fully qualified URL to the source code file on GitHub

        Raises:
            FileNotFoundError: If the file does not exist, or the generated URL is invalid
        """
        if branch == None:
            branch = get_build_environment()

        if filename.startswith('/'):
            filename = filename[1:]

        # This file exists at ./docs/main.py, so any file we link to must be relative to the top-level directory
        file_path = here.parent.joinpath(filename)
        if not file_path.exists():
            raise FileNotFoundError(f'Source file {filename} does not exist.')

        # Construct repo URL
        repo_url = get_repo_url(raw=False)
        url = f'{repo_url}/blob/{branch}/{filename}'

        # Check that the URL exists before returning it
        if not check_link(url):
            raise FileNotFoundError(f'URL {url} does not exist.')

        if raw:
            # If requesting the 'raw' URL, take this into account here...
            repo_url = get_repo_url(raw=True)
            url = f'{repo_url}/{branch}/{filename}'

        return url

    @env.macro
    def invoke_commands():
        """Provides an output of the available commands."""
        tasks = here.parent.joinpath('tasks.py')
        output = gen_base.joinpath('invoke-commands.txt')

        command = f'invoke -f {tasks} --list > {output}'

        assert subprocess.call(command, shell=True) == 0

        with open(output, encoding='utf-8') as f:
            content = f.read()

        return content

    @env.macro
    def listimages(subdir):
        """Return a listing of all asset files in the provided subdir."""
        directory = here.joinpath('docs', 'assets', 'images', subdir)

        assets = []

        allowed = ['.png', '.jpg']

        for asset in directory.iterdir():
            if any(str(asset).endswith(x) for x in allowed):
                assets.append(str(subdir / asset.relative_to(directory)))

        return assets

    @env.macro
    def includefile(filename: str, title: str, fmt: str = ''):
        """Include a file in the documentation, in a 'collapse' block.

        Arguments:
            filename: The name of the file to include (relative to the top-level directory)
            title: The title of the collapse block in the documentation
            fmt: The format of the included file (e.g., 'python', 'html', etc.)
        """
        path = here.parent.joinpath(filename)

        if not path.exists():
            raise FileNotFoundError(f'Required file {path} does not exist.')

        with open(path, encoding='utf-8') as f:
            content = f.read()

        data = f'??? abstract "{title}"\n\n'
        data += f'    ```{fmt}\n'
        data += textwrap.indent(content, '    ')
        data += '\n\n'
        data += '    ```\n\n'

        return data

    @env.macro
    def templatefile(filename):
        """Include code for a provided template file."""
        base = Path(filename).name
        fn = Path('src', 'backend', 'InvenTree', 'report', 'templates', filename)

        return includefile(fn, f'Template: {base}', fmt='html')

    def observe_setting(key: str, group: str):
        """Record that a particular setting has been observed.

        This is used to ensure that all settings are documented in the generated documentation.

        Arguments:
            key: The name of the setting to observe
            group: The group of the setting (e.g. 'global', 'user')
        """
        # Read the observed settings file
        with open(observed_settings_file, encoding='utf-8') as f:
            data = json.load(f)

        if group not in data:
            data[group] = {}

        data[group][key] = True

        # Write the updated data back to the file
        with open(observed_settings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    @env.macro
    def rendersetting(key: str, setting: dict, short: bool = False):
        """Render a provided setting object into a table row.

        Arguments:
            key: The name of the setting to extract information for.
            setting: The setting object to render.
            short: If True, return a short version of the setting (default: False)
        """
        name = setting['name']
        description = setting['description']
        default = setting.get('default')
        units = setting.get('units')

        default = f'`{default}`' if default else ''
        units = f'`{units}`' if units else ''

        if short:
            return f'<span title="{key}"><strong>{name}</strong></span>'

        return f'| <div title="{key}"><strong>{name}</strong></div> | {description} | {default} | {units} |'

    @env.macro
    def globalsetting(key: str, short: bool = False):
        """Extract information on a particular global setting.

        Arguments:
            key: The name of the global setting to extract information for.
            short: If True, return a short version of the setting (default: False)
        """
        global GLOBAL_SETTINGS
        setting = GLOBAL_SETTINGS[key]

        # Settings are only 'observed' if they are displayed in full
        if not short:
            observe_setting(key, 'global')

        return rendersetting(key, setting, short=short)

    @env.macro
    def usersetting(key: str, short: bool = False):
        """Extract information on a particular user setting.

        Arguments:
            key: The name of the user setting to extract information for.
            short: If True, return a short version of the setting (default: False)
        """
        global USER_SETTINGS
        setting = USER_SETTINGS[key]

        # Settings are only 'observed' if they are displayed in full
        if not short:
            observe_setting(key, 'user')

        return rendersetting(key, setting, short=short)

    @env.macro
    def tags_and_filters():
        """Return a list of all tags and filters."""
        global TAGS
        global FILTERS

        ret_data = ''
        for ref in [['Tags', TAGS], ['Filters', FILTERS]]:
            ret_data += f'### {ref[0]}\n\n| Namespace | Name | Description |\n| --- | --- | --- |\n'
            for value in ref[1]:
                title = (
                    value['title']
                    .replace('\n', ' ')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                )
                ret_data += f'| {value["library"]} | {value["name"]} | {title} |\n'
            ret_data += '\n'
        ret_data += '\n'

        return ret_data

    @env.macro
    def report_context(type_: Literal['models', 'base'], model: str):
        """Extract information on a particular report context."""
        global REPORT_CONTEXT

        context = REPORT_CONTEXT.get(type_).get(model)

        ret_data = '| Variable | Type | Description |\n| --- | --- | --- |\n'
        for k, v in context['context'].items():
            ret_data += f'| {k} | `{v["type"]}` | {v["description"]} |\n'

        return ret_data

    @env.macro
    def icon(
        source: str,
        size: str = '20px',
        color: Optional[str] = None,
        title: Optional[str] = None,
    ):
        """Return a tabler icon for a given source.

        Arguments:
            source: The name of the icon to display (e.g. 'check', 'cross', etc.)
            size: The size of the icon (default: 20px)
            color: The color of the icon (default: None)
            title: The title of the icon (default: None)

        Requires CSS to be loaded from:
        https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.31.0/dist/tabler-icons.min.css
        """
        c = f' color: {color};' if color else ''
        t = f' <i>{title}</i>' if title else ''

        return f"<i class='ti ti-{source}' style='font-size: {size};{c}'></i>{t}"

    @env.macro
    def image(
        source: str,
        title: Optional[str] = '',
        iid: Optional[str] = '',
        alt: Optional[str] = '',
        base: Optional[str] = '',
        maxwidth: Optional[str] = '',
        maxheight: Optional[str] = '',
    ):
        """Render an image within the documentation.

        Arguments:
            title: The title of the image (default: '')
            source: The name of the image to display (e.g. 'check', 'cross', etc.)
            iid: The ID of the image (default: '')
            alt: The alt text for the image (default: '')
            base: The base directory for the image (default: './assets/images/')
            maxwidth: The maximum width of the image (default: '')
            maxheight: The maximum height of the image (default: '')

        - This will render an image which can be clicked on to expand to full size.
        - It will also validate that the image exists in the specified directory.

        The image must be located in the './docs/assets/images/' directory
        """
        # Allow external images too - without validation
        if source.startswith('http'):
            img = source
        else:
            basedir = os.path.dirname(__file__)
            basedir = os.path.join(basedir, 'docs', 'assets', 'images')

            if base:
                basedir = os.path.abspath(os.path.join(basedir, base))
            filename = os.path.join(basedir, source)

            if not os.path.exists(filename):
                raise FileNotFoundError(f'Image {filename} does not exist.')

            # Now, create a proper URL to the image
            img = os.path.join(assets_dir, 'images', base, source)

        if not title:
            title = os.path.splitext(source)[0]

        if not iid:
            iid = title.replace(' ', '_').replace('-', '_')

        if not alt:
            alt = iid

        styles = []

        if maxwidth:
            styles.append(f'max-width: {maxwidth};')
        if maxheight:
            styles.append(f'max-height: {maxheight};')

        style = f"style='{' '.join(styles)}' " if styles else ''

        return textwrap.dedent(f"""
        <figure class='image image-inventree'>
            <a href='#{iid}'>
                <img class='img-inline' src='{img}' alt='{alt}' title='{title}' {style}/>
            </a>
            <a href='#_' class='overlay' id='{iid}'>
                <img src='{img}' alt='{alt}' />
            </a>
        </figure>
        """)
