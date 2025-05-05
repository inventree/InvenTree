"""Custom mkdocs hooks, using the mkdocs-simple-hooks plugin."""

import json
import os
import re
from datetime import datetime
from distutils.version import StrictVersion
from pathlib import Path

import requests

here = Path(__file__).parent


def fetch_rtd_versions():
    """Get a list of RTD docs versions to build the version selector."""
    print('Fetching documentation versions from ReadTheDocs')

    versions = []

    def make_request(url, headers):
        """Make a single request to the RTD API."""
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f'Error fetching RTD versions: {response.status_code}')
            return

        data = json.loads(response.text)

        for entry in data['results']:
            slug = entry['slug']
            ref = entry['ref']
            url = entry['urls']['documentation']
            aliases = []

            if ref is not None:
                aliases.append(slug)

            version = ref or slug

            if version == 'latest':
                continue

            versions.append({'version': version, 'title': version, 'aliases': aliases})

        if data['next']:
            make_request(data['next'], headers)

    # Fetch the list of versions from the RTD API
    token = os.environ.get('RTD_TOKEN', None)
    if token:
        headers = {'Authorization': f'Token {token}'}
        url = 'https://readthedocs.org/api/v3/projects/inventree/versions/?active=true&limit=50'
        make_request(url, headers)
    else:
        print('No RTD token found - skipping RTD version fetch')

    # Sort versions by version number
    versions = sorted(versions, key=lambda x: StrictVersion(x['version']), reverse=True)

    # Add "latest" version first
    if not any(x['title'] == 'latest' for x in versions):
        versions.insert(
            0,
            {
                'title': 'Development',
                'version': 'latest',
                'aliases': ['main', 'latest', 'development'],
            },
        )

    # Ensure we have the 'latest' version
    current_version = os.environ.get('READTHEDOCS_VERSION', None)

    if current_version and not any(x['title'] == current_version for x in versions):
        versions.append({
            'version': current_version,
            'title': current_version,
            'aliases': [],
        })

    output_filename = here.joinpath('versions.json')

    print('Discovered the following versions:')
    print(versions)

    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(versions, file, indent=2)


def get_release_data():
    """Return InvenTree release information.

    - First look to see if 'releases.json' file exists
    - If data does not exist in this file, request via the github API
    """
    json_file = here.parent.joinpath('generated', 'releases.json')

    releases = []

    if json_file.exists():
        # Release information has been cached to file

        print("Loading release information from 'releases.json'")
        with open(json_file, encoding='utf-8') as f:
            return json.loads(f.read())

    # Download release information via the GitHub API
    print('Fetching InvenTree release information from api.github.com:')
    releases = []

    # Keep making API requests until we run out of results
    page = 1

    while 1:
        url = f'https://api.github.com/repos/inventree/inventree/releases?page={page}&per_page=150'

        attempts = 5

        while attempts > 0:
            attempts -= 1

            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                break

        assert response.status_code == 200, (
            f'Failed to fetch release data: {response.status_code} - {url}'
        )

        data = json.loads(response.text)

        if len(data) == 0:
            break

        for item in data:
            releases.append(item)

        page += 1

    # Cache these results to file
    with open(json_file, 'w', encoding='utf-8') as f:
        print("Saving release information to 'releases.json'")
        f.write(json.dumps(releases))

    return releases


def on_config(config, *args, **kwargs):
    """Run when the mkdocs config is loaded.

    We want to be able to provide a *dynamic* config.site_url parameter to mkdocs,
    which tells it the base url, e.g.

    - https://readthedocs.io/en/latest
    - https://readthedocs.io/de/0.5.1

    Further, we need to know if we are building on readthedocs at all!

    readthedocs provides some environment variables:
    - https://docs.readthedocs.io/en/stable/builds.html#build-environment

    We can use these to determine (at run time) where we are hosting
    """
    rtd = os.environ.get('READTHEDOCS', None)

    # Note: version selection is handled by RTD internally
    # Check for 'versions.json' file
    # If it does not exist, we need to fetch it from the RTD API
    # if here.joinpath('versions.json').exists():
    #    print("Found 'versions.json' file")
    # else:
    #    fetch_rtd_versions()

    if rtd:
        rtd_version = os.environ.get('READTHEDOCS_VERSION')
        rtd_language = os.environ.get('READTHEDOCS_LANGUAGE')

        site_url = f'https://docs.inventree.org/{rtd_language}/{rtd_version}'
        assets_dir = f'/{rtd_language}/{rtd_version}/assets'

        print('Building within READTHEDOCS environment!')
        print(f' - Version: {rtd_version}')
        print(f' - Language: {rtd_language}')

        # Add *all* readthedocs related keys
        readthedocs = {}

        for key in os.environ:
            if key.startswith('READTHEDOCS_'):
                k = key.replace('READTHEDOCS_', '').lower()
                readthedocs[k] = os.environ[key]

        # Supply this to the context
        config['readthedocs'] = readthedocs

        # Determine if we want to display a 'version' banner
        # Basically we do, *unless* we are displaying the "stable" version
        config['version_banner'] = rtd_version != 'stable'

    else:
        print("'READTHEDOCS' environment variable not found")
        print('Building for localhost configuration!')

        assets_dir = '/assets'
        site_url = config['site_url']

        config['readthedocs'] = False

    config['assets_dir'] = assets_dir
    config['site_url'] = site_url

    print(f"config.site_url = '{site_url}'")
    print(f"config.assets_dir = '{assets_dir}'")

    release_data = get_release_data()

    releases = []

    for item in release_data:
        # Ignore draft releases
        if item['draft']:
            continue

        tag = item['tag_name']

        # Check that the tag is formatted correctly
        re.match(r'^\d+\.\d+\.\d+$', tag)

        if not re.match:
            print(f'Found badly formatted release: {tag}')
            continue

        # Check if there is a local file with release information
        local_path = here.joinpath('releases', f'{tag}.md')

        if local_path.exists():
            item['local_path'] = local_path

        # Extract the date
        item['date'] = item['published_at'].split('T')[0]

        date = datetime.fromisoformat(item['date'])

        # First tagged docker release was 2021-04-18
        if date > datetime(year=2021, month=4, day=17):
            item['docker'] = True

        # Add a "prefix" so we can split by sub version
        item['prefix'] = '.'.join(tag.split('.')[:-1])

        releases.append(item)

    print(f'- found {len(releases)} releases.')

    # Sort releases by descending date
    config['releases'] = sorted(releases, key=lambda it: it['date'], reverse=True)

    return config
