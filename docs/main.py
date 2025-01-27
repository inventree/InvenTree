"""Main entry point for the documentation build process."""

import json
import os
import subprocess
import textwrap

import requests
import yaml

# Debugging output - useful for diagnosing CI build issues
print('loading ./docs/main.py...')

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

# Read in the InvenTree settings file
here = os.path.dirname(__file__)
settings_file = os.path.join(here, 'inventree_settings.json')

with open(settings_file, encoding='utf-8') as sf:
    settings = json.load(sf)

    GLOBAL_SETTINGS = settings['global']
    USER_SETTINGS = settings['user']

# Tags
with open(os.path.join(here, 'inventree_tags.yml'), encoding='utf-8') as f:
    TAGS = yaml.load(f, yaml.BaseLoader)
# Filters
with open(os.path.join(here, 'inventree_filters.yml'), encoding='utf-8') as f:
    FILTERS = yaml.load(f, yaml.BaseLoader)


def get_repo_url(raw=False):
    """Return the repository URL for the current project."""
    mkdocs_yml = os.path.join(os.path.dirname(__file__), 'mkdocs.yml')

    with open(mkdocs_yml, encoding='utf-8') as f:
        mkdocs_config = yaml.safe_load(f)
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
    CACHE_FILE = os.path.join(os.path.dirname(__file__), 'url_cache.txt')

    # Keep a local cache file of URLs we have already checked
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            cache = f.read().splitlines()

        if url in cache:
            return True

    print(f'Checking external URL: {url}')

    attempts = 5

    while attempts > 0:
        response = requests.head(url, timeout=5000)
        if response.status_code == 200:
            # Update the cache file
            with open(CACHE_FILE, 'a', encoding='utf-8') as f:
                f.write(f'{url}\n')

            return True

        attempts -= 1

        print(f' - URL check failed with status code {response.status_code}')

    return False


def get_build_enviroment() -> str:
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

    @env.macro
    def sourcedir(dirname, branch=None):
        """Return a link to a directory within the source code repository.

        Arguments:
            - dirname: The name of the directory to link to (relative to the top-level directory)

        Returns:
            - A fully qualified URL to the source code directory on GitHub

        Raises:
            - FileNotFoundError: If the directory does not exist, or the generated URL is invalid
        """
        if branch == None:
            branch = get_build_enviroment()

        if dirname.startswith('/'):
            dirname = dirname[1:]

        # This file exists at ./docs/main.py, so any directory we link to must be relative to the top-level directory
        here = os.path.dirname(__file__)
        root = os.path.abspath(os.path.join(here, '..'))

        directory = os.path.join(root, dirname)
        directory = os.path.abspath(directory)

        if not os.path.exists(directory) or not os.path.isdir(directory):
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
            - filename: The name of the file to link to (relative to the top-level directory)

        Returns:
            - A fully qualified URL to the source code file on GitHub

        Raises:
            - FileNotFoundError: If the file does not exist, or the generated URL is invalid
        """
        if branch == None:
            branch = get_build_enviroment()

        if filename.startswith('/'):
            filename = filename[1:]

        # This file exists at ./docs/main.py, so any file we link to must be relative to the top-level directory
        here = os.path.dirname(__file__)
        root = os.path.abspath(os.path.join(here, '..'))

        file_path = os.path.join(root, filename)

        if not os.path.exists(file_path):
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
        here = os.path.dirname(__file__)
        base = os.path.join(here, '..')
        base = os.path.abspath(base)
        tasks = os.path.join(base, 'tasks.py')
        output = os.path.join(here, 'invoke-commands.txt')

        command = f'invoke -f {tasks} --list > {output}'

        assert subprocess.call(command, shell=True) == 0

        with open(output, encoding='utf-8') as f:
            content = f.read()

        return content

    @env.macro
    def listimages(subdir):
        """Return a listing of all asset files in the provided subdir."""
        here = os.path.dirname(__file__)

        directory = os.path.join(here, 'docs', 'assets', 'images', subdir)

        assets = []

        allowed = ['.png', '.jpg']

        for asset in os.listdir(directory):
            if any(asset.endswith(x) for x in allowed):
                assets.append(os.path.join(subdir, asset))

        return assets

    @env.macro
    def includefile(filename: str, title: str, fmt: str = ''):
        """Include a file in the documentation, in a 'collapse' block.

        Arguments:
            - filename: The name of the file to include (relative to the top-level directory)
            - title:
            - fmt:
        """
        here = os.path.dirname(__file__)
        path = os.path.join(here, '..', filename)
        path = os.path.abspath(path)

        if not os.path.exists(path):
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
        base = os.path.basename(filename)
        fn = os.path.join(
            'src', 'backend', 'InvenTree', 'report', 'templates', filename
        )

        return includefile(fn, f'Template: {base}', fmt='html')

    @env.macro
    def rendersetting(key: str, setting: dict):
        """Render a provided setting object into a table row."""
        name = setting['name']
        description = setting['description']
        default = setting.get('default')
        units = setting.get('units')

        default = f'`{default}`' if default else ''
        units = f'`{units}`' if units else ''

        return (
            f'| <div title="{key}">{name}</div> | {description} | {default} | {units} |'
        )

    @env.macro
    def globalsetting(key: str):
        """Extract information on a particular global setting.

        Arguments:
            - key: The name of the global setting to extract information for.
        """
        global GLOBAL_SETTINGS
        setting = GLOBAL_SETTINGS[key]

        return rendersetting(key, setting)

    @env.macro
    def usersetting(key: str):
        """Extract information on a particular user setting.

        Arguments:
            - key: The name of the user setting to extract information for.
        """
        global USER_SETTINGS
        setting = USER_SETTINGS[key]

        return rendersetting(key, setting)

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
