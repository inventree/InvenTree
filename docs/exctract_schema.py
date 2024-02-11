"""Extract API schema and split into smaller subsections."""

import argparse
import os

import yaml

OUTPUT_DIR = './docs/api/schema/'

# General path
GENERAL_PATH = 'general'

# List of special paths we want to split out
SPECIAL_PATHS = [
    'auth',
    'background-task',
    'barcode',
    'bom',
    'build',
    'company',
    'label',
    'order',
    'part',
    'plugins',
    'report',
    'settings',
    'stock',
    'user',
]


def top_level_path(path: str) -> str:
    """Return the top level path of the input path."""
    path = path.strip()

    if path.startswith('/'):
        path = path[1:]

    if path.endswith('/'):
        path = path[:-1]

    path = path.strip()

    key = path.split('/')[1]

    if key in SPECIAL_PATHS:
        return key

    return GENERAL_PATH


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='Input API schema file (.yml)')

    args = parser.parse_args()

    parse_api_file(args.input)
