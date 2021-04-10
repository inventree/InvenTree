#!/bin/sh

echo "Starting InvenTree worker..."

# Check that the database engine is specified
if [ -z "$INVENTREE_DB_ENGINE" ]; then
    echo "INVENTREE_DB_ENGINE not configured"
    exit 1
fi

# Activate virtual environment
source ./env/bin/activate

sleep 5

# Wait for the database to be ready
cd src/InvenTree

python manage.py wait_for_db

sleep 10

# Now we can launch the background worker process
python manage.py qcluster
