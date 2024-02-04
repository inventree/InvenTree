"""Install a plugin into the python virtual environment."""

import logging
import re
import subprocess
import sys

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import plugin.models
from InvenTree.exceptions import log_error

logger = logging.getLogger('inventree')


def pip_command(*args):
    """Build and run a pip command using using the current python executable.

    returns: subprocess.check_output
    throws: subprocess.CalledProcessError
    """
    python = sys.executable

    command = [python, '-m', 'pip']
    command.extend(args)

    command = [str(x) for x in command]

    logger.info('Running pip command: %s', ' '.join(command))

    return subprocess.check_output(
        command, cwd=settings.BASE_DIR.parent, stderr=subprocess.STDOUT
    )


def handle_pip_error(error, path: str) -> list:
    """Raise a ValidationError when the pip command fails.

    - Log the error to the database
    - Format the output from a pip command into a list of error messages.
    - Raise an appropriate error
    """
    log_error(path)

    output = error.output.decode('utf-8')

    logger.error('Pip command failed: %s', output)

    errors = []

    for line in output.split('\n'):
        line = line.strip()

        if line:
            errors.append(line)

    if len(errors) > 1:
        raise ValidationError(errors)
    else:
        raise ValidationError(errors[0])


def check_package_path(packagename: str):
    """Determine the install path of a particular package.

    - If installed, return the installation path
    - If not installed, return False
    """
    logger.debug('check_package_path: %s', packagename)

    # Remove version information
    for c in '<>=! ':
        packagename = packagename.split(c)[0]

    try:
        result = pip_command('show', packagename)

        output = result.decode('utf-8').split('\n')

        for line in output:
            # Check if line matches pattern "Location: ..."
            match = re.match(r'^Location:\s+(.+)$', line.strip())

            if match:
                return match.group(1)

    except subprocess.CalledProcessError as error:
        log_error('check_package_path')

        output = error.output.decode('utf-8')
        logger.exception('Plugin lookup failed: %s', str(output))
        return False

    # If we get here, the package is not installed
    return False


def install_plugins_file():
    """Install plugins from the plugins file."""
    logger.info('Installing plugins from plugins file')

    pf = settings.PLUGIN_FILE

    if not pf or not pf.exists():
        logger.warning('Plugin file %s does not exist', str(pf))
        return

    try:
        pip_command('install', '-r', str(pf))
    except subprocess.CalledProcessError as error:
        output = error.output.decode('utf-8')
        logger.exception('Plugin file installation failed: %s', str(output))
        log_error('pip')
        return False
    except Exception as exc:
        logger.exception('Plugin file installation failed: %s', exc)
        log_error('pip')
        return False

    # At this point, the plugins file has been installed
    return True


def add_plugin_to_file(install_name):
    """Add a plugin to the plugins file."""
    logger.info('Adding plugin to plugins file: %s', install_name)

    pf = settings.PLUGIN_FILE

    if not pf or not pf.exists():
        logger.warning('Plugin file %s does not exist', str(pf))
        return

    # First, read in existing plugin file
    try:
        with pf.open(mode='r') as f:
            lines = f.readlines()
    except Exception as exc:
        logger.exception('Failed to read plugins file: %s', str(exc))
        return

    # Check if plugin is already in file
    for line in lines:
        if line.strip() == install_name:
            logger.debug('Plugin already exists in file')
            return

    # Append plugin to file
    lines.append(f'{install_name}')

    # Write file back to disk
    try:
        with pf.open(mode='w') as f:
            for line in lines:
                f.write(line)

                if not line.endswith('\n'):
                    f.write('\n')
    except Exception as exc:
        logger.exception('Failed to add plugin to plugins file: %s', str(exc))


def install_plugin(url=None, packagename=None, user=None):
    """Install a plugin into the python virtual environment.

    Rules:
    - A staff user account is required
    - We must detect that we are running within a virtual environment
    """
    if user and not user.is_staff:
        raise ValidationError(_('Only staff users can administer plugins'))

    logger.info('install_plugin: %s, %s', url, packagename)

    # Check if we are running in a virtual environment
    # For now, just log a warning
    in_venv = sys.prefix != sys.base_prefix

    if not in_venv:
        logger.warning('InvenTree is not running in a virtual environment')

    # build up the command
    install_name = ['install', '-U']

    full_pkg = ''

    if url:
        # use custom registration / VCS
        if True in [
            identifier in url for identifier in ['git+https', 'hg+https', 'svn+svn']
        ]:
            # using a VCS provider
            if packagename:
                full_pkg = f'{packagename}@{url}'
            else:
                full_pkg = url
        else:  # pragma: no cover
            # using a custom package repositories
            # This is only for pypa compliant directory services (all current are tested above)
            # and not covered by tests.
            if url:
                install_name.append('-i')
                full_pkg = url
            elif packagename:
                full_pkg = packagename

    elif packagename:
        # use pypi
        full_pkg = packagename

    install_name.append(full_pkg)

    ret = {}

    # Execute installation via pip
    try:
        result = pip_command(*install_name)

        ret['result'] = ret['success'] = _('Installed plugin successfully')
        ret['output'] = str(result, 'utf-8')

        if packagename:
            if path := check_package_path(packagename):
                # Override result information
                ret['result'] = _(f'Installed plugin into {path}')

    except subprocess.CalledProcessError as error:
        handle_pip_error(error, 'plugin_install')

    # Save plugin to plugins file
    add_plugin_to_file(full_pkg)

    # Reload the plugin registry, to discover the new plugin
    from plugin.registry import registry

    registry.reload_plugins(full_reload=True, force_reload=True, collect=True)

    return ret


def validate_package_plugin(cfg: plugin.models.PluginConfig, user=None):
    """Validate a package plugin for update or removal."""
    if not cfg.plugin:
        raise ValidationError(_('Plugin was not found in registry'))

    if not cfg.is_package():
        raise ValidationError(_('Plugin is not a packaged plugin'))

    if not cfg.package_name:
        raise ValidationError(_('Plugin package name not found'))

    if user and not user.is_staff:
        raise ValidationError(_('Only staff users can administer plugins'))


def update_plugin(
    cfg: plugin.models.PluginConfig, user=None, version=None, registry_name=None
):
    """Update the specified plugin (via PIP).

    Args:
        cfg: PluginConfig - the plugin to update
        user: User - the user performing the update
        version: Optional version specifier
        registry_name: Optional name of the external registry to use
    """
    from InvenTree.tasks import check_for_migrations, offload_task
    from plugin.registry import registry

    if not cfg.active:
        raise ValidationError(_('Plugin is not active'))

    validate_package_plugin(cfg, user=user)

    package_name = cfg.package_name

    logger.info('Updating plugin: %s', package_name)

    cmd = ['install']

    if version:
        cmd.append(f'{package_name}=={version}')
    else:
        cmd.extend(['-U', package_name])

    if registry_name:
        cmd.extend(['-i', registry_name])

    try:
        result = pip_command(*cmd)

        ret = {
            'result': _('Updated plugin successfully'),
            'success': True,
            'output': str(result, 'utf-8'),
        }

        if path := check_package_path(package_name):
            ret['result'] = _(f'Updated plugin into {path}')

    except subprocess.CalledProcessError as error:
        handle_pip_error(error, 'plugin_update')

    # Reload the plugin registry, to discover the new plugin
    registry.reload_plugins(full_reload=True, force_reload=True, collect=True)

    # Run a check for database migrations
    offload_task(check_for_migrations)

    return ret
