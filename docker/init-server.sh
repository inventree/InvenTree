#!/bin/sh
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
    python3 -m venv ${INVENTREE_PY_ENV}

    # Activate the virtual environment
    source ${INVENTREE_PY_ENV}/bin/activate

    echo "Installing required packages..."
    pip install --no-cache-dir -U -r ${INVENTREE_HOME}/requirements.txt
fi

# Wait for the InvenTree database to be ready
cd ${INVENTREE_MNG_DIR}
echo "InvenTree: Waiting for database connection"
python3 manage.py wait_for_db && echo "InvenTree: db found, sleeping 10" || { echo "InvenTree: Failed to connect to db due to errors, aborting"; exit 1; }
sleep 10

# Check database migrations
cd ${INVENTREE_HOME}

# We assume at this stage that the database is up and running
# Ensure that the database schema are up to date
echo "InvenTree: Checking database..."
invoke check || exit 1
echo "InvenTree: Check successful"
echo "InvenTree: Database Migrations..."
invoke migrate || exit 1
echo "InvenTree: Migrations successful"
echo "InvenTree: Collecting static files..."
# Note: "translate" calls "static" also
invoke translate || exit 1
echo "InvenTree: static successful"

# Can be run as a cron job or directly to clean out expired sessions.
cd ${INVENTREE_MNG_DIR}
python3 manage.py clearsessions || exit 1
echo "InvenTree: migrations complete"

#Launch the CMD
#echo "init-server launching $@"
#exec "$@"
#echo "init-server exiting"
