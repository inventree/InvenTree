"""Tasks for automating certain actions and interacting with InvenTree from the CLI."""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
from platform import python_version

from invoke import task


def checkPythonVersion():
    """Check that the installed python version meets minimum requirements.

    If the python version is not sufficient, exits with a non-zero exit code.
    """
    REQ_MAJOR = 3
    REQ_MINOR = 9

    version = sys.version.split(' ')[0]

    valid = True

    if sys.version_info.major < REQ_MAJOR:
        valid = False

    elif sys.version_info.major == REQ_MAJOR and sys.version_info.minor < REQ_MINOR:
        valid = False

    if not valid:
        print(f'The installed python version ({version}) is not supported!')
        print(f'InvenTree requires Python {REQ_MAJOR}.{REQ_MINOR} or above')
        sys.exit(1)


if __name__ in ['__main__', 'tasks']:
    checkPythonVersion()


def apps():
    """Returns a list of installed apps."""
    return [
        'build',
        'common',
        'company',
        'label',
        'order',
        'part',
        'report',
        'stock',
        'users',
        'plugin',
        'InvenTree',
    ]


def content_excludes(
    allow_auth: bool = True,
    allow_tokens: bool = True,
    allow_plugins: bool = True,
    allow_sso: bool = True,
):
    """Returns a list of content types to exclude from import/export.

    Arguments:
        allow_tokens (bool): Allow tokens to be exported/importe
        allow_plugins (bool): Allow plugin information to be exported/imported
        allow_sso (bool): Allow SSO tokens to be exported/imported
    """
    excludes = [
        'contenttypes',
        'auth.permission',
        'error_report.error',
        'admin.logentry',
        'django_q.schedule',
        'django_q.task',
        'django_q.ormq',
        'exchange.rate',
        'exchange.exchangebackend',
        'common.notificationentry',
        'common.notificationmessage',
        'user_sessions.session',
    ]

    # Optionally exclude user auth data
    if not allow_auth:
        excludes.append('auth.group')
        excludes.append('auth.user')

    # Optionally exclude user token information
    if not allow_tokens:
        excludes.append('users.apitoken')

    # Optionally exclude plugin information
    if not allow_plugins:
        excludes.append('plugin.pluginconfig')
        excludes.append('plugin.pluginsetting')

    # Optionally exclude SSO application information
    if not allow_sso:
        excludes.append('socialaccount.socialapp')
        excludes.append('socialaccount.socialtoken')

    return ' '.join([f'--exclude {e}' for e in excludes])


def localDir() -> Path:
    """Returns the directory of *THIS* file.

    Used to ensure that the various scripts always run
    in the correct directory.
    """
    return Path(__file__).parent.resolve()


def managePyDir():
    """Returns the directory of the manage.py file."""
    return localDir().joinpath('InvenTree')


def managePyPath():
    """Return the path of the manage.py file."""
    return managePyDir().joinpath('manage.py')


def manage(c, cmd, pty: bool = False):
    """Runs a given command against django's "manage.py" script.

    Args:
        c: Command line context.
        cmd: Django command to run.
        pty (bool, optional): Run an interactive session. Defaults to False.
    """
    c.run(
        'cd "{path}" && python3 manage.py {cmd}'.format(path=managePyDir(), cmd=cmd),
        pty=pty,
    )


def yarn(c, cmd, pty: bool = False):
    """Runs a given command against the yarn package manager.

    Args:
        c: Command line context.
        cmd: Yarn command to run.
        pty (bool, optional): Run an interactive session. Defaults to False.
    """
    path = managePyDir().parent.joinpath('src').joinpath('frontend')
    c.run(f'cd "{path}" && {cmd}', pty=pty)


def node_available(versions: bool = False, bypass_yarn: bool = False):
    """Checks if the frontend environment (ie node and yarn in bash) is available."""

    def ret(val, val0=None, val1=None):
        if versions:
            return val, val0, val1
        return val

    def check(cmd):
        try:
            return str(
                subprocess.check_output([cmd], stderr=subprocess.STDOUT, shell=True),
                encoding='utf-8',
            ).strip()
        except subprocess.CalledProcessError:
            return None
        except FileNotFoundError:
            return None

    yarn_version = check('yarn --version')
    node_version = check('node --version')

    # Either yarn is available or we don't care about yarn
    yarn_passes = bypass_yarn or yarn_version

    # Print a warning if node is available but yarn is not
    if node_version and not yarn_passes:
        print(
            'Node is available but yarn is not. Install yarn if you wish to build the frontend.'
        )

    # Return the result
    return ret(yarn_passes and node_version, node_version, yarn_version)


def check_file_existance(filename: str, overwrite: bool = False):
    """Checks if a file exists and asks the user if it should be overwritten.

    Args:
        filename (str): Name of the file to check.
        overwrite (bool, optional): Overwrite the file without asking. Defaults to False.
    """
    if Path(filename).is_file() and overwrite is False:
        response = input(
            'Warning: file already exists. Do you want to overwrite? [y/N]: '
        )
        response = str(response).strip().lower()

        if response not in ['y', 'yes']:
            print('Cancelled export operation')
            sys.exit(1)


# Install tasks
@task(help={'nouv': 'Do not use UV'})
def plugins(c, nouv=False):
    """Installs all plugins as specified in 'plugins.txt'."""
    from InvenTree.InvenTree.config import get_plugin_file

    plugin_file = get_plugin_file()

    print(f"Installing plugin packages from '{plugin_file}'")

    # Install the plugins
    if nouv:
        c.run(f"pip3 install --disable-pip-version-check -U -r '{plugin_file}'")
    else:
        c.run('pip3 install --no-cache-dir --disable-pip-version-check uv')
        c.run(f"uv pip install -r '{plugin_file}'")


@task(post=[plugins], help={'nouv': 'Do not use UV'})
def install(c, nouv=False):
    """Installs required python packages."""
    print("Installing required python packages from 'requirements.txt'")

    # Install required Python packages with PIP
    if nouv:
        c.run('pip3 install --upgrade pip')
        c.run('pip3 install --upgrade setuptools')
        c.run(
            'pip3 install --no-cache-dir --disable-pip-version-check -U -r requirements.txt'
        )
    else:
        c.run('pip3 install --upgrade uv')
        c.run('uv pip install --upgrade setuptools')
        c.run('uv pip install -U -r requirements.txt')


@task(help={'tests': 'Set up test dataset at the end'})
def setup_dev(c, tests=False):
    """Sets up everything needed for the dev environment."""
    print("Installing required python packages from 'requirements-dev.txt'")

    # Install required Python packages with PIP
    c.run('pip3 install -U -r requirements-dev.txt')

    # Install pre-commit hook
    print('Installing pre-commit for checks before git commits...')
    c.run('pre-commit install')

    # Update all the hooks
    c.run('pre-commit autoupdate')
    print('pre-commit set up is done...')

    # Set up test-data if flag is set
    if tests:
        setup_test(c)


# Setup / maintenance tasks
@task
def superuser(c):
    """Create a superuser/admin account for the database."""
    manage(c, 'createsuperuser', pty=True)


@task
def rebuild_models(c):
    """Rebuild database models with MPTT structures."""
    manage(c, 'rebuild_models', pty=True)


@task
def rebuild_thumbnails(c):
    """Rebuild missing image thumbnails."""
    manage(c, 'rebuild_thumbnails', pty=True)


@task
def clean_settings(c):
    """Clean the setting tables of old settings."""
    manage(c, 'clean_settings')


@task(help={'mail': "mail of the user who's MFA should be disabled"})
def remove_mfa(c, mail=''):
    """Remove MFA for a user."""
    if not mail:
        print('You must provide a users mail')

    manage(c, f'remove_mfa {mail}')


@task(help={'frontend': 'Build the frontend'})
def static(c, frontend=False):
    """Copies required static files to the STATIC_ROOT directory, as per Django requirements."""
    manage(c, 'prerender')
    if frontend and node_available():
        frontend_build(c)

    print('Collecting static files...')
    manage(c, 'collectstatic --no-input --clear')


@task
def translate_stats(c):
    """Collect translation stats.

    The file generated from this is needed for the UI.
    """
    # Recompile the translation files (.mo)
    # We do not run 'invoke translate' here, as that will touch the source (.po) files too!
    try:
        manage(c, 'compilemessages', pty=True)
    except Exception:
        print('WARNING: Translation files could not be compiled:')

    path = Path('InvenTree', 'script', 'translation_stats.py')
    c.run(f'python3 {path}')


@task(post=[translate_stats])
def translate(c, ignore_static=False, no_frontend=False):
    """Rebuild translation source files. Advanced use only!

    Note: This command should not be used on a local install,
    it is performed as part of the InvenTree translation toolchain.
    """
    # Translate applicable .py / .html / .js files
    manage(c, 'makemessages --all -e py,html,js --no-wrap')
    manage(c, 'compilemessages')

    if not no_frontend and node_available():
        frontend_install(c)
        frontend_trans(c)
        frontend_build(c)

    # Update static files
    if not ignore_static:
        static(c)


@task
def backup(c):
    """Backup the database and media files."""
    print('Backing up InvenTree database...')
    manage(c, 'dbbackup --noinput --clean --compress')
    print('Backing up InvenTree media files...')
    manage(c, 'mediabackup --noinput --clean --compress')


@task
def restore(c):
    """Restore the database and media files."""
    print('Restoring InvenTree database...')
    manage(c, 'dbrestore --noinput --uncompress')
    print('Restoring InvenTree media files...')
    manage(c, 'mediarestore --noinput --uncompress')


@task(post=[rebuild_models, rebuild_thumbnails])
def migrate(c):
    """Performs database migrations.

    This is a critical step if the database schema have been altered!
    """
    print('Running InvenTree database migrations...')
    print('========================================')

    # Run custom management command which wraps migrations in "maintenance mode"
    manage(c, 'makemigrations')
    manage(c, 'runmigrations', pty=True)
    manage(c, 'migrate --run-syncdb')

    print('========================================')
    print('InvenTree database migrations completed!')


@task(
    post=[clean_settings, translate_stats],
    help={
        'skip_backup': 'Skip database backup step (advanced users)',
        'frontend': 'Force frontend compilation/download step (ignores INVENTREE_DOCKER)',
        'no_frontend': 'Skip frontend compilation/download step',
        'skip_static': 'Skip static file collection step',
    },
)
def update(
    c,
    skip_backup: bool = False,
    frontend: bool = False,
    no_frontend: bool = False,
    skip_static: bool = False,
):
    """Update InvenTree installation.

    This command should be invoked after source code has been updated,
    e.g. downloading new code from GitHub.

    The following tasks are performed, in order:

    - install
    - backup (optional)
    - migrate
    - frontend_compile or frontend_download (optional)
    - static (optional)
    - clean_settings
    - translate_stats
    """
    # Ensure required components are installed
    install(c)

    if not skip_backup:
        backup(c)

    # Perform database migrations
    migrate(c)

    # Stop here if we are not building/downloading the frontend
    # If:
    # - INVENTREE_DOCKER is set (by the docker image eg.) and not overridden by `--frontend` flag
    # - `--no-frontend` flag is set
    if (os.environ.get('INVENTREE_DOCKER', False) and not frontend) or no_frontend:
        print('Skipping frontend update!')
        frontend = False
        no_frontend = True
    else:
        print('Updating frontend...')
        # Decide if we should compile the frontend or try to download it
        if node_available(bypass_yarn=True):
            frontend_compile(c)
        else:
            frontend_download(c)

    if not skip_static:
        static(c, frontend=not no_frontend)


# Data tasks
@task(
    help={
        'filename': "Output filename (default = 'data.json')",
        'overwrite': 'Overwrite existing files without asking first (default = False)',
        'include_permissions': 'Include user and group permissions in the output file (default = False)',
        'include_tokens': 'Include API tokens in the output file (default = False)',
        'exclude_plugins': 'Exclude plugin data from the output file (default = False)',
        'include_sso': 'Include SSO token data in the output file (default = False)',
        'retain_temp': 'Retain temporary files (containing permissions) at end of process (default = False)',
    }
)
def export_records(
    c,
    filename='data.json',
    overwrite=False,
    include_permissions=False,
    include_tokens=False,
    exclude_plugins=False,
    include_sso=False,
    retain_temp=False,
):
    """Export all database records to a file.

    Write data to the file defined by filename.
    If --overwrite is not set, the user will be prompted about overwriting an existing files.
    If --include-permissions is not set, the file defined by filename will have permissions specified for a user or group removed.
    If --delete-temp is not set, the temporary file (which includes permissions) will not be deleted. This file is named filename.tmp

    For historical reasons, calling this function without any arguments will thus result in two files:
    - data.json: does not include permissions
    - data.json.tmp: includes permissions

    If you want the script to overwrite any existing files without asking, add argument -o / --overwrite.

    If you only want one file, add argument - d / --delete-temp.

    If you want only one file, with permissions, then additionally add argument -i / --include-permissions
    """
    # Get an absolute path to the file
    if not os.path.isabs(filename):
        filename = localDir().joinpath(filename).resolve()

    print(f"Exporting database records to file '{filename}'")

    check_file_existance(filename, overwrite)

    tmpfile = f'{filename}.tmp'

    excludes = content_excludes(
        allow_tokens=include_tokens,
        allow_plugins=not exclude_plugins,
        allow_sso=include_sso,
    )

    cmd = f"dumpdata --natural-foreign --indent 2 --output '{tmpfile}' {excludes}"

    # Dump data to temporary file
    manage(c, cmd, pty=True)

    print('Running data post-processing step...')

    # Post-process the file, to remove any "permissions" specified for a user or group
    with open(tmpfile, 'r') as f_in:
        data = json.loads(f_in.read())

    data_out = []

    if include_permissions is False:
        for entry in data:
            model_name = entry.get('model', None)

            # Ignore any temporary settings (start with underscore)
            if model_name in ['common.inventreesetting', 'common.inventreeusersetting']:
                if entry['fields'].get('key', '').startswith('_'):
                    continue

            if model_name == 'auth.group':
                entry['fields']['permissions'] = []

            if model_name == 'auth.user':
                entry['fields']['user_permissions'] = []

            data_out.append(entry)

    # Write the processed data to file
    with open(filename, 'w') as f_out:
        f_out.write(json.dumps(data_out, indent=2))

    print('Data export completed')

    if not retain_temp:
        print('Removing temporary files')
        os.remove(tmpfile)


@task(
    help={
        'filename': 'Input filename',
        'clear': 'Clear existing data before import',
        'retain_temp': 'Retain temporary files at end of process (default = False)',
    },
    post=[rebuild_models, rebuild_thumbnails],
)
def import_records(
    c, filename='data.json', clear: bool = False, retain_temp: bool = False
):
    """Import database records from a file."""
    # Get an absolute path to the supplied filename
    if not os.path.isabs(filename):
        filename = localDir().joinpath(filename)

    if not os.path.exists(filename):
        print(f"Error: File '{filename}' does not exist")
        sys.exit(1)

    if clear:
        delete_data(c, force=True)

    print(f"Importing database records from '{filename}'")

    # We need to load 'auth' data (users / groups) *first*
    # This is due to the users.owner model, which has a ContentType foreign key
    authfile = f'{filename}.auth.json'

    # Pre-process the data, to remove any "permissions" specified for a user or group
    datafile = f'{filename}.data.json'

    with open(filename, 'r') as f_in:
        try:
            data = json.loads(f_in.read())
        except json.JSONDecodeError as exc:
            print(f'Error: Failed to decode JSON file: {exc}')
            sys.exit(1)

    auth_data = []
    load_data = []

    for entry in data:
        if 'model' in entry:
            # Clear out any permissions specified for a group
            if entry['model'] == 'auth.group':
                entry['fields']['permissions'] = []

            # Clear out any permissions specified for a user
            if entry['model'] == 'auth.user':
                entry['fields']['user_permissions'] = []

            # Save auth data for later
            if entry['model'].startswith('auth.'):
                auth_data.append(entry)
            else:
                load_data.append(entry)
        else:
            print('Warning: Invalid entry in data file')
            print(entry)

    # Write the auth file data
    with open(authfile, 'w') as f_out:
        f_out.write(json.dumps(auth_data, indent=2))

    # Write the processed data to the tmp file
    with open(datafile, 'w') as f_out:
        f_out.write(json.dumps(load_data, indent=2))

    excludes = content_excludes(allow_auth=False)

    # Import auth models first
    print('Importing user auth data...')
    cmd = f"loaddata '{authfile}'"
    manage(c, cmd, pty=True)

    # Import everything else next
    print('Importing database records...')
    cmd = f"loaddata '{datafile}' -i {excludes}"

    manage(c, cmd, pty=True)

    if not retain_temp:
        print('Removing temporary files')
        os.remove(datafile)
        os.remove(authfile)

    print('Data import completed')


@task
def delete_data(c, force=False):
    """Delete all database records!

    Warning: This will REALLY delete all records in the database!!
    """
    print('Deleting all data from InvenTree database...')

    if force:
        manage(c, 'flush --noinput')
    else:
        manage(c, 'flush')


@task(post=[rebuild_models, rebuild_thumbnails])
def import_fixtures(c):
    """Import fixture data into the database.

    This command imports all existing test fixture data into the database.

    Warning:
        - Intended for testing / development only!
        - Running this command may overwrite existing database data!!
        - Don't say you were not warned...
    """
    fixtures = [
        # Build model
        'build',
        # Common models
        'settings',
        # Company model
        'company',
        'price_breaks',
        'supplier_part',
        # Order model
        'order',
        # Part model
        'bom',
        'category',
        'params',
        'part',
        'test_templates',
        # Stock model
        'location',
        'stock_tests',
        'stock',
        # Users
        'users',
    ]

    command = 'loaddata ' + ' '.join(fixtures)

    manage(c, command, pty=True)


# Execution tasks
@task
def wait(c):
    """Wait until the database connection is ready."""
    return manage(c, 'wait_for_db')


@task(pre=[wait], help={'address': 'Server address:port (default=0.0.0.0:8000)'})
def gunicorn(c, address='0.0.0.0:8000'):
    """Launch a gunicorn webserver.

    Note: This server will not auto-reload in response to code changes.
    """
    c.run(
        'gunicorn -c ./docker/gunicorn.conf.py InvenTree.wsgi -b {address} --chdir ./InvenTree'.format(
            address=address
        ),
        pty=True,
    )


@task(pre=[wait], help={'address': 'Server address:port (default=127.0.0.1:8000)'})
def server(c, address='127.0.0.1:8000'):
    """Launch a (development) server using Django's in-built webserver.

    Note: This is *not* sufficient for a production installation.
    """
    manage(c, 'runserver {address}'.format(address=address), pty=True)


@task(pre=[wait])
def worker(c):
    """Run the InvenTree background worker process."""
    manage(c, 'qcluster', pty=True)


# Testing tasks
@task
def render_js_files(c):
    """Render templated javascript files (used for static testing)."""
    manage(c, 'test InvenTree.ci_render_js')


@task(post=[translate_stats, static, server])
def test_translations(c):
    """Add a fictional language to test if each component is ready for translations."""
    import django
    from django.conf import settings

    # setup django
    base_path = Path.cwd()
    new_base_path = pathlib.Path('InvenTree').resolve()
    sys.path.append(str(new_base_path))
    os.chdir(new_base_path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
    django.setup()

    # Add language
    print('Add dummy language...')
    print('========================================')
    manage(c, 'makemessages -e py,html,js --no-wrap -l xx')

    # change translation
    print('Fill in dummy translations...')
    print('========================================')

    file_path = pathlib.Path(settings.LOCALE_PATHS[0], 'xx', 'LC_MESSAGES', 'django.po')
    new_file_path = str(file_path) + '_new'

    # compile regex
    reg = re.compile(
        r'[a-zA-Z0-9]{1}'  # match any single letter and number  # noqa: W504
        + r'(?![^{\(\<]*[}\)\>])'  # that is not inside curly brackets, brackets or a tag  # noqa: W504
        + r'(?<![^\%][^\(][)][a-z])'  # that is not a specially formatted variable with singles  # noqa: W504
        + r'(?![^\\][\n])'  # that is not a newline
    )
    last_string = ''

    # loop through input file lines
    with open(file_path, 'rt') as file_org:
        with open(new_file_path, 'wt') as file_new:
            for line in file_org:
                if line.startswith('msgstr "'):
                    # write output -> replace regex matches with x in the read in (multi)string
                    file_new.write(f'msgstr "{reg.sub("x", last_string[7:-2])}"\n')
                    last_string = ''  # reset (multi)string
                elif line.startswith('msgid "'):
                    last_string = (
                        last_string + line
                    )  # a new translatable string starts -> start append
                    file_new.write(line)
                else:
                    if last_string:
                        last_string = (
                            last_string + line
                        )  # a string is being read in -> continue appending
                    file_new.write(line)

    # change out translation files
    file_path.rename(str(file_path) + '_old')
    new_file_path.rename(file_path)

    # compile languages
    print('Compile languages ...')
    print('========================================')
    manage(c, 'compilemessages')

    # reset cwd
    os.chdir(base_path)

    # set env flag
    os.environ['TEST_TRANSLATIONS'] = 'True'


@task(
    help={
        'disable_pty': 'Disable PTY',
        'runtest': 'Specify which tests to run, in format <module>.<file>.<class>.<method>',
        'migrations': 'Run migration unit tests',
        'report': 'Display a report of slow tests',
        'coverage': 'Run code coverage analysis (requires coverage package)',
    }
)
def test(
    c, disable_pty=False, runtest='', migrations=False, report=False, coverage=False
):
    """Run unit-tests for InvenTree codebase.

    To run only certain test, use the argument --runtest.
    This can filter all the way down to:
        <module>.<file>.<class>.<method>

    Example:
        test --runtest=company.test_api
    will run tests in the company/test_api.py file.
    """
    # Run sanity check on the django install
    manage(c, 'check')

    pty = not disable_pty

    _apps = ' '.join(apps())

    cmd = 'test'

    if runtest:
        # Specific tests to run
        cmd += f' {runtest}'
    else:
        # Run all tests
        cmd += f' {_apps}'

    if report:
        cmd += ' --slowreport'

    if migrations:
        cmd += ' --tag migration_test'
    else:
        cmd += ' --exclude-tag migration_test'

    if coverage:
        # Run tests within coverage environment, and generate report
        c.run(f'coverage run {managePyPath()} {cmd}')
        c.run('coverage html -i')
    else:
        # Run simple test runner, without coverage
        manage(c, cmd, pty=pty)


@task(help={'dev': 'Set up development environment at the end'})
def setup_test(c, ignore_update=False, dev=False, path='inventree-demo-dataset'):
    """Setup a testing environment."""
    from InvenTree.InvenTree.config import get_media_dir

    if not ignore_update:
        update(c)

    # Remove old data directory
    if os.path.exists(path):
        print('Removing old data ...')
        c.run(f'rm {path} -r')

    # Get test data
    print('Cloning demo dataset ...')
    c.run(f'git clone https://github.com/inventree/demo-dataset {path} -v --depth=1')
    print('========================================')

    # Make sure migrations are done - might have just deleted sqlite database
    if not ignore_update:
        migrate(c)

    # Load data
    print('Loading database records ...')
    import_records(c, filename=f'{path}/inventree_data.json', clear=True)

    # Copy media files
    print('Copying media files ...')
    src = Path(path).joinpath('media').resolve()
    dst = get_media_dir()

    shutil.copytree(src, dst, dirs_exist_ok=True)

    print('Done setting up test environment...')
    print('========================================')

    # Set up development setup if flag is set
    if dev:
        setup_dev(c)


@task(
    help={
        'filename': "Output filename (default = 'schema.yml')",
        'overwrite': 'Overwrite existing files without asking first (default = off/False)',
    }
)
def schema(c, filename='schema.yml', overwrite=False, ignore_warnings=False):
    """Export current API schema."""
    check_file_existance(filename, overwrite)

    cmd = f'spectacular --file {filename} --validate --color'

    if not ignore_warnings:
        cmd += ' --fail-on-warn'

    manage(c, cmd, pty=True)


@task(default=True)
def version(c):
    """Show the current version of InvenTree."""
    import InvenTree.InvenTree.version as InvenTreeVersion
    from InvenTree.InvenTree.config import (
        get_config_file,
        get_media_dir,
        get_static_dir,
    )

    # Gather frontend version information
    _, node, yarn = node_available(versions=True)

    print(
        f"""
InvenTree - inventree.org
The Open-Source Inventory Management System\n

Installation paths:
Base        {localDir()}
Config      {get_config_file()}
Media       {get_media_dir()}
Static      {get_static_dir()}

Versions:
Python      {python_version()}
Django      {InvenTreeVersion.inventreeDjangoVersion()}
InvenTree   {InvenTreeVersion.inventreeVersion()}
API         {InvenTreeVersion.inventreeApiVersion()}
Node        {node if node else 'N/A'}
Yarn        {yarn if yarn else 'N/A'}

Commit hash:{InvenTreeVersion.inventreeCommitHash()}
Commit date:{InvenTreeVersion.inventreeCommitDate()}"""
    )
    if len(sys.argv) == 1 and sys.argv[0].startswith('/opt/inventree/env/lib/python'):
        print(
            """
You are probably running the package installer / single-line installer. Please mentioned that in any bug reports!

Use '--list' for a list of available commands
Use '--help' for help on a specific command"""
        )


@task()
def frontend_check(c):
    """Check if frontend is available."""
    print(node_available())


@task
def frontend_compile(c):
    """Generate react frontend.

    Args:
        c: Context variable
    """
    print('Compiling frontend code...')

    frontend_install(c)
    frontend_trans(c)
    frontend_build(c)


@task
def frontend_install(c):
    """Install frontend requirements.

    Args:
        c: Context variable
    """
    print('Installing frontend dependencies')
    yarn(c, 'yarn install')


@task
def frontend_trans(c):
    """Compile frontend translations.

    Args:
        c: Context variable
    """
    print('Compiling frontend translations')
    yarn(c, 'yarn run extract')
    yarn(c, 'yarn run compile')


@task
def frontend_build(c):
    """Build frontend.

    Args:
        c: Context variable
    """
    print('Building frontend')
    yarn(c, 'yarn run build --emptyOutDir')


@task
def frontend_dev(c):
    """Start frontend development server.

    Args:
        c: Context variable
    """
    print('Starting frontend development server')
    yarn(c, 'yarn run compile')
    yarn(c, 'yarn run dev')


@task(
    help={
        'ref': 'git ref, default: current git ref',
        'tag': 'git tag to look for release',
        'file': 'destination to frontend-build.zip file',
        'repo': 'GitHub repository, default: InvenTree/inventree',
        'extract': 'Also extract and place at the correct destination, default: True',
        'clean': 'Delete old files from InvenTree/web/static/web first, default: True',
    }
)
def frontend_download(
    c,
    ref=None,
    tag=None,
    file=None,
    repo='InvenTree/inventree',
    extract=True,
    clean=True,
):
    """Download a pre-build frontend from GitHub if you dont want to install nodejs on your machine.

    There are 3 possibilities to install the frontend:
    1. invoke frontend-download --ref 01f2aa5f746a36706e9a5e588c4242b7bf1996d5
       if ref is omitted, it tries to auto detect the current git ref via `git rev-parse HEAD`.
       Note: GitHub doesn't allow workflow artifacts to be downloaded from anonymous users, so
             this will output a link where you can download the frontend with a signed in browser
             and then continue with option 3
    2. invoke frontend-download --tag 0.13.0
       Downloads the frontend build from the releases.
    3. invoke frontend-download --file /home/vscode/Downloads/frontend-build.zip
       This will extract your zip file and place the contents at the correct destination
    """
    import functools
    import subprocess
    from tempfile import NamedTemporaryFile
    from zipfile import ZipFile

    import requests

    print('Downloading frontend...')

    # globals
    default_headers = {'Accept': 'application/vnd.github.v3+json'}

    # helper functions
    def find_resource(resource, key, value):
        for obj in resource:
            if obj[key] == value:
                return obj
        return None

    def handle_extract(file):
        # if no extract is requested, exit here
        if not extract:
            return

        dest_path = Path(__file__).parent / 'InvenTree/web/static/web'

        # if clean, delete static/web directory
        if clean:
            shutil.rmtree(dest_path, ignore_errors=True)
            os.makedirs(dest_path)
            print(f'Cleaned directory: {dest_path}')

        # unzip build to static folder
        with ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(dest_path)

        print(f'Unzipped downloaded frontend build to: {dest_path}')

    def handle_download(url):
        # download frontend-build.zip to temporary file
        with requests.get(
            url, headers=default_headers, stream=True, allow_redirects=True
        ) as response, NamedTemporaryFile(suffix='.zip') as dst:
            response.raise_for_status()

            # auto decode the gzipped raw data
            response.raw.read = functools.partial(
                response.raw.read, decode_content=True
            )
            with open(dst.name, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            print(f'Downloaded frontend build to temporary file: {dst.name}')

            handle_extract(dst.name)

    # if zip file is specified, try to extract it directly
    if file:
        handle_extract(file)
        return

    # check arguments
    if ref is not None and tag is not None:
        print('[ERROR] Do not set ref and tag.')
        return

    if ref is None and tag is None:
        try:
            ref = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], encoding='utf-8'
            ).strip()
        except Exception:
            print("[ERROR] Cannot get current ref via 'git rev-parse HEAD'")
            return

    if ref is None and tag is None:
        print('[ERROR] Either ref or tag needs to be set.')

    if tag:
        tag = tag.lstrip('v')
        try:
            handle_download(
                f'https://github.com/{repo}/releases/download/{tag}/frontend-build.zip'
            )
        except Exception as e:
            if not isinstance(e, requests.HTTPError):
                raise e
            print(
                f"""[ERROR] An Error occurred. Unable to download frontend build, release or build does not exist,
try downloading the frontend-build.zip yourself via: https://github.com/{repo}/releases
Then try continuing by running: invoke frontend-download --file <path-to-downloaded-zip-file>"""
            )

        return

    if ref:
        # get workflow run from all workflow runs on that particular ref
        workflow_runs = requests.get(
            f'https://api.github.com/repos/{repo}/actions/runs?head_sha={ref}',
            headers=default_headers,
        ).json()

        if not (qc_run := find_resource(workflow_runs['workflow_runs'], 'name', 'QC')):
            print('[ERROR] Cannot find any workflow runs for current sha')
            return
        print(
            f"Found workflow {qc_run['name']} (run {qc_run['run_number']}-{qc_run['run_attempt']})"
        )

        # get frontend-build artifact from all artifacts available for this workflow run
        artifacts = requests.get(
            qc_run['artifacts_url'], headers=default_headers
        ).json()
        if not (
            frontend_artifact := find_resource(
                artifacts['artifacts'], 'name', 'frontend-build'
            )
        ):
            print('[ERROR] Cannot find frontend-build.zip attachment for current sha')
            return
        print(
            f"Found artifact {frontend_artifact['name']} with id {frontend_artifact['id']} ({frontend_artifact['size_in_bytes']/1e6:.2f}MB)."
        )

        print(
            f"""
GitHub doesn't allow artifact downloads from anonymous users. Either download the following file
via your signed in browser, or consider using a point release download via invoke frontend-download --tag <git-tag>

    Download: https://github.com/{repo}/suites/{qc_run['check_suite_id']}/artifacts/{frontend_artifact['id']} manually and
    continue by running: invoke frontend-download --file <path-to-downloaded-zip-file>"""
        )
