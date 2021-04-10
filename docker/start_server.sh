#!/bin/sh

echo "Starting InvenTree server..."

# Check that the database engine is specified
if [ -z "$INVENTREE_DB_ENGINE" ]; then
    echo "INVENTREE_DB_ENGINE not configured"
    exit 1
fi

# Activate virtual environment
source $INVENTREE_VENV/bin/activate

sleep 5

# Wait for the database to be ready
cd $INVENTREE_MNG_DIR
python manage.py wait_for_db

sleep 10

echo "Running InvenTree database migrations and collecting static files..."

# We assume at this stage that the database is up and running
# Ensure that the database schema are up to date
python manage.py check || exit 1
python manage.py migrate --noinput || exit 1
python manage.py migrate --run-syncdb || exit 1
python manage.py collectstatic --noinput || exit 1
python manage.py clearsessions || exit 1

# Now we can launch the server
gunicorn -c $INVENTREE_HOME/gunicorn.conf.py InvenTree.wsgi -b 0.0.0.0:8080
