"""Extract API schema and split into smaller subsections."""

import argparse
import os
import re
import textwrap

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

    !!! tip "API Schema History"
        We track API schema changes, and provide a snapshot of each API schema version in the [API schema repository](https://github.com/inventree/schema/).

    ## API Schema File

    The API schema file is available for download, and can be used for generating client libraries, or for testing API endpoints.

    ## API Schema Documentation

    API schema documentation is split into the following categories:

    | Category | Description |
    | --- | --- |
    """

    output = textwrap.dedent(output).strip() + '\n'

    for key, value in SPECIAL_PATHS.items():
        output += f'| [{value}](./schema/{key}.md) | {value} |\n'

    output += '| [General](./schema/general.md) | General API endpoints |\n'

    output += '\n'

    output_file = os.path.join(os.path.dirname(__file__), OUTPUT_DIR, '..', 'schema.md')

    print('Writing index file to:', output_file)

    with open(output_file, 'w') as f:
        f.write(output)


def extract_refs(data: dict, components: dict) -> list:
    """Extract a list of refs from the provided paths dict.

    The refs are located like so:
    <path>:<method>:responses:<status>:content:application/json:schema:$ref

    Also, the referenced components might reference *sub* components,
    so we need to do this step recursively.

    """
    pattern = r"'?\$ref'?: '#\/components\/schemas\/(\S+)'"

    # First, extract the results from the paths data dict
    matches = re.findall(pattern, str(data))

    refs = list(matches)

    # Next, extract additional refs from the components dict
    # Note that the components dict may reference other components

    idx = 0

    while idx < len(refs):
        ref = refs[idx]

        schema = components.get('schemas', {}).get(ref, None)

        if schema:
            # Search for additional refs
            matches = re.findall(pattern, str(schema))

            for match in matches:
                if match not in refs:
                    refs.append(match)

        idx += 1

    # Return a dict only of the extracted refs
    schemas = {ref: components['schemas'][ref] for ref in refs}

    return schemas


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

        components = data.get('components', {})

        # Extract only the schemas relating to the provided paths
        path_schemas = extract_refs(value, components)

        for k, v in data.items():
            if k == 'components':
                v = v.copy()
                v['schemas'] = path_schemas

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
