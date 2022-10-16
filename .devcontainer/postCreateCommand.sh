#!/bin/bash

# create folders
mkdir -p /workspaces/InvenTree/dev/{commandhistory,plugins}
cd /workspaces/InvenTree

# create venv
python3 -m venv dev/venv
. dev/venv/bin/activate

# setup inventree server
pip install invoke
inv update
inv setup-dev
