#!/bin/sh

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

# Setup a virtual environment (within the "dev" directory)
python3 -m venv ./dev/env

# Activate the virtual environment
source ./dev/env/bin/activate

echo "Installing required packages..."
pip install --no-cache-dir -U -r ${INVENTREE_HOME}/requirements.txt

echo "Starting InvenTree server..."

# Wait for the database to be ready
cd ${INVENTREE_HOME}/InvenTree
python3 manage.py wait_for_db

sleep 10

echo "Running InvenTree database migrations..."

# We assume at this stage that the database is up and running
# Ensure that the database schema are up to date
python3 manage.py check || exit 1
python3 manage.py migrate --noinput || exit 1
python3 manage.py migrate --run-syncdb || exit 1
python3 manage.py clearsessions || exit 1

# Launch a development server
python3 manage.py runserver ${INVENTREE_WEB_ADDR}:${INVENTREE_WEB_PORT}
