"""Extract API schema and split into smaller subsections."""

import argparse
import os
import textwrap

import yaml
from render_schema import SchemaRenderer

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
    'importer': 'Data Importing',
    'label': 'Label Printing',
    'machine': 'External Machine Management',
    'order': 'External Order Management',
    'part': 'Parts and Part Categories',
    'plugins': 'Plugin Functionality',
    'pricing': 'Part and Stock Pricing',
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

    parts = path.split('/')
    key = parts[1] if len(parts) > 1 else parts[0]

    if key in SPECIAL_PATHS:
        return key

    return GENERAL_PATH


def generate_schema_file(key: str, renderer: SchemaRenderer, paths: dict) -> None:
    """Render the API documentation page for the provided key."""
    description = SPECIAL_PATHS.get(key, 'General API Endpoints')

    output = renderer.render_page(description, paths)

    output_file = os.path.join(os.path.dirname(__file__), OUTPUT_DIR, f'{key}.md')
    output_file = os.path.abspath(output_file)

    print('Writing schema file to:', output_file)

    # Generated pages are not tracked in git, so the directory may not exist yet
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)


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

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)


def parse_api_file(filename: str):
    """Parse the input API file, and render it as a set of smaller documentation pages.

    The intent is to make the API schema easier to peruse on the documentation.
    """
    with open(filename, encoding='utf-8') as f:
        data = yaml.safe_load(f)

    top_level_paths = {}

    for path, methods in data['paths'].items():
        tlp = top_level_path(path)
        top_level_paths.setdefault(tlp, {})[path] = methods

    # The renderer uses the complete schema, so all references can be resolved
    renderer = SchemaRenderer(data)

    # Generate output files
    for key, value in top_level_paths.items():
        generate_schema_file(key, renderer, value)

    # Finally, generate an index file for the API schema
    generate_index_file(data['info']['version'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='Input API schema file (.yml)')

    args = parser.parse_args()

    parse_api_file(args.input)
