"""Tasks for automating certain actions and interacting with InvenTree from the CLI."""

import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from functools import wraps
from pathlib import Path
from platform import python_version
from typing import Optional

import invoke
from invoke import Collection, task
from invoke.exceptions import UnexpectedExit


def safe_value(fnc):
    """Helper function to safely get value from function, catching import exceptions."""
    try:
        return fnc()
    except (ModuleNotFoundError, ImportError):
        return wrap_color('N/A', '93')  # Yellow color for "Not Available"


def is_true(x):
    """Shortcut function to determine if a value "looks" like a boolean."""
    return str(x).strip().lower() in ['1', 'y', 'yes', 't', 'true', 'on']


def is_devcontainer_environment():
    """Check if the InvenTree environment is running in a development container."""
    return is_true(os.environ.get('INVENTREE_DEVCONTAINER', 'False'))


def is_docker_environment():
    """Check if the InvenTree environment is running in a Docker container."""
    return is_true(os.environ.get('INVENTREE_DOCKER', 'False'))


def is_rtd_environment():
    """Check if the InvenTree environment is running on ReadTheDocs."""
    return is_true(os.environ.get('READTHEDOCS', 'False'))


def is_debug_environment():
    """Check if the InvenTree environment is running in a debug environment."""
    return is_true(os.environ.get('INVENTREE_DEBUG', 'False')) or is_true(
        os.environ.get('RUNNER_DEBUG', 'False')
    )


def get_django_version():
    """Return the current Django version."""
    from src.backend.InvenTree.InvenTree.version import (
        inventreeDjangoVersion,  # type: ignore[import]
    )

    return safe_value(inventreeDjangoVersion)


def get_inventree_version():
    """Return the current InvenTree version."""
    from src.backend.InvenTree.InvenTree.version import (
        inventreeVersion,  # type: ignore[import]
    )

    return safe_value(inventreeVersion)


def get_inventree_api_version():
    """Return the current InvenTree API version."""
    from src.backend.InvenTree.InvenTree.version import (
        inventreeApiVersion,  # type: ignore[import]
    )

    return safe_value(inventreeApiVersion)


def get_commit_hash():
    """Return the current git commit hash."""
    from src.backend.InvenTree.InvenTree.version import (
        inventreeCommitHash,  # type: ignore[import]
    )

    return safe_value(inventreeCommitHash)


def get_commit_date():
    """Return the current git commit date."""
    from src.backend.InvenTree.InvenTree.version import (
        inventreeCommitDate,  # type: ignore[import]
    )

    return safe_value(inventreeCommitDate)


def get_version_vals():
    """Get values from the VERSION file."""
    version_file = local_dir().joinpath('VERSION')
    if not version_file.exists():
        return {}
    try:
        from dotenv import dotenv_values

        return dotenv_values(version_file)
    except ImportError:
        error(
            'ERROR: dotenv package not installed. You might not be running in the right environment.'
        )
        return {}


def is_pkg_installer(content: Optional[dict] = None, load_content: bool = False):
    """Check if the current environment is a package installer by VERSION/environment."""
    if load_content:
        content = get_version_vals()
    return get_installer(content) == 'PKG'


def is_pkg_installer_by_path():
    """Check if the current environment is a package installer by checking the path."""
    return len(sys.argv) >= 1 and sys.argv[0].startswith(
        '/opt/inventree/env/bin/invoke'
    )


def get_installer(content: Optional[dict] = None):
    """Get the installer for the current environment or a content dict."""
    if content is None:
        content = dict(os.environ)
    return content.get('INVENTREE_PKG_INSTALLER')


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
        func.method_name = method_name or func.__name__

        @wraps(func)
        def wrapped(c, *args, **kwargs):
            do_log = is_debug_environment()
            if do_log:
                info(f'# task | {func.method_name} | start')

            t1 = time.time()
            try:
                func(c, *args, **kwargs)
            except KeyboardInterrupt:
                error('INVE-W15: Process interrupted by user.')
                sys.exit(1)
            except UnexpectedExit:
                error(f"Task '{func.method_name}' failed with an error.")
                raise
            t2 = time.time()

            if do_log:
                info(f'# task | {func.method_name} | done | elapsed: {t2 - t1:.2f}s')

        return wrapped

    if fn and callable(fn):
        return decorator(fn)
    elif fn and isinstance(fn, str):
        method_name = fn
    return decorator


# endregion


# region environment checks
def envcheck_invoke_version():
    """Check that the installed invoke version meets minimum requirements."""
    MIN_INVOKE_VERSION: str = '2.0.0'

    min_version = tuple(map(int, MIN_INVOKE_VERSION.split('.')))
    invoke_version = tuple(map(int, invoke.__version__.split('.')))  # noqa: RUF048

    if invoke_version < min_version:
        error(f'The installed invoke version ({invoke.__version__}) is not supported!')
        error(f'InvenTree requires invoke version {MIN_INVOKE_VERSION} or above')
        sys.exit(1)


def envcheck_invoke_path():
    """Check that the path of the used invoke is correct."""
    if is_docker_environment() or is_rtd_environment():
        return

    invoke_path: Path = Path(invoke.__file__)
    env_path: Path = Path(sys.prefix).resolve()
    loc_path: Path = Path(__file__).parent.resolve()
    if not invoke_path.is_relative_to(loc_path) and not invoke_path.is_relative_to(
        env_path
    ):
        error('INVE-E2 - Wrong Invoke Path')
        error(
            f'The invoke tool `{invoke_path}` is not correctly located, ensure you are using the invoke installed in an environment in `{loc_path}` or `{env_path}`'
        )
        sys.exit(1)


def envcheck_python_version():
    """Check that the installed python version meets minimum requirements.

    If the python version is not sufficient, exits with a non-zero exit code.
    """
    REQ_MAJOR: int = 3
    REQ_MINOR: int = 9

    version = sys.version.split(' ')[0]

    valid: bool = True

    if sys.version_info.major < REQ_MAJOR or (
        sys.version_info.major == REQ_MAJOR and sys.version_info.minor < REQ_MINOR
    ):
        valid = False

    if not valid:
        error(f'The installed python version ({version}) is not supported!')
        error(f'InvenTree requires Python {REQ_MAJOR}.{REQ_MINOR} or above')
        sys.exit(1)


def envcheck_invoke_cmd():
    """Checks if the rights invoke command for the current environment is used."""
    first_cmd = sys.argv[0].replace(sys.prefix, '')
    intendded = ['/bin/invoke', '/bin/inv']

    correct_cmd: Optional[str] = None
    if is_rtd_environment() or is_docker_environment() or is_devcontainer_environment():
        return  # Skip invoke command check for Docker/RTD/DevContainer environments
    elif is_pkg_installer(load_content=True) and not is_pkg_installer_by_path():
        correct_cmd = 'inventree run invoke'
    else:
        warning('Unknown environment, not checking used invoke command')

    if first_cmd not in intendded:
        correct_cmd = correct_cmd if correct_cmd else 'invoke'
        error('INVE-W9 - Wrong Invoke Environment')
        error(
            f'The detected invoke command `{first_cmd}` is not the intended one for this environment, ensure you are using one of the following command(s) `{correct_cmd}`'
        )


def main():
    """Main function to check the execution environment."""
    envcheck_invoke_version()
    envcheck_python_version()
    envcheck_invoke_path()
    envcheck_invoke_cmd()


# endregion


def builtin_apps():
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
    allow_email: bool = False,
    allow_plugins: bool = True,
    allow_session: bool = True,
    allow_sso: bool = True,
    allow_tokens: bool = True,
):
    """Returns a list of content types to exclude from import / export.

    Arguments:
        allow_auth (bool): Allow user authentication data to be exported / imported
        allow_email (bool): Allow email log data to be exported / imported
        allow_plugins (bool): Allow plugin information to be exported / imported
        allow_session (bool): Allow user session data to be exported / imported
        allow_sso (bool): Allow SSO tokens to be exported / imported
        allow_tokens (bool): Allow tokens to be exported / imported
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
        'common.newsfeedentry',
        'common.notificationentry',
        'common.notificationmessage',
        'importer.dataimportsession',
        'importer.dataimportcolumnmap',
        'importer.dataimportrow',
    ]

    # Optional exclude email message logs
    if not allow_email:
        excludes.extend(['common.emailmessage', 'common.emailthread'])

    # Optionally exclude user auth data
    if not allow_auth:
        excludes.extend(['auth.group', 'auth.user', 'users.userprofile'])

    # Optionally exclude user token information
    if not allow_tokens:
        excludes.extend(['users.apitoken'])

    # Optionally exclude plugin information
    if not allow_plugins:
        excludes.extend([
            'plugin.pluginconfig',
            'plugin.pluginsetting',
            'plugin.pluginusersetting',
        ])

    # Optionally exclude SSO application information
    if not allow_sso:
        excludes.extend(['socialaccount.socialapp', 'socialaccount.socialtoken'])

    # Optionally exclude user session information
    if not allow_session:
        excludes.extend(['sessions.session', 'usersessions.usersession'])

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


def _frontend_info():
    """Return the path of the frontend info directory."""
    return manage_py_dir().joinpath('web', 'static', 'web', '.vite')


def version_target_pth():
    """Return the path of the target version file."""
    return _frontend_info().joinpath('tag.txt')


def version_sha_pth():
    """Return the path of the SHA version file."""
    return _frontend_info().joinpath('sha.txt')


def version_source_pth():
    """Return the path of the source version file."""
    return _frontend_info().joinpath('source.txt')


# endregion

if __name__ in ['__main__', 'tasks']:
    main()


def run(
    c, cmd, path: Optional[Path] = None, pty: bool = False, hide: bool = False, env=None
):
    """Runs a given command a given path.

    Args:
        c: Command line context.
        cmd: Command to run.
        path: Path to run the command in.
        pty (bool, optional): Run an interactive session. Defaults to False.
        hide (bool, optional): Hide the command output. Defaults to False.
        env (dict, optional): Environment variables to pass to the command. Defaults to None.
    """
    env = env or {}
    path = path or local_dir()

    try:
        result = c.run(f'cd "{path}" && {cmd}', pty=pty, env=env, hide=hide)
    except UnexpectedExit as e:
        error(f"ERROR: InvenTree command failed: '{cmd}'")
        warning('- Refer to the error messages in the log above for more information')
        raise e

    return result


def manage(c, cmd, pty: bool = False, env=None, verbose: bool = False, **kwargs):
    """Runs a given command against django's "manage.py" script.

    Args:
        c: Command line context.
        cmd: Django command to run.
        pty (bool, optional): Run an interactive session. Defaults to False.
        env (dict, optional): Environment variables to pass to the command. Defaults to None.
        verbose (bool, optional): Print verbose output from the command. Defaults to False.
    """
    if verbose:
        info(f'Running command: python3 manage.py {cmd}')
        cmd += ' -v 1'
    else:
        cmd += ' -v 0'

    return run(
        c, f'python3 manage.py {cmd}', manage_py_dir(), pty=pty, env=env, **kwargs
    )


def installed_apps(c) -> list[str]:
    """Returns a list of all installed apps, including plugins."""
    result = manage(c, 'list_apps', pty=False, hide=True)
    output = result.stdout.strip()

    # Look for the expected pattern
    match = re.findall(r'>>> (.*) <<<', output)

    if not match:
        raise ValueError(f"Unexpected output from 'list_apps' command: {output}")

    return match[0].split(',')


def run_install(
    c,
    uv: bool,
    install_file: Path,
    run_preflight=True,
    version_check=False,
    pinned=True,
    verbose: bool = False,
):
    """Run the installation of python packages from a requirements file.

    Arguments:
        c: Command line context.
        uv: Whether to use UV (experimental package manager) instead of pip.
        install_file: Path to the requirements file to install from.
        run_preflight: Whether to run the preflight installation step (installing pip/uv itself). Default is True.
        version_check: Whether to check for a version-specific requirements file. Default is False.
        pinned: Whether to use the --require-hashes option when installing packages. Default is True.
        verbose: Whether to print verbose output from pip install commands. Default is False.
    """
    if version_check:
        # Test if there is a version specific requirements file
        sys_ver_s = python_version().split('.')
        sys_string = f'{sys_ver_s[0]}.{sys_ver_s[1]}'
        install_file_vers = install_file.parent.joinpath(
            f'{install_file.stem}-{sys_string}{install_file.suffix}'
        )
        if install_file_vers.exists():
            install_file = install_file_vers
            info(f"Using version-specific requirements file '{install_file_vers}'")

    info(f"Installing required python packages from '{install_file}'")
    if not Path(install_file).is_file():
        raise FileNotFoundError(f"Requirements file '{install_file}' not found")

    # Install required Python packages with PIP
    if not uv:
        # Optionally run preflight first
        if run_preflight:
            run(
                c,
                f'pip3 install --no-cache-dir --disable-pip-version-check -U pip setuptools {"" if verbose else "--quiet"}',
            )
            info('Installed package manager')

        run(
            c,
            f'pip3 install --no-cache-dir --disable-pip-version-check -U {"--require-hashes" if pinned else ""} -r {install_file} {"" if verbose else "--quiet"}',
        )
    else:
        if run_preflight:
            run(
                c,
                f'pip3 install --no-cache-dir --disable-pip-version-check -U uv setuptools {"" if verbose else "--quiet"}',
            )
            info('Installed package manager')
        run(
            c,
            f'uv pip install -U {"--require-hashes" if pinned else ""} -r {install_file} {"" if verbose else "--quiet"}',
        )


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


@task(help={'verbose': 'Print verbose output from the command'})
@state_logger
def wait(c, verbose: bool = False):
    """Wait until the database connection is ready."""
    return manage(c, 'wait_for_db', verbose=verbose)


# Install tasks
# region tasks
@task(
    help={
        'uv': 'Use UV (experimental package manager)',
        'verbose': 'Print verbose output from installation commands',
    }
)
@state_logger
def plugins(c, uv: bool = False, verbose: bool = False):
    """Installs all plugins as specified in 'plugins.txt'."""
    from src.backend.InvenTree.InvenTree.config import (  # type: ignore[import]
        get_plugin_file,
    )

    run_install(
        c, uv, get_plugin_file(), run_preflight=False, pinned=False, verbose=verbose
    )

    # Collect plugin static files
    manage(c, 'collectplugins', verbose=verbose)


@task(
    help={
        'uv': 'Use UV package manager (experimental)',
        'skip_plugins': 'Skip plugin installation',
        'dev': 'Install development requirements instead of production requirements',
        'verbose': 'Print verbose output from pip install commands',
    }
)
@state_logger
def install(
    c,
    uv: bool = False,
    skip_plugins: bool = False,
    dev: bool = False,
    verbose: bool = False,
):
    """Install required python packages for InvenTree.

    Arguments:
        c: Command line context.
        uv: Use UV package manager (experimental) instead of pip. Default is False.
        skip_plugins: Skip plugin installation. Default is False.
        dev: Install development requirements instead of production requirements. Default is False.
        verbose: Print verbose output from pip install commands. Default is False.
    """
    info('Installing required python packages...')

    if dev:
        run_install(
            c,
            uv,
            local_dir().joinpath('src/backend/requirements-dev.txt'),
            version_check=True,
            verbose=verbose,
        )
        success('Dependency installation complete')
        return

    # Ensure path is relative to *this* directory
    run_install(
        c,
        uv,
        local_dir().joinpath('src/backend/requirements.txt'),
        version_check=True,
        verbose=verbose,
    )

    # Run plugins install
    if not skip_plugins:
        plugins(c, uv=uv, verbose=verbose)

    # Compile license information
    lic_path = manage_py_dir().joinpath('InvenTree', 'licenses.txt')
    run(
        c,
        f'pip-licenses --format=json --with-license-file --no-license-path > {lic_path}',
    )

    success('Dependency installation complete')


@task(
    help={
        'tests': 'Set up test dataset at the end',
        'verbose': 'Print verbose output from commands',
    }
)
def setup_dev(c, tests: bool = False, verbose: bool = False):
    """Sets up everything needed for the dev environment."""
    # Install required Python packages with PIP
    install(c, uv=False, skip_plugins=True, dev=True, verbose=verbose)

    # Install pre-commit hook
    info('Installing pre-commit for checks before git commits...')
    run(c, 'pre-commit install')
    run(c, 'pre-commit autoupdate')
    success('pre-commit set up complete')

    # Set up test-data if flag is set
    if tests:
        setup_test(c, verbose=verbose)


# Setup / maintenance tasks


@task
def shell(c):
    """Launch a Django shell."""
    manage(c, 'shell', pty=True)


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
    from src.backend.InvenTree.InvenTree.config import (  # type: ignore[import]
        get_media_dir,
    )

    info(f'Rebuilding image thumbnails in {get_media_dir()}')
    manage(c, 'rebuild_thumbnails', pty=True)


@task
@state_logger
def clean_settings(c):
    """Clean the setting tables of old settings."""
    info('Cleaning old settings from the database...')
    manage(c, 'clean_settings')
    success('Settings cleaned successfully')


@task(
    help={
        'mail': "mail of the user who's MFA should be disabled",
        'username': "username of the user who's MFA should be disabled",
    }
)
def remove_mfa(c, mail='', username=''):
    """Remove MFA for a user."""
    if not mail and not username:
        warning('You must provide a users mail or username')
        return

    manage(c, f'remove_mfa --mail {mail} --username {username}')


@task(
    help={
        'frontend': 'Build the frontend',
        'clear': 'Remove existing static files',
        'skip_plugins': 'Ignore collection of plugin static files',
    }
)
@state_logger
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
        frontend_compile(c, extract=True)

    # Update static files
    if not ignore_static:
        static(c)

    success('Translation files built successfully')


@task(help={'verbose': 'Print verbose output'})
@state_logger('backend_trans')
def backend_trans(c, verbose: bool = False):
    """Compile backend Django translation files."""
    info('Compiling backend translations...')
    manage(c, 'compilemessages', verbose=verbose)
    success('Backend translations compiled successfully')


@task(
    help={
        'clean': 'Clean up old backup files',
        'compress': 'Compress the backup files',
        'encrypt': 'Encrypt the backup files (requires GPG recipient to be set)',
        'path': 'Specify path for generated backup files (leave blank for default path)',
        'quiet': 'Suppress informational output (only show errors)',
        'skip_db': 'Skip database backup step (only backup media files)',
        'skip_media': 'Skip media backup step (only backup database files)',
    }
)
@state_logger
def backup(
    c,
    clean: bool = False,
    compress: bool = True,
    encrypt: bool = False,
    path=None,
    quiet: bool = False,
    skip_db: bool = False,
    skip_media: bool = False,
):
    """Backup the database and media files."""
    cmd = '--noinput -v 2'

    if compress:
        cmd += ' --compress'

    if encrypt:
        cmd += ' --encrypt'

    # A path to the backup dir can be specified here
    # If not specified, the default backup dir is used
    if path:
        path = Path(path)
        if not os.path.isabs(path):
            path = local_dir().joinpath(path).resolve()

        cmd += f' -O {path}'

    if clean:
        cmd += ' --clean'

    if quiet:
        cmd += ' --quiet'

    if skip_db:
        info('Skipping database backup...')
    else:
        info('Backing up InvenTree database...')
        manage(c, f'dbbackup {cmd}')

    if skip_media:
        info('Skipping media backup...')
    else:
        info('Backing up InvenTree media files...')
        manage(c, f'mediabackup {cmd}')

    if not skip_db or not skip_media:
        success('Backup completed successfully')


@task(
    help={
        'path': 'Specify path to locate backup files (leave blank for default path)',
        'db_file': 'Specify filename of compressed database archive (leave blank to use most recent backup)',
        'decrypt': 'Decrypt the backup files (requires GPG recipient to be set)',
        'media_file': 'Specify filename of compressed media archive (leave blank to use most recent backup)',
        'skip_db': 'Do not import database archive (media restore only)',
        'skip_media': 'Do not import media archive (database restore only)',
        'uncompress': 'Uncompress the backup files before restoring (default behavior)',
        'restore_allow_newer_version': 'Allow restore from a newer version backup (use with caution)',
    }
)
def restore(
    c,
    path=None,
    db_file=None,
    media_file=None,
    decrypt: bool = False,
    skip_db: bool = False,
    skip_media: bool = False,
    uncompress: bool = True,
    restore_allow_newer_version: bool = False,
):
    """Restore the database and media files."""
    base_cmd = '--noinput -v 2'

    env = {}

    if restore_allow_newer_version:
        env['INVENTREE_BACKUP_RESTORE_ALLOW_NEWER_VERSION'] = 'True'

    if uncompress:
        base_cmd += ' --uncompress'

    if decrypt:
        base_cmd += ' --decrypt'

    if path:
        # Resolve the provided path
        path = Path(path)
        if not os.path.isabs(path):
            path = local_dir().joinpath(path).resolve()

        base_cmd += f' -I {path}'

    if skip_db:
        info('Skipping database archive...')
    else:
        info('Restoring InvenTree database')
        cmd = f'dbrestore {base_cmd}'

        if db_file:
            cmd += f' -i {db_file}'

        manage(c, cmd, env=env)

    if skip_media:
        info('Skipping media restore...')
    else:
        info('Restoring InvenTree media files')
        cmd = f'mediarestore {base_cmd}'

        if media_file:
            cmd += f' -i {media_file}'

        manage(c, cmd, env=env)


@task()
@state_logger
def listbackups(c):
    """List available backup files."""
    info('Finding available backup files...')
    manage(c, 'listbackups')


@task(
    pre=[wait],
    post=[rebuild_models, rebuild_thumbnails],
    help={
        'verbose': 'Print verbose output from migration commands',
        'detect': 'Detect and create new migrations based on changes to models',
    },
)
@state_logger
def migrate(c, detect: bool = True, verbose: bool = False):
    """Performs database migrations.

    This is a critical step if the database schema have been altered!
    """
    info('Running InvenTree database migrations...')

    if detect:
        manage(c, 'makemigrations', verbose=verbose)

    manage(c, 'runmigrations', pty=True, verbose=verbose)
    manage(c, 'migrate --run-syncdb', verbose=verbose)
    manage(
        c,
        'remove_stale_contenttypes --include-stale-apps --no-input',
        pty=True,
        verbose=verbose,
    )

    success('InvenTree database migrations completed')


@task(help={'app': 'Specify an app to show migrations for (leave blank for all apps)'})
def showmigrations(c, app=''):
    """Show the migration status of the database."""
    manage(c, f'showmigrations {app}', pty=True)


@task(
    post=[clean_settings],
    help={
        'skip_backup': 'Skip database backup step (advanced users)',
        'backend': 'Force backend translation compilation step (ignores INVENTREE_DOCKER)',
        'no_backend': 'Skip backend translation compilation step',
        'frontend': 'Force frontend compilation/download step (ignores INVENTREE_DOCKER)',
        'no_frontend': 'Skip frontend compilation/download step',
        'skip_static': 'Skip static file collection step',
        'uv': 'Use UV (experimental package manager)',
        'verbose': 'Print verbose output from installation commands',
    },
)
@state_logger
def update(
    c,
    skip_backup: bool = False,
    backend: bool = False,
    no_backend: bool = False,
    frontend: bool = False,
    no_frontend: bool = False,
    skip_static: bool = False,
    uv: bool = False,
    verbose: bool = False,
):
    """Update InvenTree installation.

    This command should be invoked after source code has been updated,
    e.g. downloading new code from GitHub.

    The following tasks are performed, in order:

    - install
    - backend_trans (optional)
    - backup (optional)
    - migrate
    - frontend_compile or frontend_download (optional)
    - static (optional)
    - clean_settings
    """
    info('Updating InvenTree installation...')

    # Ensure required components are installed
    install(c, uv=uv, verbose=verbose)

    # Skip backend translation compilation on docker, unless explicitly requested.
    # Users can also forcefully disable the step via `--no-backend`.
    if (is_docker_environment() and not backend) or no_backend:
        if no_backend:
            info('Skipping backend translation compilation (no_backend flag set)')
        else:
            info('Skipping backend translation compilation (INVENTREE_DOCKER flag set)')
    else:
        backend_trans(c, verbose=verbose)

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

    success('InvenTree update complete')


# Data tasks
@task(
    help={
        'filename': "Output filename (default = 'data.json')",
        'overwrite': 'Overwrite existing files without asking first (default = False)',
        'include_email': 'Include email logs in the output file (default = False)',
        'include_permissions': 'Include user and group permissions in the output file (default = False)',
        'include_tokens': 'Include API tokens in the output file (default = False)',
        'exclude_plugins': 'Exclude plugin data from the output file (default = False)',
        'include_sso': 'Include SSO token data in the output file (default = False)',
        'include_session': 'Include user session data in the output file (default = False)',
        'verbose': 'Print verbose output from management commands',
    }
)
def export_records(
    c,
    filename='data.json',
    overwrite: bool = False,
    include_email: bool = False,
    include_permissions: bool = False,
    include_tokens: bool = False,
    exclude_plugins: bool = False,
    include_sso: bool = False,
    include_session: bool = False,
    verbose: bool = False,
):
    """Export all database records to a file."""
    # Get an absolute path to the file
    target = Path(filename)
    if not target.is_absolute():
        target = local_dir().joinpath(filename).resolve()

    info(f"Exporting database records to file '{target}'")

    wait(c, verbose=verbose)

    check_file_existence(target, overwrite)

    excludes = content_excludes(
        allow_email=include_email,
        allow_tokens=include_tokens,
        allow_plugins=not exclude_plugins,
        allow_session=include_session,
        allow_sso=include_sso,
    )

    with tempfile.NamedTemporaryFile(
        suffix='.json', encoding='utf-8', mode='w+t', delete=True
    ) as tmpfile:
        cmd = f"dumpdata --natural-foreign --indent 2 --output '{tmpfile.name}' {excludes}"

        # Dump data to temporary file
        manage(c, cmd, pty=True, verbose=verbose)
        info('Running data post-processing step...')

        # Post-process the file, to remove any "permissions" specified for a user or group
        tmpfile.seek(0)
        data = json.loads(tmpfile.read())

    data_out = [
        {
            'metadata': True,
            'comment': 'This file contains a dump of the InvenTree database',
            'exported_at': datetime.datetime.now().isoformat(),
            'exported_at_utc': datetime.datetime.utcnow().isoformat(),
            'source_version': get_inventree_version(),
            'api_version': get_inventree_api_version(),
            'django_version': get_django_version(),
            'python_version': python_version(),
            'source_commit': get_commit_hash(),
            'installed_apps': installed_apps(c),
        }
    ]

    for entry in data:
        model_name = entry.get('model', None)

        # Ignore any temporary settings (start with underscore)
        if model_name in ['common.inventreesetting', 'common.inventreeusersetting']:
            if entry['fields'].get('key', '').startswith('_'):
                continue

        if include_permissions is False:
            if model_name == 'auth.group':
                entry['fields']['permissions'] = []

            if model_name == 'auth.user':
                entry['fields']['user_permissions'] = []

        data_out.append(entry)

    # Write the processed data to file
    with open(target, 'w', encoding='utf-8') as f_out:
        f_out.write(json.dumps(data_out, indent=2))

    success('Data export completed')


def validate_import_metadata(
    c, metadata: dict, strict: bool = False, apps: bool = True, verbose: bool = False
) -> bool:
    """Validate the metadata associated with an import file.

    Arguments:
        c: The context or connection object
        metadata (dict): The metadata to validate
        apps (bool): If True, validate that all apps listed in the metadata are installed in the current environment.
        strict (bool): If True, the import process will fail if any issues are detected.
        verbose (bool): If True, print detailed information during validation.
    """
    if verbose:
        info('Validating import metadata...')

    valid = True

    def metadata_issue(message: str):
        """Handle an issue with the metadata."""
        nonlocal valid
        valid = False

        if strict:
            error(f'INVE-E16 Data Import Error: {message}')
            sys.exit(1)
        else:
            warning(f'INVE-W13 Data Import Warning: {message}')

    if not metadata:
        metadata_issue(
            'No metadata found in the import file - cannot validate source version'
        )
        return False

    source_version = metadata.get('source_version')

    if source_version != get_inventree_version():
        metadata_issue(
            f"Source version '{source_version}' does not match the current InvenTree version '{get_inventree_version()}' - this may lead to issues with the import process"
        )

    if apps:
        local_apps = set(installed_apps(c))
        source_apps = set(metadata.get('installed_apps', []))

        for app in source_apps:
            if app not in local_apps:
                metadata_issue(
                    f"Source app '{app}' is not installed in the current environment - this may break the import process"
                )

    if verbose and valid:
        success('Metadata validation succeeded - no issues detected')

    return valid


@task(
    help={
        'filename': 'Input filename',
        'clear': 'Clear existing data before import',
        'strict': 'Strict mode - fail if any issues are detected with the metadata (default = False)',
        'ignore_nonexistent': 'Ignore non-existent database models (default = False)',
        'exclude_plugins': 'Exclude plugin data from the import process (default = False)',
        'skip_migrations': 'Skip the migration step after clearing data (default = False)',
        'verbose': 'Print verbose output from management commands',
    },
    pre=[wait],
    post=[rebuild_models, rebuild_thumbnails],
)
def import_records(
    c,
    filename='data.json',
    clear: bool = False,
    strict: bool = False,
    exclude_plugins: bool = False,
    ignore_nonexistent: bool = False,
    skip_migrations: bool = False,
    verbose: bool = False,
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
        delete_data(c, force=True, migrate=True, verbose=verbose)

    if not skip_migrations:
        migrate(c, verbose=verbose)

    info(f"Importing database records from '{target}'")

    with open(target, encoding='utf-8') as f_in:
        try:
            data = json.loads(f_in.read())
        except json.JSONDecodeError as exc:
            error(f'ERROR: Failed to decode JSON file: {exc}')
            sys.exit(1)

    # Separate out the data into different categories, to ensure they are loaded in the correct order
    auth_data = []
    common_data = []
    plugin_data = []
    all_data = []

    # A dict containing metadata associated with the data file
    metadata = {}

    def load_data(
        title: str,
        data: list[dict],
        app: Optional[str] = None,
        excludes: Optional[list[str]] = None,
    ) -> tempfile.NamedTemporaryFile:
        """Helper function to save data to a temporary file, and then load into the database."""
        nonlocal ignore_nonexistent
        nonlocal verbose
        nonlocal c

        # Skip if there is no data to load
        if len(data) == 0:
            return

        info(f'Loading {len(data)} {title} records...')

        with tempfile.NamedTemporaryFile(
            suffix='.json', mode='w', encoding='utf-8', delete=False
        ) as f_out:
            f_out.write(json.dumps(data, indent=2))

        cmd = f'loaddata {f_out.name} -v 0 --force-color'

        if app:
            cmd += f' --app {app}'

        if ignore_nonexistent:
            cmd += ' --ignorenonexistent'

        # A set of content types to exclude from the import process
        if excludes:
            cmd += f' -i {excludes}'

        manage(c, cmd, pty=True, verbose=verbose)

    # Iterate through each entry in the provided data file, and separate out into different categories based on the model type
    for entry in data:
        # Metadata needs to be extracted first
        if entry.get('metadata', False):
            metadata = entry
            continue

        if model := entry.get('model', None):
            # Clear out any permissions specified for a group
            if model == 'auth.group':
                entry['fields']['permissions'] = []

            # Clear out any permissions specified for a user
            if model == 'auth.user':
                entry['fields']['user_permissions'] = []

            # Handle certain model types separately, to ensure they are loaded in the correct order
            if model.startswith('auth.'):
                auth_data.append(entry)
            if model.startswith('users.'):
                auth_data.append(entry)
            elif model.startswith('common.'):
                common_data.append(entry)
            elif model.startswith('plugin.'):
                plugin_data.append(entry)
            else:
                all_data.append(entry)
        else:
            error(
                f'{"ERROR" if strict else "WARNING"}: Invalid entry in data file - missing "model" key'
            )
            print(entry)
            if strict:
                sys.exit(1)

    # Check the metadata associated with the imported data
    # Do not validate the 'apps' list yet - as the plugins have not yet been loaded
    validate_import_metadata(c, metadata, strict=strict, apps=False)

    # Load the temporary files in order
    load_data('auth', auth_data)
    load_data('common', common_data, app='common')

    if not exclude_plugins:
        load_data('plugins', plugin_data, app='plugin')

        if len(plugin_data) > 0 and not skip_migrations:
            # Now that the plugins have been loaded, run database migrations again to ensure any new plugins have their database schema up to date
            migrate(c)

    # Run validation again - ensure that the plugin apps have been loaded correctly
    validate_import_metadata(c, metadata, strict=strict, apps=True)

    load_data('remaining', all_data, excludes=content_excludes(allow_auth=False))

    success('Data import completed')


@task(
    help={
        'force': 'Force deletion of all data without confirmation',
        'migrate': 'Run migrations before deleting data (default = False)',
        'verbose': 'Print verbose output from management commands',
    }
)
def delete_data(c, force: bool = False, migrate: bool = False, verbose: bool = False):
    """Delete all database records!

    Warning: This will REALLY delete all records in the database!!
    """
    info('Deleting existing data from InvenTree database...')

    if migrate:
        manage(c, 'migrate --run-syncdb', verbose=verbose)

    manage(c, f'flush{" --noinput" if force else ""}', verbose=verbose)

    success('Existing data deleted')


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
        'address': 'Server address:port (default=0.0.0.0:8000)',
        'no_reload': 'Do not automatically reload the server in response to code changes',
        'no_threading': 'Disable multi-threading for the development server',
    },
)
def server(c, address='0.0.0.0:8000', no_reload=False, no_threading=False):
    """Launch a (development) server using Django's in-built webserver.

    - This is *not* sufficient for a production installation.
    - The default address exposes the server on all network interfaces.
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
    new_file_path = Path(str(file_path) + '_new')

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
        'check': 'Run sanity check on the django install (default = False)',
        'disable_pty': 'Disable PTY',
        'runtest': 'Specify which tests to run, in format <module>.<file>.<class>.<method>',
        'migrations': 'Run migration unit tests',
        'report': 'Display a report of slow tests',
        'coverage': 'Run code coverage analysis (requires coverage package)',
        'translations': 'Compile translations before running tests',
        'keepdb': 'Keep the test database after running tests (default = False)',
        'pytest': 'Use pytest to run tests',
        'verbosity': 'Verbosity level for test output (default = 1)',
    }
)
def test(
    c,
    check: bool = False,
    disable_pty: bool = False,
    runtest: str = '',
    migrations: bool = False,
    report: bool = False,
    coverage: bool = False,
    translations: bool = False,
    keepdb: bool = False,
    pytest: bool = False,
    verbosity: int = 1,
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
    if check:
        manage(c, 'check')

    if translations:
        try:
            manage(c, 'compilemessages', pty=True)
        except Exception:
            warning('Failed to compile translations')

    pty = not disable_pty

    tested_apps = ' '.join(builtin_apps())

    cmd = 'test'

    if runtest:
        # Specific tests to run
        cmd += f' {runtest}'
    else:
        # Run all tests
        cmd += f' {tested_apps}'

    if report:
        cmd += ' --slowreport'

    if keepdb:
        cmd += ' --keepdb'

    if migrations:
        cmd += ' --tag migration_test'
    else:
        cmd += ' --exclude-tag migration_test'

    cmd += ' --exclude-tag performance_test'

    cmd += f' --verbosity {verbosity}'

    if coverage:
        # Run tests within coverage environment, and generate report
        run(c, f'coverage run {manage_py_path()} {cmd}')
        run(c, 'coverage xml -i')
    elif pytest:
        # Use pytest to run the tests
        migrate(c)
        run(c, f'pytest {manage_py_path().parent.parent} --codspeed')
    else:
        # Run simple test runner, without coverage
        manage(c, cmd, pty=pty)


@task(
    help={
        'dev': 'Set up development environment at the end',
        'validate_files': 'Validate media files are correctly copied',
        'use_ssh': 'Use SSH protocol for cloning the demo dataset (requires SSH key)',
        'branch': 'Specify branch of demo-dataset to clone (default = main)',
        'verbose': 'Print verbose output from management commands',
    }
)
def setup_test(
    c,
    ignore_update=False,
    dev=False,
    validate_files=False,
    use_ssh=False,
    verbose=False,
    path='inventree-demo-dataset',
    branch='main',
):
    """Setup a testing environment."""
    from src.backend.InvenTree.InvenTree.config import (  # type: ignore[import]
        get_media_dir,
    )

    if not ignore_update:
        update(c, verbose=verbose)

    template_dir = local_dir().joinpath(path)

    # Remove old data directory
    if template_dir.exists():
        run(c, f'rm {template_dir} -r')

    URL = 'https://github.com/inventree/demo-dataset'

    if use_ssh:
        # Use SSH protocol for cloning the demo dataset
        URL = 'git@github.com:inventree/demo-dataset.git'

    # Get test data
    info('Cloning demo dataset ...')
    run(c, f'git clone {URL} {template_dir} -b {branch} -v --depth=1')

    # Make sure migrations are done - might have just deleted sqlite database
    if not ignore_update:
        migrate(c, verbose=verbose)

    # Load data
    info('Loading database records ...')
    import_records(
        c,
        filename=template_dir.joinpath('inventree_data.json'),
        clear=True,
        verbose=verbose,
    )

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
        setup_dev(c, verbose=verbose)


@task(
    help={
        'filename': "Output filename (default = 'schema.yml')",
        'overwrite': 'Overwrite existing files without asking first (default = off/False)',
        'no_default': 'Do not use default settings for schema (default = off/False)',
    }
)
@state_logger
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
            'AUD,CAD,CNY,EUR,GBP,JPY,NZD,USD'  # Default currency codes to ensure they are stable
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
    from src.backend.InvenTree.InvenTree.config import (  # type: ignore[import]
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

    platform = NOT_SPECIFIED

    if is_pkg_installer():
        platform = 'Package Installer'
    elif is_docker_environment():
        platform = 'Docker'
    elif is_devcontainer_environment():
        platform = 'Devcontainer'
    elif is_rtd_environment():
        platform = 'ReadTheDocs'

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
Config      {safe_value(get_config_file)}
Plugin File {safe_value(get_plugin_file) or NOT_SPECIFIED}
Media       {safe_value(lambda: get_media_dir(error=False)) or NOT_SPECIFIED}
Static      {safe_value(lambda: get_static_dir(error=False)) or NOT_SPECIFIED}
Backup      {safe_value(lambda: get_backup_dir(error=False)) or NOT_SPECIFIED}

Versions:
InvenTree   {get_inventree_version() or NOT_SPECIFIED}
API         {get_inventree_api_version() or NOT_SPECIFIED}
Python      {python_version()}
Django      {get_django_version() or NOT_SPECIFIED}
Node        {node if node else NA}
Yarn        {yarn if yarn else NA}

Environment:
Platform    {platform}
Debug       {is_debug_environment()}

Commit hash: {get_commit_hash() or NOT_SPECIFIED}
Commit date: {get_commit_date() or NOT_SPECIFIED}"""
    )
    if is_pkg_installer_by_path():
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


@task(help={'extract': 'Extract translation strings. Default: False'})
@state_logger
def frontend_compile(c, extract: bool = False):
    """Generate react frontend.

    Arguments:
        c: Context variable
        extract (bool): Whether to extract translations from source code. Defaults to False.
    """
    info('Compiling frontend code...')
    frontend_install(c)
    frontend_trans(c, extract=extract)
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
    info('Building frontend...')
    yarn(c, 'yarn run build')

    def write_info(path: Path, content: str):
        """Helper function to write version content to file after cleaning it if it exists."""
        if path.exists():
            path.unlink()
        path.write_text(content, encoding='utf-8')

    # Write version marker
    try:
        import src.backend.InvenTree.InvenTree.version as InvenTreeVersion  # type: ignore[import]

        if version_hash := InvenTreeVersion.inventreeCommitHash():
            write_info(version_sha_pth(), version_hash)
        elif version_tag := InvenTreeVersion.inventreeVersion():
            write_info(version_target_pth(), version_tag)
        else:
            warning('No version information available to write frontend version marker')

        # Write source marker
        write_info(
            version_source_pth(),
            f'local build on {datetime.datetime.now().isoformat()}',
        )
    except Exception:
        warning('Failed to write frontend version marker')

    success('Frontend build complete')


@task
def frontend_server(c):
    """Start frontend development server.

    Args:
        c: Context variable
    """
    info('Starting frontend development server')
    yarn(c, 'yarn run compile')
    yarn(c, 'yarn run dev --host')


@task
def frontend_test(c, host: str = '0.0.0.0'):
    """Start the playwright test runner for the frontend code."""
    info('Starting frontend test runner')

    frontend_path = local_dir().joinpath('src', 'frontend').resolve()

    cmd = 'npx playwright test --ui'

    if host:
        cmd += f' --ui-host={host}'

    run(c, cmd, path=frontend_path)


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
@state_logger
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
            dest_path.mkdir(parents=True, exist_ok=True)
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
            current = version_target_pth()
        elif sha:
            current = version_sha_pth()
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
        static(c, frontend=False, skip_plugins=True)
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
            content: dict = get_version_vals()
            if is_pkg_installer(content):
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
        'compile_schema': 'Compile the API schema documentation first (default: False)',
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


@task(pre=[wait])
def monitor(c):
    """Monitor the worker performance."""
    manage(c, 'qmonitor', pty=True)


# endregion tasks

# Collection sorting
development = Collection(
    delete_data,
    docs_server,
    frontend_server,
    frontend_test,
    gunicorn,
    import_fixtures,
    schema,
    server,
    setup_dev,
    setup_test,
    shell,
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
    backend_trans,
    backup,
    export_records,
    frontend_download,
    import_records,
    install,
    listbackups,
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
    monitor,
    build_docs,
)

ns.add_collection(development, 'dev')
ns.add_collection(internal, 'int')
