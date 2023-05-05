#!/bin/bash

# create folders
mkdir -p /workspaces/InvenTree/dev/{commandhistory,plugins}
cd /workspaces/InvenTree

# create venv
python3 -m venv dev/venv
. dev/venv/bin/activate

# Avoiding Dubious Ownership in Dev Containers for setup commands that use git
git config --global --add safe.directory /workspaces/InvenTree

# setup InvenTree server
pip install invoke
inv update
inv setup-dev

# remove existing gitconfig created by "Avoiding Dubious Ownership" step
# so that it gets copyied from host to the container to have your global 
# git config in container
rm -f /home/vscode/.gitconfig
