#!/bin/bash

# Avoiding Dubious Ownership in Dev Containers for setup commands that use git
# Note that the local workspace directory is passed through as the first argument $1
git config --global --add safe.directory $1

# create folders
mkdir -p $1/dev/{commandhistory,plugins}
cd $1

# create venv
python3 -m venv dev/venv
. dev/venv/bin/activate

# setup InvenTree server
pip install invoke
invoke update --no-frontend
invoke setup-dev
invoke frontend-install

# remove existing gitconfig created by "Avoiding Dubious Ownership" step
# so that it gets copied from host to the container to have your global
# git config in container
rm -f /home/vscode/.gitconfig
