"""Remove the orphaned 'user_sessions_session' table.

Instances upgraded from a version predating #6293 (which switched from the
django-user-sessions package to allauth.usersessions) can still have the old
'user_sessions_session' table in their database. As the 'user_sessions' app
was removed from INSTALLED_APPS, Django no longer knows about this table or
its foreign key to auth_user, so deleting a user with an old-style session
fails with a ForeignKeyViolation. Drop the leftover table if present.
"""

from django.db import migrations


def remove_legacy_table(apps, schema_editor):
    """Drop the legacy 'user_sessions_session' table, if it exists."""
    table_name = 'user_sessions_session'

    if table_name in schema_editor.connection.introspection.table_names():
        schema_editor.execute(f'DROP TABLE {table_name}')


class Migration(migrations.Migration):
    dependencies = [('users', '0015_alter_userprofile_type')]

    operations = [
        migrations.RunPython(remove_legacy_table, reverse_code=migrations.RunPython.noop, atomic=False)
    ]
