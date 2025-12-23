#!/bin/bash
set -e

echo "Running postCreateCommand.sh ..."

# Avoiding Dubious Ownership in Dev Containers for setup commands that use git
git config --global --add safe.directory /home/inventree

# create venv
python3 -m venv /home/inventree/dev/venv --system-site-packages --upgrade-deps
. /home/inventree/dev/venv/bin/activate

# remove existing gitconfig created by "Avoiding Dubious Ownership" step
# so that it gets copied from host to the container to have your global
# git config in container
rm -f /home/vscode/.gitconfig

# Fix issue related to CFFI version mismatch
pip uninstall cffi -y
sudo apt remove --purge -y python3-cffi
pip install --no-cache-dir --force-reinstall --ignore-installed cffi

# Upgrade pip
python3 -m pip install --upgrade pip

# Ensure the correct invoke is available
pip3 install --ignore-installed --upgrade invoke Pillow

# install base level packages
pip3 install -Ur contrib/container/requirements.txt

# Run initial InvenTree server setup
invoke update -s

# Configure dev environment
invoke dev.setup-dev

# Install required frontend packages
invoke int.frontend-install
