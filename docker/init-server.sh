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

# Setup a dev environment on the mounted filesys
if [[ -n "$INVENTREE_DEV_VENV" ]]; then
    echo "Setting up a virtual env in ${INVENTREE_HOME}"
    # Setup a virtual environment (within the "dev" directory)
    python3 -m venv ./dev/env

    # Activate the virtual environment
    source ./dev/env/bin/activate

    echo "Installing required packages..."
    pip install --no-cache-dir -U -r ${INVENTREE_HOME}/requirements.txt
fi

if [[ "${INVENTREE_MIGRATE:-True}" = "True"  || "${INVENTREE_CREATE_SUPERUSER:-True}" = "True" ]]; then
	# Wait for the database to be ready
	cd $INVENTREE_MNG_DIR
	echo "InvenTree: Waiting for db"
	python3 manage.py wait_for_db && echo "InvenTree: db found, sleeping 10" || { echo "InvenTree: Failed to connect to db due to errors, aborting"; exit 1; }
	sleep 10
fi

if [[ "${INVENTREE_MIGRATE:-True}" = "True" ]]; then
    echo "InvenTree: Running database migrations and collecting static files..."

    # We assume at this stage that the database is up and running
    # Ensure that the database schema are up to date
    python3 manage.py check || exit 1
    echo "InvenTree: Check successful"
    python3 manage.py migrate --noinput || exit 1
    python3 manage.py migrate --run-syncdb || exit 1
    echo "InvenTree: Migrations successful"
    python3 manage.py prerender || exit 1
    python3 manage.py collectstatic --noinput || exit 1
    echo "InvenTree: static successful"

	#Can be run as a cron job or directly to clean out expired sessions.
    python3 manage.py clearsessions || exit 1
    echo "InvenTree: migrations complete"
fi

if [[ "${INVENTREE_CREATE_SUPERUSER:-True}" = "True" ]]; then
    #Check that the DJANGO properties are set
    if [[ -n "${DJANGO_SUPERUSER_USERNAME}" && -n "${DJANGO_SUPERUSER_EMAIL}" && -n "${DJANGO_SUPERUSER_PASSWORD}" ]]; then
        echo "InvenTree: Admin - Creating superuser account from env"
    	python3 manage.py createsuperuser --noinput || true #allow user to already exist
    else
		echo "InvenTree: Admin - Cannot create superuser account as the following variables are empty:"
		# -z is the opposite of -n
        [  -z "${DJANGO_SUPERUSER_USERNAME}" ] && echo "\t DJANGO_SUPERUSER_USERNAME"
        [  -z "${DJANGO_SUPERUSER_EMAIL}" ] && echo "\t DJANGO_SUPERUSER_EMAIL"
        [  -z "${DJANGO_SUPERUSER_PASSWORD}" ] && echo "\t DJANGO_SUPERUSER_PASSWORD"
	    exit 1
    fi

fi

cd $INVENTREE_HOME/InvenTree

#Launch the CMD
echo "init-server launching $@"
exec "$@"
echo "init-server exiting"
