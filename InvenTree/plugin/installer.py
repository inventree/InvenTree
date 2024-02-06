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


def update_plugins_file(install_name, remove=False):
    """Add a plugin to the plugins file."""
    logger.info('Adding plugin to plugins file: %s', install_name)

    pf = settings.PLUGIN_FILE

    if not pf or not pf.exists():
        logger.warning('Plugin file %s does not exist', str(pf))
        return

    def compare_line(line: str):
        """Check if a line in the file matches the installname."""
        return line.strip().split('==')[0] == install_name.split('==')[0]

    # First, read in existing plugin file
    try:
        with pf.open(mode='r') as f:
            lines = f.readlines()
    except Exception as exc:
        logger.exception('Failed to read plugins file: %s', str(exc))
        return

    # Reconstruct output file
    output = []

    found = False

    # Check if plugin is already in file
    for line in lines:
        # Ignore processing for any commented lines
        if line.strip().startswith('#'):
            output.append(line)
            continue

        if compare_line(line):
            found = True
            if not remove:
                # Replace line with new install name
                output.append(install_name)
        else:
            output.append(line)

    # Append plugin to file
    if not found and not remove:
        output.append(install_name)

    # Write file back to disk
    try:
        with pf.open(mode='w') as f:
            for line in output:
                f.write(line)

                if not line.endswith('\n'):
                    f.write('\n')
    except Exception as exc:
        logger.exception('Failed to add plugin to plugins file: %s', str(exc))


def install_plugin(url=None, packagename=None, user=None, version=None):
    """Install a plugin into the python virtual environment.

    Args:
        packagename: Optional package name to install
        url: Optional URL to install from
        user: Optional user performing the installation
        version: Optional version specifier
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

        if version:
            full_pkg = f'{full_pkg}=={version}'

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
    update_plugins_file(full_pkg)

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


def uninstall_plugin(cfg: plugin.models.PluginConfig, user=None, delete_config=True):
    """Uninstall a plugin from the python virtual environment.

    - The plugin must not be active
    - The plugin must be a "package" and have a valid package name

    Args:
        cfg: PluginConfig object
        user: User performing the uninstall
        delete_config: If True, delete the plugin configuration from the database
    """
    from plugin.registry import registry

    if cfg.active:
        raise ValidationError(
            _('Plugin cannot be uninstalled as it is currently active')
        )

    validate_package_plugin(cfg, user)
    package_name = cfg.package_name
    logger.info('Uninstalling plugin: %s', package_name)

    cmd = ['uninstall', '-y', package_name]

    try:
        result = pip_command(*cmd)

        ret = {
            'result': _('Uninstalled plugin successfully'),
            'success': True,
            'output': str(result, 'utf-8'),
        }

    except subprocess.CalledProcessError as error:
        handle_pip_error(error, 'plugin_uninstall')

    # Update the plugins file
    update_plugins_file(package_name, remove=True)

    if delete_config:
        # Remove the plugin configuration from the database
        cfg.delete()

    # Reload the plugin registry
    registry.reload_plugins(full_reload=True, force_reload=True, collect=True)

    return ret
