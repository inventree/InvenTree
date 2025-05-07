"""Tasks for automating certain actions and interacting with InvenTree from the CLI."""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from functools import wraps
from pathlib import Path
from platform import python_version
from typing import Optional

import invoke
from invoke import Collection, task
from invoke.exceptions import UnexpectedExit


def is_docker_environment():
    """Check if the InvenTree environment is running in a Docker container."""
    from src.backend.InvenTree.InvenTree.config import is_true

    return is_true(os.environ.get('INVENTREE_DOCKER', 'False'))


def is_rtd_environment():
    """Check if the InvenTree environment is running on ReadTheDocs."""
    from src.backend.InvenTree.InvenTree.config import is_true

    return is_true(os.environ.get('READTHEDOCS', 'False'))


def is_debug_environment():
    """Check if the InvenTree environment is running in a debug environment."""
    from src.backend.InvenTree.InvenTree.config import is_true

    return is_true(os.environ.get('INVENTREE_DEBUG', 'False')) or is_true(
        os.environ.get('RUNNER_DEBUG', 'False')
    )


# region execution logging helpers
def task_exception_handler(t, v, tb):
    """Handle exceptions raised by tasks.

    The intent here is to provide more 'useful' error messages when tasks fail.
    """
    sys.__excepthook__(t, v, tb)

    if t is ModuleNotFoundError:
        mod_name = str(v).split(' ')[-1].strip("'")

        error(f'Error importing required module: {mod_name}')
        warning('- Ensure the correct Python virtual environment is active')
        warning(
            '- Ensure that the invoke tool is installed in the active Python environment'
        )
        warning(
            "- Ensure all required packages are installed by running 'invoke install'"
        )


sys.excepthook = task_exception_handler


def wrap_color(text: str, color: str) -> str:
    """Wrap text in a color code."""
    return f'\033[{color}m{text}\033[0m'


def success(*args):
    """Print a success message to the console."""
    msg = ' '.join(map(str, args))
    print(wrap_color(msg, '92'))


def error(*args):
    """Print an error message to the console."""
    msg = ' '.join(map(str, args))
    print(wrap_color(msg, '91'))


def warning(*args):
    """Print a warning message to the console."""
    msg = ' '.join(map(str, args))
    print(wrap_color(msg, '93'))


def info(*args):
    """Print an informational message to the console."""
    msg = ' '.join(map(str, args))
    print(wrap_color(msg, '94'))


def state_logger(fn=None, method_name=None):
    """Decorator to log state markers before/after function execution, optionally accepting arguments."""

    def decorator(func):
        func.method_name = method_name or f'invoke task named `{func.__name__}`'

        @wraps(func)
        def wrapped(c, *args, **kwargs):
            do_log = is_debug_environment()
            if do_log:
                info(f'# {func.method_name}| start')
            func(c, *args, **kwargs)
            if do_log:
                info(f'# {func.method_name}| done')

        return wrapped

    if fn and callable(fn):
        return decorator(fn)
    elif fn and isinstance(fn, str):
        method_name = fn
    return decorator


# endregion


# region environment checks
def check_invoke_version():
    """Check that the installed invoke version meets minimum requirements."""
    MIN_INVOKE_VERSION = '2.0.0'

    min_version = tuple(map(int, MIN_INVOKE_VERSION.split('.')))
    invoke_version = tuple(map(int, invoke.__version__.split('.')))  # noqa: RUF048

    if invoke_version < min_version:
        error(f'The installed invoke version ({invoke.__version__}) is not supported!')
        error(f'InvenTree requires invoke version {MIN_INVOKE_VERSION} or above')
        sys.exit(1)


def check_invoke_path():
    """Check that the path of the used invoke is correct."""
    if is_docker_environment() or is_rtd_environment():
        return

    invoke_path = Path(invoke.__file__)
    env_path = Path(sys.prefix).resolve()
    loc_path = Path(__file__).parent.resolve()
    if not invoke_path.is_relative_to(loc_path) and not invoke_path.is_relative_to(
        env_path
    ):
        error('INVE-E2 - Wrong Invoke Path')
        error(
            f'The invoke tool `{invoke_path}` is not correctly located, ensure you are using the invoke installed in an environment in `{loc_path}` or `{env_path}`'
        )
        sys.exit(1)


def check_python_version():
    """Check that the installed python version meets minimum requirements.

    If the python version is not sufficient, exits with a non-zero exit code.
    """
    REQ_MAJOR = 3
    REQ_MINOR = 9

    version = sys.version.split(' ')[0]

    valid = True

    if sys.version_info.major < REQ_MAJOR or (
        sys.version_info.major == REQ_MAJOR and sys.version_info.minor < REQ_MINOR
    ):
        valid = False

    if not valid:
        error(f'The installed python version ({version}) is not supported!')
        error(f'InvenTree requires Python {REQ_MAJOR}.{REQ_MINOR} or above')
        sys.exit(1)


if __name__ in ['__main__', 'tasks']:
    check_invoke_version()
    check_invoke_path()
    check_python_version()
# endregion


def apps():
    """Returns a list of installed apps."""
    return [
        'build',
        'common',
        'company',
        'importer',
        'machine',
        'order',
        'part',
        'report',
        'stock',
        'users',
        'plugin',
        'InvenTree',
        'generic',
        'machine',
        'web',
    ]


def content_excludes(
    allow_auth: bool = True,
    allow_tokens: bool = True,
    allow_plugins: bool = True,
    allow_sso: bool = True,
):
    """Returns a list of content types to exclude from import / export.

    Arguments:
        allow_auth (bool): Allow user authentication data to be exported / imported
        allow_tokens (bool): Allow tokens to be exported / imported
        allow_plugins (bool): Allow plugin information to be exported / imported
        allow_sso (bool): Allow SSO tokens to be exported / imported
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
        'common.dataoutput',
        'common.notificationentry',
        'common.notificationmessage',
        'importer.dataimportsession',
        'importer.dataimportcolumnmap',
        'importer.dataimportrow',
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


# region file helpers
def local_dir() -> Path:
    """Returns the directory of *THIS* file.

    Used to ensure that the various scripts always run
    in the correct directory.
    """
    return Path(__file__).parent.resolve()


def manage_py_dir():
    """Returns the directory of the manage.py file."""
    return local_dir().joinpath('src', 'backend', 'InvenTree')


def manage_py_path():
    """Return the path of the manage.py file."""
    return manage_py_dir().joinpath('manage.py')


# endregion


def run(c, cmd, path: Optional[Path] = None, pty=False, env=None):
    """Runs a given command a given path.

    Args:
        c: Command line context.
        cmd: Command to run.
        path: Path to run the command in.
        pty (bool, optional): Run an interactive session. Defaults to False.
        env (dict, optional): Environment variables to pass to the command. Defaults to None.
    """
    env = env or {}
    path = path or local_dir()

    try:
        c.run(f'cd "{path}" && {cmd}', pty=pty, env=env)
    except UnexpectedExit as e:
        error(f"ERROR: InvenTree command failed: '{cmd}'")
        warning('- Refer to the error messages in the log above for more information')
        raise e


def manage(c, cmd, pty: bool = False, env=None):
    """Runs a given command against django's "manage.py" script.

    Args:
        c: Command line context.
        cmd: Django command to run.
        pty (bool, optional): Run an interactive session. Defaults to False.
        env (dict, optional): Environment variables to pass to the command. Defaults to None.
    """
    run(c, f'python3 manage.py {cmd}', manage_py_dir(), pty, env)


def yarn(c, cmd):
    """Runs a given command against the yarn package manager.

    Args:
        c: Command line context.
        cmd: Yarn command to run.
    """
    path = local_dir().joinpath('src', 'frontend')
    run(c, cmd, path, False)


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
        warning(
            'Node is available but yarn is not. Install yarn if you wish to build the frontend.'
        )

    # Return the result
    return ret(yarn_passes and node_version, node_version, yarn_version)


@state_logger
def check_file_existence(filename: Path, overwrite: bool = False):
    """Checks if a file exists and asks the user if it should be overwritten.

    Args:
        filename (str): Name of the file to check.
        overwrite (bool, optional): Overwrite the file without asking. Defaults to False.
    """
    if filename.is_file() and overwrite is False:
        response = input(
            'Warning: file already exists. Do you want to overwrite? [y/N]: '
        )
        response = str(response).strip().lower()

        if response not in ['y', 'yes']:
            error('Cancelled export operation')
            sys.exit(1)


# Install tasks
# region tasks
@task(help={'uv': 'Use UV (experimental package manager)'})
@state_logger('TASK01')
def plugins(c, uv=False):
    """Installs all plugins as specified in 'plugins.txt'."""
    from src.backend.InvenTree.InvenTree.config import get_plugin_file

    plugin_file = get_plugin_file()

    info(f"Installing plugin packages from '{plugin_file}'")

    # Install the plugins
    if not uv:
        run(c, f"pip3 install --disable-pip-version-check -U -r '{plugin_file}'")
    else:
        run(c, 'pip3 install --no-cache-dir --disable-pip-version-check uv')
        run(c, f"uv pip install -r '{plugin_file}'")

    # Collect plugin static files
    manage(c, 'collectplugins')


@task(
    help={
        'uv': 'Use UV package manager (experimental)',
        'skip_plugins': 'Skip plugin installation',
    }
)
@state_logger('TASK02')
def install(c, uv=False, skip_plugins=False):
    """Installs required python packages."""
    # Ensure path is relative to *this* directory
    INSTALL_FILE = local_dir().joinpath('src/backend/requirements.txt')

    info(f"Installing required python packages from '{INSTALL_FILE}'")

    if not Path(INSTALL_FILE).is_file():
        raise FileNotFoundError(f"Requirements file '{INSTALL_FILE}' not found")

    # Install required Python packages with PIP
    if not uv:
        run(
            c,
            'pip3 install --no-cache-dir --disable-pip-version-check -U pip setuptools',
        )
        run(
            c,
            f'pip3 install --no-cache-dir --disable-pip-version-check -U --require-hashes -r {INSTALL_FILE}',
        )
    else:
        run(
            c,
            'pip3 install --no-cache-dir --disable-pip-version-check -U uv setuptools',
        )
        run(c, f'uv pip install -U --require-hashes  -r {INSTALL_FILE}')

    # Run plugins install
    if not skip_plugins:
        plugins(c, uv=uv)

    # Compile license information
    lic_path = manage_py_dir().joinpath('InvenTree', 'licenses.txt')
    run(
        c,
        f'pip-licenses --format=json --with-license-file --no-license-path > {lic_path}',
    )

    success('Dependency installation complete')


@task(help={'tests': 'Set up test dataset at the end'})
def setup_dev(c, tests=False):
    """Sets up everything needed for the dev environment."""
    info("Installing required python packages from 'src/backend/requirements-dev.txt'")

    # Install required Python packages with PIP
    run(c, 'pip3 install -U --require-hashes -r src/backend/requirements-dev.txt')

    # Install pre-commit hook
    info('Installing pre-commit for checks before git commits...')
    run(c, 'pre-commit install')

    # Update all the hooks
    run(c, 'pre-commit autoupdate')

    success('pre-commit set up complete')

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
    info('Rebuilding internal database structures')
    manage(c, 'rebuild_models', pty=True)


@task
def rebuild_thumbnails(c):
    """Rebuild missing image thumbnails."""
    from src.backend.InvenTree.InvenTree.config import get_media_dir

    info(f'Rebuilding image thumbnails in {get_media_dir()}')
    manage(c, 'rebuild_thumbnails', pty=True)


@task
@state_logger('TASK09')
def clean_settings(c):
    """Clean the setting tables of old settings."""
    info('Cleaning old settings from the database')
    manage(c, 'clean_settings')
    success('Settings cleaned successfully')


@task(help={'mail': "mail of the user who's MFA should be disabled"})
def remove_mfa(c, mail=''):
    """Remove MFA for a user."""
    if not mail:
        warning('You must provide a users mail')
        return

    manage(c, f'remove_mfa {mail}')


@task(
    help={
        'frontend': 'Build the frontend',
        'clear': 'Remove existing static files',
        'skip_plugins': 'Ignore collection of plugin static files',
    }
)
@state_logger('TASK08')
def static(c, frontend=False, clear=True, skip_plugins=False):
    """Copies required static files to the STATIC_ROOT directory, as per Django requirements."""
    if frontend and node_available():
        frontend_compile(c)

    info('Collecting static files...')

    cmd = 'collectstatic --no-input --verbosity 0'

    if clear:
        cmd += ' --clear'

    manage(c, cmd)

    # Collect plugin static files
    if not skip_plugins:
        manage(c, 'collectplugins')

    success('Static files collected successfully')


@task
def translate(c, ignore_static=False, no_frontend=False):
    """Rebuild translation source files. Advanced use only!

    Note: This command should not be used on a local install,
    it is performed as part of the InvenTree translation toolchain.
    """
    info('Building translation files')

    # Translate applicable .py / .html / .js files
    manage(c, 'makemessages --all -e py,html,js --no-wrap')
    manage(c, 'compilemessages')

    if not no_frontend and node_available():
        frontend_compile(c)

    # Update static files
    if not ignore_static:
        static(c)

    success('Translation files built successfully')


@task(
    help={
        'clean': 'Clean up old backup files',
        'path': 'Specify path for generated backup files (leave blank for default path)',
    }
)
@state_logger('TASK04')
def backup(c, clean=False, path=None):
    """Backup the database and media files."""
    info('Backing up InvenTree database...')

    cmd = '--noinput --compress -v 2'

    if path:
        # Resolve the provided path
        path = Path(path)
        if not os.path.isabs(path):
            path = local_dir().joinpath(path).resolve()

        cmd += f' -O {path}'

    if clean:
        cmd += ' --clean'

    manage(c, f'dbbackup {cmd}')
    info('Backing up InvenTree media files...')
    manage(c, f'mediabackup {cmd}')

    success('Backup completed successfully')


@task(
    help={
        'path': 'Specify path to locate backup files (leave blank for default path)',
        'db_file': 'Specify filename of compressed database archive (leave blank to use most recent backup)',
        'media_file': 'Specify filename of compressed media archive (leave blank to use most recent backup)',
        'ignore_media': 'Do not import media archive (database restore only)',
        'ignore_database': 'Do not import database archive (media restore only)',
    }
)
def restore(
    c,
    path=None,
    db_file=None,
    media_file=None,
    ignore_media=False,
    ignore_database=False,
):
    """Restore the database and media files."""
    base_cmd = '--noinput --uncompress -v 2'

    if path:
        # Resolve the provided path
        path = Path(path)
        if not os.path.isabs(path):
            path = local_dir().joinpath(path).resolve()

        base_cmd += f' -I {path}'

    if ignore_database:
        info('Skipping database archive...')
    else:
        info('Restoring InvenTree database')
        cmd = f'dbrestore {base_cmd}'

        if db_file:
            cmd += f' -i {db_file}'

        manage(c, cmd)

    if ignore_media:
        info('Skipping media restore...')
    else:
        info('Restoring InvenTree media files')
        cmd = f'mediarestore {base_cmd}'

        if media_file:
            cmd += f' -i {media_file}'

        manage(c, cmd)


@task(post=[rebuild_models, rebuild_thumbnails])
@state_logger('TASK05')
def migrate(c):
    """Performs database migrations.

    This is a critical step if the database schema have been altered!
    """
    info('Running InvenTree database migrations...')

    # Run custom management command which wraps migrations in "maintenance mode"
    manage(c, 'makemigrations')
    manage(c, 'runmigrations', pty=True)
    manage(c, 'migrate --run-syncdb')
    manage(c, 'remove_stale_contenttypes --include-stale-apps --no-input', pty=True)

    success('InvenTree database migrations completed')


@task(help={'app': 'Specify an app to show migrations for (leave blank for all apps)'})
def showmigrations(c, app=''):
    """Show the migration status of the database."""
    manage(c, f'showmigrations {app}', pty=True)


@task(
    post=[clean_settings],
    help={
        'skip_backup': 'Skip database backup step (advanced users)',
        'frontend': 'Force frontend compilation/download step (ignores INVENTREE_DOCKER)',
        'no_frontend': 'Skip frontend compilation/download step',
        'skip_static': 'Skip static file collection step',
        'uv': 'Use UV (experimental package manager)',
    },
)
@state_logger('TASK03')
def update(
    c,
    skip_backup: bool = False,
    frontend: bool = False,
    no_frontend: bool = False,
    skip_static: bool = False,
    uv: bool = False,
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
    """
    info('Updating InvenTree installation...')

    # Ensure required components are installed
    install(c, uv=uv)

    if not skip_backup:
        backup(c)

    # Perform database migrations
    migrate(c)

    # Stop here if we are not building/downloading the frontend
    # If:
    # - INVENTREE_DOCKER is set (by the docker image eg.) and not overridden by `--frontend` flag
    # - `--no-frontend` flag is set
    if (is_docker_environment() and not frontend) or no_frontend:
        if no_frontend:
            info('Skipping frontend update (no_frontend flag set)')
        else:
            info('Skipping frontend update (INVENTREE_DOCKER flag set)')

        frontend = False
        no_frontend = True
    else:
        info('Updating frontend...')
        # Decide if we should compile the frontend or try to download it
        if node_available(bypass_yarn=True):
            frontend_compile(c)
        else:
            frontend_download(c)

    if not skip_static:
        # Collect static files
        # Note: frontend has already been compiled if required
        static(c, frontend=False)

    success('InvenTree update complete!')


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
    target = Path(filename)
    if not target.is_absolute():
        target = local_dir().joinpath(filename).resolve()

    info(f"Exporting database records to file '{target}'")

    check_file_existence(target, overwrite)

    tmpfile = f'{target}.tmp'

    excludes = content_excludes(
        allow_tokens=include_tokens,
        allow_plugins=not exclude_plugins,
        allow_sso=include_sso,
    )

    cmd = f"dumpdata --natural-foreign --indent 2 --output '{tmpfile}' {excludes}"

    # Dump data to temporary file
    manage(c, cmd, pty=True)

    info('Running data post-processing step...')

    # Post-process the file, to remove any "permissions" specified for a user or group
    with open(tmpfile, encoding='utf-8') as f_in:
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
    with open(target, 'w', encoding='utf-8') as f_out:
        f_out.write(json.dumps(data_out, indent=2))

    if not retain_temp:
        info('Removing temporary files')
        os.remove(tmpfile)

    success('Data export completed')


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
    target = Path(filename)
    if not target.is_absolute():
        target = local_dir().joinpath(filename)

    if not target.exists():
        error(f"ERROR: File '{target}' does not exist")
        sys.exit(1)

    if clear:
        delete_data(c, force=True)

    info(f"Importing database records from '{target}'")

    # We need to load 'auth' data (users / groups) *first*
    # This is due to the users.owner model, which has a ContentType foreign key
    authfile = f'{target}.auth.json'

    # Pre-process the data, to remove any "permissions" specified for a user or group
    datafile = f'{target}.data.json'

    with open(target, encoding='utf-8') as f_in:
        try:
            data = json.loads(f_in.read())
        except json.JSONDecodeError as exc:
            error(f'ERROR: Failed to decode JSON file: {exc}')
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
            warning('WARNING: Invalid entry in data file')
            print(entry)

    # Write the auth file data
    with open(authfile, 'w', encoding='utf-8') as f_out:
        f_out.write(json.dumps(auth_data, indent=2))

    # Write the processed data to the tmp file
    with open(datafile, 'w', encoding='utf-8') as f_out:
        f_out.write(json.dumps(load_data, indent=2))

    excludes = content_excludes(allow_auth=False)

    # Import auth models first
    info('Importing user auth data...')
    cmd = f"loaddata '{authfile}'"
    manage(c, cmd, pty=True)

    # Import everything else next
    info('Importing database records...')
    cmd = f"loaddata '{datafile}' -i {excludes}"

    manage(c, cmd, pty=True)

    if not retain_temp:
        info('Removing temporary files')
        os.remove(datafile)
        os.remove(authfile)

    info('Data import completed')


@task
def delete_data(c, force=False):
    """Delete all database records!

    Warning: This will REALLY delete all records in the database!!
    """
    info('Deleting all data from InvenTree database...')

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
@state_logger('TASK10')
def wait(c):
    """Wait until the database connection is ready."""
    info('Waiting for database connection...')
    return manage(c, 'wait_for_db')


@task(
    pre=[wait],
    help={
        'address': 'Server address:port (default=0.0.0.0:8000)',
        'workers': 'Specify number of worker threads (override config file)',
    },
)
def gunicorn(c, address='0.0.0.0:8000', workers=None):
    """Launch a gunicorn webserver.

    Note: This server will not auto-reload in response to code changes.
    """
    config_file = local_dir().joinpath('contrib', 'container', 'gunicorn.conf.py')
    cmd = f'gunicorn -c {config_file} InvenTree.wsgi -b {address} --chdir {manage_py_dir()}'

    if workers:
        cmd += f' --workers={workers}'

    info(f'Starting Gunicorn Server: {cmd}')
    run(c, cmd, pty=True)


@task(
    pre=[wait],
    help={
        'address': 'Server address:port (default=127.0.0.1:8000)',
        'no_reload': 'Do not automatically reload the server in response to code changes',
        'no_threading': 'Disable multi-threading for the development server',
    },
)
def server(c, address='127.0.0.1:8000', no_reload=False, no_threading=False):
    """Launch a (development) server using Django's in-built webserver.

    Note: This is *not* sufficient for a production installation.
    """
    cmd = f'runserver {address}'

    if no_reload:
        cmd += ' --noreload'

    if no_threading:
        cmd += ' --nothreading'

    manage(c, cmd, pty=True)


@task(pre=[wait])
def worker(c):
    """Run the InvenTree background worker process."""
    manage(c, 'qcluster', pty=True)


@task(post=[static, server])
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
    info('Add dummy language...')
    manage(c, 'makemessages -e py,html,js --no-wrap -l xx')

    # change translation
    info('Fill in dummy translations...')

    file_path = pathlib.Path(settings.LOCALE_PATHS[0], 'xx', 'LC_MESSAGES', 'django.po')
    new_file_path = str(file_path) + '_new'

    # compile regex
    reg = re.compile(
        r'[a-zA-Z0-9]{1}'  # match any single letter and number
        + r'(?![^{\(\<]*[}\)\>])'  # that is not inside curly brackets, brackets or a tag
        + r'(?<![^\%][^\(][)][a-z])'  # that is not a specially formatted variable with singles
        + r'(?![^\\][\n])'  # that is not a newline
    )
    last_string = ''

    # loop through input file lines
    with open(file_path, encoding='utf-8') as file_org:
        with open(new_file_path, 'w', encoding='utf-8') as file_new:
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
    info('Compile languages ...')
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
    c,
    disable_pty=False,
    runtest='',
    migrations=False,
    report=False,
    coverage=False,
    translations=False,
):
    """Run unit-tests for InvenTree codebase.

    Args:
        c: Command line context.
        disable_pty (bool): Disable PTY (default = False)
        runtest (str): Specify which tests to run, in format <module>.<file>.<class>.<method> (default = '')
        migrations (bool): Run migration unit tests (default = False)
        report (bool): Display a report of slow tests (default = False)
        coverage (bool): Run code coverage analysis (requires coverage package) (default = False)
        translations (bool): Compile translations before running tests (default = False)

    To run only certain test, use the argument --runtest.
    This can filter all the way down to:
        <module>.<file>.<class>.<method>

    Example:
        test --runtest=company.test_api
    will run tests in the company/test_api.py file.
    """
    # Run sanity check on the django install
    manage(c, 'check')

    if translations:
        try:
            manage(c, 'compilemessages', pty=True)
        except Exception:
            warning('Failed to compile translations')

    pty = not disable_pty

    tested_apps = ' '.join(apps())

    cmd = 'test'

    if runtest:
        # Specific tests to run
        cmd += f' {runtest}'
    else:
        # Run all tests
        cmd += f' {tested_apps}'

    if report:
        cmd += ' --slowreport'

    if migrations:
        cmd += ' --tag migration_test'
    else:
        cmd += ' --exclude-tag migration_test'

    if coverage:
        # Run tests within coverage environment, and generate report
        run(c, f'coverage run {manage_py_path()} {cmd}')
        run(c, 'coverage xml -i')
    else:
        # Run simple test runner, without coverage
        manage(c, cmd, pty=pty)


@task(
    help={
        'dev': 'Set up development environment at the end',
        'validate_files': 'Validate media files are correctly copied',
    }
)
def setup_test(
    c,
    ignore_update=False,
    dev=False,
    validate_files=False,
    path='inventree-demo-dataset',
):
    """Setup a testing environment."""
    from src.backend.InvenTree.InvenTree.config import get_media_dir

    if not ignore_update:
        update(c)

    template_dir = local_dir().joinpath(path)

    # Remove old data directory
    if template_dir.exists():
        info('Removing old data ...')
        run(c, f'rm {template_dir} -r')

    # Get test data
    info('Cloning demo dataset ...')
    run(
        c,
        f'git clone https://github.com/inventree/demo-dataset {template_dir} -v --depth=1',
    )

    # Make sure migrations are done - might have just deleted sqlite database
    if not ignore_update:
        migrate(c)

    # Load data
    info('Loading database records ...')
    import_records(c, filename=template_dir.joinpath('inventree_data.json'), clear=True)

    # Copy media files
    src = template_dir.joinpath('media')
    dst = get_media_dir()
    info(f'Copying media files - "{src}" to "{dst}"')
    shutil.copytree(src, dst, dirs_exist_ok=True)

    if validate_files:
        info(' - Validating media files')
        missing = False
        # Check that the media files are correctly copied across
        for dirpath, _dirnames, filenames in os.walk(src):
            rel_path = os.path.relpath(dirpath, src)
            dst_path = os.path.join(dst, rel_path)

            if not os.path.exists(dst_path):
                error(f' - Missing directory: {dst_path}')
                missing = True
                continue

            for filename in filenames:
                dst_file = os.path.join(dst_path, filename)
                if not os.path.exists(dst_file):
                    missing = True
                    error(f' - Missing file: {dst_file}')

        if missing:
            raise FileNotFoundError('Media files not correctly copied')
        else:
            success(' - All media files correctly copied')

    info('Done setting up test environment...')

    # Set up development setup if flag is set
    if dev:
        setup_dev(c)


@task(
    help={
        'filename': "Output filename (default = 'schema.yml')",
        'overwrite': 'Overwrite existing files without asking first (default = off/False)',
        'no_default': 'Do not use default settings for schema (default = off/False)',
    }
)
@state_logger('TASK11')
def schema(
    c, filename='schema.yml', overwrite=False, ignore_warnings=False, no_default=False
):
    """Export current API schema."""
    filename = Path(filename).resolve()
    check_file_existence(filename, overwrite)

    info(f"Exporting schema file to '{filename}'")

    cmd = f'schema --file {filename} --validate --color'

    if not ignore_warnings:
        cmd += ' --fail-on-warn'

    envs = {}
    if not no_default:
        envs['INVENTREE_SITE_URL'] = (
            'http://localhost:8000'  # Default site URL - to ensure server field is stable
        )
        envs['INVENTREE_PLUGINS_ENABLED'] = (
            'False'  # Disable plugins to ensure they are kep out of schema
        )
        envs['INVENTREE_CURRENCY_CODES'] = (
            'AUD,CNY,EUR,USD'  # Default currency codes to ensure they are stable
        )

    manage(c, cmd, pty=True, env=envs)

    assert filename.exists()

    success(f'Schema export completed: {filename}')


@task
def export_settings_definitions(c, filename='inventree_settings.json', overwrite=False):
    """Export settings definition to a JSON file."""
    filename = Path(filename).resolve()
    check_file_existence(filename, overwrite)

    info(f"Exporting settings definition to '{filename}'...")
    manage(c, f'export_settings_definitions {filename}', pty=True)


@task(help={'basedir': 'Export to a base directory (default = False)'})
def export_definitions(c, basedir: str = ''):
    """Export various definitions."""
    if basedir != '' and basedir.endswith('/') is False:
        basedir += '/'
    base_path = Path(basedir, 'generated').resolve()

    filenames = [
        base_path.joinpath('inventree_settings.json'),
        base_path.joinpath('inventree_tags.yml'),
        base_path.joinpath('inventree_filters.yml'),
        base_path.joinpath('inventree_report_context.json'),
    ]

    info('Exporting definitions...')
    export_settings_definitions(c, overwrite=True, filename=filenames[0])

    check_file_existence(filenames[1], overwrite=True)
    manage(c, f'export_tags {filenames[1]}', pty=True)

    check_file_existence(filenames[2], overwrite=True)
    manage(c, f'export_filters {filenames[2]}', pty=True)

    check_file_existence(filenames[3], overwrite=True)
    manage(c, f'export_report_context {filenames[3]}', pty=True)

    info('Exporting definitions complete')


@task(default=True)
def version(c):
    """Show the current version of InvenTree."""
    import src.backend.InvenTree.InvenTree.version as InvenTreeVersion
    from src.backend.InvenTree.InvenTree.config import (
        get_backup_dir,
        get_config_file,
        get_media_dir,
        get_plugin_file,
        get_static_dir,
    )

    # Gather frontend version information
    _, node, yarn = node_available(versions=True)

    invoke_path = Path(invoke.__file__).resolve()

    # Special output messages
    NOT_SPECIFIED = wrap_color('NOT SPECIFIED', '91')
    NA = wrap_color('N/A', '93')

    print(
        f"""
InvenTree - inventree.org
The Open-Source Inventory Management System\n

Python paths:
Executable  {sys.executable}
Environment {sys.prefix}
Invoke Tool {invoke_path}

Installation paths:
Base        {local_dir()}
Config      {get_config_file()}
Plugin File {get_plugin_file() or NOT_SPECIFIED}
Media       {get_media_dir(error=False) or NOT_SPECIFIED}
Static      {get_static_dir(error=False) or NOT_SPECIFIED}
Backup      {get_backup_dir(error=False) or NOT_SPECIFIED}

Versions:
Python      {python_version()}
Django      {InvenTreeVersion.inventreeDjangoVersion()}
InvenTree   {InvenTreeVersion.inventreeVersion()}
API         {InvenTreeVersion.inventreeApiVersion()}
Node        {node if node else NA}
Yarn        {yarn if yarn else NA}

Environment:
Docker      {is_docker_environment()}
RTD         {is_rtd_environment()}

Commit hash: {InvenTreeVersion.inventreeCommitHash()}
Commit date: {InvenTreeVersion.inventreeCommitDate()}"""
    )
    if len(sys.argv) == 1 and sys.argv[0].startswith('/opt/inventree/env/lib/python'):
        print(
            """
You are probably running the package installer / single-line installer. Please mention this in any bug reports!

Use '--list' for a list of available commands
Use '--help' for help on a specific command"""
        )


@task()
def frontend_check(c):
    """Check if frontend is available."""
    print(node_available())


@task
@state_logger('TASK06')
def frontend_compile(c):
    """Generate react frontend.

    Args:
        c: Context variable
    """
    info('Compiling frontend code...')
    frontend_install(c)
    frontend_trans(c, extract=False)
    frontend_build(c)
    success('Frontend compilation complete')


@task
def frontend_install(c):
    """Install frontend requirements.

    Args:
        c: Context variable
    """
    info('Installing frontend dependencies')
    yarn(c, 'yarn install')


@task(help={'extract': 'Extract translations (changes sourcecode), default: True'})
def frontend_trans(c, extract: bool = True):
    """Compile frontend translations.

    Args:
        c: Context variable
        extract (bool): Whether to extract translations from source code. Defaults to True.
    """
    info('Compiling frontend translations')
    if extract:
        yarn(c, 'yarn run extract')
    yarn(c, 'yarn run compile')


@task
def frontend_build(c):
    """Build frontend.

    Args:
        c: Context variable
    """
    info('Building frontend')
    yarn(c, 'yarn run build')


@task
def frontend_server(c):
    """Start frontend development server.

    Args:
        c: Context variable
    """
    info('Starting frontend development server')
    yarn(c, 'yarn run compile')
    yarn(c, 'yarn run dev --host')


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
@state_logger('TASK07')
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

    info('Downloading frontend...')

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

        dest_path = manage_py_dir().joinpath('web', 'static', 'web')

        # if clean, delete static/web directory
        if clean:
            shutil.rmtree(dest_path, ignore_errors=True)
            dest_path.mkdir()
            info(f'Cleaned directory: {dest_path}')

        # unzip build to static folder
        with ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(dest_path)

        info(f'Unzipped downloaded frontend build to: {dest_path}')

    def handle_download(url):
        # download frontend-build.zip to temporary file
        with (
            requests.get(
                url, headers=default_headers, stream=True, allow_redirects=True
            ) as response,
            NamedTemporaryFile(suffix='.zip') as dst,
        ):
            response.raise_for_status()

            # auto decode the gzipped raw data
            response.raw.read = functools.partial(
                response.raw.read, decode_content=True
            )
            with open(dst.name, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            info(f'Downloaded frontend build to temporary file: {dst.name}')

            handle_extract(dst.name)

    def check_already_current(tag=None, sha=None):
        """Check if the currently available frontend is already the requested one."""
        ref = 'tag' if tag else 'commit'

        if tag:
            current = manage_py_dir().joinpath(
                'web', 'static', 'web', '.vite', 'tag.txt'
            )
        elif sha:
            current = manage_py_dir().joinpath(
                'web', 'static', 'web', '.vite', 'sha.txt'
            )
        else:
            raise ValueError('Either tag or sha needs to be set')

        if not current.exists():
            warning(
                f'Current frontend information for {ref} is not available in {current!s} - this is expected in some cases'
            )
            return False

        current_content = current.read_text().strip()
        ref_value = tag or sha
        if current_content == ref_value:
            info(f'Frontend {ref} is already `{ref_value}`')
            return True
        else:
            info(
                f'Frontend {ref} is not expected `{ref_value}` but `{current_content}` - new version will be downloaded'
            )
            return False

    # if zip file is specified, try to extract it directly
    if file:
        handle_extract(file)
        return

    # check arguments
    if ref is not None and tag is not None:
        error('ERROR: Do not set ref and tag.')
        return

    if ref is None and tag is None:
        try:
            ref = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], encoding='utf-8'
            ).strip()
        except Exception:
            # .deb Packages contain extra information in the VERSION file
            version_file = local_dir().joinpath('VERSION')
            if not version_file.exists():
                return
            from dotenv import dotenv_values

            content = dotenv_values(version_file)
            if (
                'INVENTREE_PKG_INSTALLER' in content
                and content['INVENTREE_PKG_INSTALLER'] == 'PKG'
            ):
                ref = content.get('INVENTREE_COMMIT_SHA')
                info(
                    f'[INFO] Running in package environment, got commit "{ref}" from VERSION file'
                )
            else:
                error("ERROR: Cannot get current ref via 'git rev-parse HEAD'")
                return

    if ref is None and tag is None:
        error('ERROR: Either ref or tag needs to be set.')

    if tag:
        tag = tag.lstrip('v')
        try:
            if check_already_current(tag=tag):
                return
            handle_download(
                f'https://github.com/{repo}/releases/download/{tag}/frontend-build.zip'
            )
        except Exception as e:
            if not isinstance(e, requests.HTTPError):
                raise e
            error(
                f"""ERROR: An Error occurred. Unable to download frontend build, release or build does not exist,
try downloading the frontend-build.zip yourself via: https://github.com/{repo}/releases
Then try continuing by running: invoke frontend-download --file <path-to-downloaded-zip-file>"""
            )

        return

    if ref:
        if check_already_current(sha=ref):
            return
        # get workflow run from all workflow runs on that particular ref
        workflow_runs = requests.get(
            f'https://api.github.com/repos/{repo}/actions/runs?head_sha={ref}',
            headers=default_headers,
        ).json()

        if not (qc_run := find_resource(workflow_runs['workflow_runs'], 'name', 'QC')):
            error(f'ERROR: Cannot find any workflow runs for current SHA {ref}')
            return

        info(
            f'Found workflow {qc_run["name"]} (run {qc_run["run_number"]}-{qc_run["run_attempt"]})'
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
            error('[ERROR] Cannot find frontend-build.zip attachment for current sha')
            return

        info(
            f'Found artifact {frontend_artifact["name"]} with id {frontend_artifact["id"]} ({frontend_artifact["size_in_bytes"] / 1e6:.2f}MB).'
        )

        print(
            f"""
GitHub doesn't allow artifact downloads from anonymous users. Either download the following file
via your signed in browser, or consider using a point release download via invoke frontend-download --tag <git-tag>

    Download: https://github.com/{repo}/suites/{qc_run['check_suite_id']}/artifacts/{frontend_artifact['id']} manually and
    continue by running: invoke frontend-download --file <path-to-downloaded-zip-file>"""
        )


def doc_schema(c):
    """Generate schema documentation for the API."""
    schema(
        c, ignore_warnings=True, overwrite=True, filename='docs/generated/schema.yml'
    )
    run(c, 'python docs/extract_schema.py docs/generated/schema.yml')


@task(
    help={
        'address': 'Host and port to run the server on (default: localhost:8080)',
        'compile_schema': 'Compile the schema documentation first (default: False)',
    }
)
def docs_server(c, address='localhost:8080', compile_schema=False):
    """Start a local mkdocs server to view the documentation."""
    # Extract settings definitions
    export_definitions(c, basedir='docs')

    if compile_schema:
        doc_schema(c)

    run(c, f'mkdocs serve -a {address} -f docs/mkdocs.yml')


@task(
    help={'mkdocs': 'Build the documentation using mkdocs at the end (default: False)'}
)
def build_docs(c, mkdocs=False):
    """Build the required documents for building the docs. Optionally build the documentation using mkdocs."""
    migrate(c)
    export_definitions(c, basedir='docs')
    doc_schema(c)

    if mkdocs:
        run(c, 'mkdocs build  -f docs/mkdocs.yml')
        info('Documentation build complete')
    else:
        info('Documentation build complete, but mkdocs not requested')


@task
def clear_generated(c):
    """Clear generated files from `invoke update`."""
    # pyc/pyo files
    run(c, 'find src -name "*.pyc" -exec rm -f {} +')
    run(c, 'find src -name "*.pyo" -exec rm -f {} +')

    # cache folders
    run(c, 'find src -name "__pycache__" -exec rm -rf {} +')

    # Generated translations
    run(c, 'find src -name "django.mo" -exec rm -f {} +')
    run(c, 'find src -name "messages.mo" -exec rm -f {} +')


# endregion tasks

# Collection sorting
development = Collection(
    delete_data,
    docs_server,
    frontend_server,
    gunicorn,
    import_fixtures,
    schema,
    server,
    setup_dev,
    setup_test,
    test,
    test_translations,
    translate,
)

internal = Collection(
    clean_settings,
    clear_generated,
    export_settings_definitions,
    export_definitions,
    frontend_build,
    frontend_check,
    frontend_compile,
    frontend_install,
    frontend_trans,
    rebuild_models,
    rebuild_thumbnails,
    showmigrations,
)

ns = Collection(
    backup,
    export_records,
    frontend_download,
    import_records,
    install,
    migrate,
    plugins,
    remove_mfa,
    restore,
    static,
    superuser,
    update,
    version,
    wait,
    worker,
    build_docs,
)

ns.add_collection(development, 'dev')
ns.add_collection(internal, 'int')
