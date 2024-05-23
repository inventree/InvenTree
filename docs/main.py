"""Main entry point for the documentation build process."""

import os
import textwrap


def define_env(env):
    """Define custom environment variables for the documentation build process."""

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
