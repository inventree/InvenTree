#!/bin/bash
# exit when any command fails
set -e

# Create required directory structure (if it does not already exist)
if [[ ! -d "$INVENTREE_STATIC_ROOT" ]]; then
    echo "Creating directory $INVENTREE_STATIC_ROOT"
    mkdir -p $INVENTREE_STATIC_ROOT
fi

if [[ ! -d "$INVENTREE_MEDIA_ROOT" ]]; then
    echo "Creating directory $INVENTREE_MEDIA_ROOT"
    mkdir -p $INVENTREE_MEDIA_ROOT
fi

# Check if "config.yaml" has been copied into the correct location
if test -f "$INVENTREE_CONFIG_FILE"; then
    echo "$INVENTREE_CONFIG_FILE exists - skipping"
else
    echo "Copying config file to $INVENTREE_CONFIG_FILE"
    cp $INVENTREE_HOME/InvenTree/config_template.yaml $INVENTREE_CONFIG_FILE
fi

# Setup a python virtual environment
# This should be done on the *mounted* filesystem,
# so that the installed modules persist!
if [[ -n "$INVENTREE_PY_ENV" ]]; then
    echo "Using Python virtual environment: ${INVENTREE_PY_ENV}"
    # Setup a virtual environment (within the "dev" directory)
    python3 -m venv ${INVENTREE_PY_ENV} --system-site-packages

    # Activate the virtual environment
    source ${INVENTREE_PY_ENV}/bin/activate

    # Note: Python packages will have to be installed on first run
    # e.g docker-compose run inventree-dev-server invoke update
fi

cd ${INVENTREE_HOME}

# Collect translation file stats
invoke translate-stats

# Launch the CMD *after* the ENTRYPOINT completes
exec "$@"
