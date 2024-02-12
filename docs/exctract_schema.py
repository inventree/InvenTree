"""Extract API schema and split into smaller subsections."""

import argparse
import os

import yaml

OUTPUT_DIR = './docs/api/schema/'

# General path
GENERAL_PATH = 'general'

# List of special paths we want to split out
SPECIAL_PATHS = {
    'auth': 'Authorization and Authentication',
    'background-task': 'Background Task Management',
    'barcode': 'Barcode Scanning',
    'bom': 'Bill of Materials',
    'build': 'Build Order Management',
    'company': 'Company Management',
    'label': 'Label Printing',
    'order': 'External Order Management',
    'part': 'Parts and Part Categories',
    'plugins': 'Plugin Functionality',
    'report': 'Report Generation',
    'settings': 'Settings Management',
    'stock': 'Stock and Stock Locations',
    'user': 'User Management',
}


def top_level_path(path: str) -> str:
    """Return the top level path of the input path."""
    path = path.strip()

    if path.startswith('/'):
        path = path[1:]

    if path.endswith('/'):
        path = path[:-1]

    path = path.strip()

    key = path.split('/')[1]

    if key in SPECIAL_PATHS.keys():
        return key

    return GENERAL_PATH


def generate_index_file(version: str):
    """Generate the index file for the API schema."""
    output = f"""
    ---
    title: InvenTree API Schema
    ---

    The InvenTree API is implemented using the [Django REST framework](https://www.django-rest-framework.org).
    The API schema as documented below is generated using the [drf-spectactular](https://github.com/tfranzel/drf-spectacular/) extension.

    ## API Version

    This documentation is for API version: `{version}`

    ## API Schema File

    The API schema file is available for download, and can be used for generating client libraries, or for testing API endpoints.

    ## API Schema Documentation

    API schema documentation is split into the following categories:

    | Category | Description |
    | --- | --- |
    """

    for key, value in SPECIAL_PATHS.items():
        output += f'| [{value}](./schema/{key}.md) | {value} |\n'

    output += '| [General](./schema/general.md) | General API endpoints |\n'

    output += '\n'

    output_file = os.path.join(os.path.dirname(__file__), OUTPUT_DIR, 'schema.md')

    print('Writing index file to:', output_file)

    with open(output_file, 'w') as f:
        f.write(output)


def parse_api_file(filename: str):
    """Parse the input API file, and split into smaller sections.

    The intent is to make the API schema easier to peruse on the documentation.
    """
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)

    paths = data['paths']

    top_level_paths = {}

    for path, methods in paths.items():
        tlp = top_level_path(path)

        if tlp not in top_level_paths:
            top_level_paths[tlp] = {}

        top_level_paths[tlp][path] = methods

    # Generate output files
    for key, value in top_level_paths.items():
        output_file = os.path.join(os.path.dirname(__file__), OUTPUT_DIR, f'{key}.yml')

        output = {}

        output['paths'] = value

        for k, v in data.items():
            if k != 'paths':
                output[k] = v

        print(f'Writing schema file to {output_file}...')

        output_file = os.path.abspath(output_file)

        with open(output_file, 'w') as f:
            yaml.dump(output, f)

    # Finally, generate an index file for the API schema
    generate_index_file(data['info']['version'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='Input API schema file (.yml)')

    args = parser.parse_args()

    parse_api_file(args.input)
