#!/bin/sh

echo "Starting InvenTree worker..."

cd $INVENTREE_SRC_DIR

# Activate virtual environment
source inventree-docker-dev/bin/activate

sleep 5

# Wait for the database to be ready
cd $INVENTREE_MNG_DIR
python manage.py wait_for_db

sleep 10

# Now we can launch the background worker process
python manage.py qcluster
