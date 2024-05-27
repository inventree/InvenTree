"""Main entry point for the documentation build process."""

import os
import subprocess
import textwrap

import requests
import yaml


def get_repo_url(raw=False):
    """Return the repository URL for the current project."""
    mkdocs_yml = os.path.join(os.path.dirname(__file__), 'mkdocs.yml')

    with open(mkdocs_yml, 'r') as f:
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
        with open(CACHE_FILE, 'r') as f:
            cache = f.read().splitlines()

        if url in cache:
            return True

    attempts = 5

    while attempts > 0:
        response = requests.head(url, timeout=5000)
        if response.status_code == 200:
            # Update the cache file
            with open(CACHE_FILE, 'a') as f:
                f.write(f'{url}\n')

            return True

        attempts -= 1

    return False


def define_env(env):
    """Define custom environment variables for the documentation build process."""

    @env.macro
    def sourcedir(dirname, branch='master'):
        """Return a link to a directory within the source code repository.

        Arguments:
            - dirname: The name of the directory to link to (relative to the top-level directory)

        Returns:
            - A fully qualified URL to the source code directory on GitHub

        Raises:
            - FileNotFoundError: If the directory does not exist, or the generated URL is invalid
        """
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
    def sourcefile(filename, branch='master', raw=False):
        """Return a link to a file within the source code repository.

        Arguments:
            - filename: The name of the file to link to (relative to the top-level directory)

        Returns:
            - A fully qualified URL to the source code file on GitHub

        Raises:
            - FileNotFoundError: If the file does not exist, or the generated URL is invalid
        """
        if filename.startswith('/'):
            filename = filename[1:]

        # This file exists at ./docs/main.py, so any file we link to must be relative to the top-level directory
        here = os.path.dirname(__file__)
        root = os.path.abspath(os.path.join(here, '..'))

        file_path = os.path.join(root, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f'Source file {filename} does not exist.')

        repo_url = get_repo_url(raw=raw)

        if raw:
            url = f'{repo_url}/{branch}/{filename}'
        else:
            url = f'{repo_url}/blob/{branch}/{filename}'

        # Check that the URL exists before returning it
        if not check_link(url):
            raise FileNotFoundError(f'URL {url} does not exist.')

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

        with open(output, 'r') as f:
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
    def includefile(filename: str, title: str, format: str = ''):
        """Include a file in the documentation, in a 'collapse' block.

        Arguments:
            - filename: The name of the file to include (relative to the top-level directory)
            - title:
        """
        here = os.path.dirname(__file__)
        path = os.path.join(here, '..', filename)
        path = os.path.abspath(path)

        if not os.path.exists(path):
            raise FileNotFoundError(f'Required file {path} does not exist.')

        with open(path, 'r') as f:
            content = f.read()

        data = f'??? abstract "{title}"\n\n'
        data += f'    ```{format}\n'
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

        return includefile(fn, f'Template: {base}', format='html')
