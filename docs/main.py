"""Main entry point for the documentation build process."""

import os
import textwrap

import requests
import yaml


def get_repo_url():
    """Return the repository URL for the current project."""
    mkdocs_yml = os.path.join(os.path.dirname(__file__), 'mkdocs.yml')

    with open(mkdocs_yml, 'r') as f:
        mkdocs_config = yaml.safe_load(f)
        return mkdocs_config['repo_url']


def define_env(env):
    """Define custom environment variables for the documentation build process."""

    @env.macro
    def sourcefile(filename, branch='master'):
        """Return a link to a file within the source code repository.

        Arguments:
            - filename: The name of the file to link to (relative to the top-level directory)

        Returns:
            - A fully qualified URL to the source code file on GitHub

        Raises:
            - FileNotFoundError: If the file does not exist, or the generated URL is invalid
        """
        # This file exists at ./docs/main.py, so any file we link to must be relative to the top-level directory
        here = os.path.dirname(__file__)
        root = os.path.abspath(os.path.join(here, '..'))

        file_path = os.path.join(root, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f'Source file {filename} does not exist.')

        repo_url = get_repo_url()

        url = f'{repo_url}/blob/{branch}/{filename}'

        # Check that the URL exists before returning it
        response = requests.head(url)

        if response.status_code != 200:
            raise FileNotFoundError(f'URL {url} does not exist.')

        return url

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
    def templatefile(filename):
        """Include code for a provided template file."""
        here = os.path.dirname(__file__)
        template_dir = os.path.join(
            here, '..', 'src', 'backend', 'InvenTree', 'report', 'templates'
        )
        template_file = os.path.join(template_dir, filename)
        template_file = os.path.abspath(template_file)

        basename = os.path.basename(filename)

        if not os.path.exists(template_file):
            raise FileNotFoundError(f'Report template file {filename} does not exist.')

        with open(template_file, 'r') as f:
            content = f.read()

        data = f'??? abstract "Template: {basename}"\n\n'
        data += '    ```html\n'
        data += textwrap.indent(content, '    ')
        data += '\n\n'
        data += '    ```\n\n'

        return data
