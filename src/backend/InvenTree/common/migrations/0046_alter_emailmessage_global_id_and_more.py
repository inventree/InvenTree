"""Migration to store UUID primary keys as char(32) on MySQL / MariaDB.

On MariaDB 10.7+, Django 5.x creates UUIDField columns with the native 'uuid'
type and writes 36-character (hyphenated) values. Databases migrated under older
Django / MariaDB versions retain char(32) columns, into which the new values
do not fit.

See: https://github.com/inventree/InvenTree/issues/12270
"""

import uuid

from django.db import migrations

import InvenTree.fields


class Migration(migrations.Migration):
    dependencies = [('common', '0045_projectcode_active')]

    operations = [
        migrations.AlterField(
            model_name='emailmessage',
            name='global_id',
            field=InvenTree.fields.InvenTreeUUIDField(
                default=uuid.uuid4,
                editable=False,
                help_text='Unique identifier for this message',
                primary_key=True,
                serialize=False,
                unique=True,
                verbose_name='Global ID',
            ),
        ),
        migrations.AlterField(
            model_name='emailthread',
            name='global_id',
            field=InvenTree.fields.InvenTreeUUIDField(
                default=uuid.uuid4,
                editable=False,
                help_text='Unique identifier for this thread',
                primary_key=True,
                serialize=False,
                verbose_name='Global ID',
            ),
        ),
        migrations.AlterField(
            model_name='webhookmessage',
            name='message_id',
            field=InvenTree.fields.InvenTreeUUIDField(
                default=uuid.uuid4,
                editable=False,
                help_text='Unique identifier for this message',
                primary_key=True,
                serialize=False,
                verbose_name='Message ID',
            ),
        ),
    ]
