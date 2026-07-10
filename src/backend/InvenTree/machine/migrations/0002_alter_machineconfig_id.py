"""Migration to store MachineConfig UUID primary keys as char(32) on MySQL / MariaDB.

On MariaDB 10.7+, Django 5.x writes 36-character (hyphenated) UUID values,
but databases migrated under older Django / MariaDB versions retain char(32)
columns, causing machine creation to fail with "Data too long for column 'id'".

See: https://github.com/inventree/InvenTree/issues/12270
"""

import uuid

from django.db import migrations

import InvenTree.fields


class Migration(migrations.Migration):
    dependencies = [('machine', '0001_initial')]

    operations = [
        migrations.AlterField(
            model_name='machineconfig',
            name='id',
            field=InvenTree.fields.InvenTreeUUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
    ]
