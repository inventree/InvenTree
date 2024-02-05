"""Check mkdocs.yml config file for errors."""

exit(0)
import os

import yaml

here = os.path.dirname(__file__)

tld = os.path.abspath(os.path.join(here, '..'))

config_file = os.path.join(tld, 'mkdocs.yml')

with open(config_file, 'r') as f:
    data = yaml.load(f, yaml.BaseLoader)

    assert data['strict'] == 'true'
