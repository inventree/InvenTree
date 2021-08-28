"""
Pull 'rendered' copies of the templated JS files down from the  InvenTree server.

These files can then be used for linting and unit testing
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import re
import os
import json
import pathlib
import argparse
import requests
from requests.auth import HTTPBasicAuth


here = os.path.abspath(os.path.dirname(__file__))
js_template_dir = os.path.abspath(os.path.join(here, '..', 'InvenTree', 'templates', 'js'))

js_tmp_dir = os.path.join(here, 'js_tmp')

def get_token(server, username, password):

    url = os.path.join(
        server,
        'api',
        'user',
        'token',
    )

    auth = HTTPBasicAuth(username, password)

    response = requests.get(url, auth=auth, allow_redirects=False)

    data = json.loads(response.text)

    return data['token']


def download_file(url, filename, token):
    """
    Download a single javascript file
    """

    print(f"Downloading '{url}'")

    headers = {
        'AUTHORIZATION': f'Token {token}'
    }

    response = requests.get(
        url,
        allow_redirects=False,
        headers=headers
    )

    output_file = os.path.join(
        js_tmp_dir,
        filename,
    )

    with open(output_file, 'wb') as output:
        output.write(response.content)


def download_js_files(subdir, url, token):
    """
    Returns a flattened list of all javascript files
    """

    d = os.path.join(js_template_dir, subdir)

    files = pathlib.Path(d).rglob('*.js')

    for filename in files:
        js = os.path.basename(filename)

        js_url = os.path.join(url, js)

        download_file(js_url, js, token)

if __name__ == '__main__':

    parser = argparse.ArgumentParser("Download JavaScript files")

    parser.add_argument('-s', '--server', help='InvenTree server', action='store')
    parser.add_argument('-u', '--username', help='Username', action='store')
    parser.add_argument('-p', '--password', help='password', action='store')

    args = parser.parse_args()

    if not os.path.exists(js_tmp_dir):
        os.mkdir(js_tmp_dir)

    auth = HTTPBasicAuth(args.username, args.password)

    # Get an auth token from the server
    token = get_token(args.server, args.username, args.password)

    # Dynamic javascript files
    dynamic_url = os.path.join(args.server, 'js', 'dynamic')

    download_js_files('dynamic', dynamic_url, token)

    # Translated JS files
    i18n_url = os.path.join(args.server, 'js', 'i18n')

    download_js_files("translated", i18n_url, token)