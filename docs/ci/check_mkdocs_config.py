"""Check mkdocs.yml config file for errors."""

import os

import yaml

here = os.path.dirname(__file__)

tld = os.path.abspath(os.path.join(here, '..'))

config_file = os.path.join(tld, 'mkdocs.yml')

with open(config_file, encoding='utf-8') as f:
    data = yaml.load(f, yaml.BaseLoader)

    assert data['strict'] == 'true'
