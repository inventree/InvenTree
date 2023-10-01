"""Install a plugin into the python virtual environment"""

import logging
import os
import re
import subprocess
import sys

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('inventree')


def pip_command(*args):
    """Build and run a pip command using using the current python executable

    returns: subprocess.check_output
    throws: subprocess.CalledProcessError
    """

    python = sys.executable

    command = [python, '-m', 'pip']
    command.extend(args)

    logger.info("running pip command: %s", ' '.join(command))
    logger.debug("python executable path: %s", python)

    return subprocess.check_output(
        command,
        cwd=settings.BASE_DIR.parent,
        stderr=subprocess.STDOUT,
    )


def check_package_path(packagename):
    """Determine the install path of a particular package

    - If installed, return the installation path
    - If not installed, return False
    """

    logger.info("check_package_path: %s", packagename)

    try:
        result = pip_command('show', packagename)

        output = result.decode('utf-8').split("\n")

        for line in output:
            # Check if line matches pattern "Location: ..."
            match = re.match(r'^Location:\s+(.+)$', line.strip())

            if match:
                return match.group(1)

    except subprocess.CalledProcessError as error:

        output = error.output.decode('utf-8')
        logger.exception("Plugin lookup failed: %s", str(output))
        return False

    # If we get here, the package is not installed
    return False


def install_plugins_file():
    """Install plugins from the plugins file"""

    logger.info("Installing plugins from plugins file")

    pf = settings.PLUGIN_FILE

    if not os.path.exists(pf):
        logger.warning("Plugin file %s does not exist", str(pf))
        return

    pf = os.path.abspath(pf)

    try:
        pip_command('install', '-U', '-r', pf)
    except subprocess.CalledProcessError as error:
        output = error.output.decode('utf-8')
        logger.exception("Plugin file installation failed: %s", str(output))
        return False
    except Exception as exc:
        logger.exception("Plugin file installation failed: %s", exc)
        return False

    # At this point, the plugins file has been installed
    return True


def add_plugin_to_file(install_name):
    """Add a plugin to the plugins file"""

    logger.info("Adding plugin to plugins file: %s", install_name)

    pf = settings.PLUGIN_FILE

    if not os.path.exists(pf):
        logger.warning("Plugin file %s does not exist", str(pf))
        return

    pf = os.path.abspath(pf)

    # First, read in existing plugin file
    try:
        with open(pf, 'r') as f:
            lines = f.readlines()
    except Exception as exc:
        logger.exception("Failed to read plugins file: %s", str(exc))
        return

    # Check if plugin is already in file
    for line in lines:
        if line.strip() == install_name:
            logger.info("Plugin already exists in file")
            return

    # Append plugin to file
    lines.append(f'{install_name}')

    # Write file back to disk
    try:
        with open(pf, 'w') as f:
            for line in lines:
                f.write(line)

                if not line.endswith('\n'):
                    f.write('\n')
    except Exception as exc:
        logger.exception("Failed to add plugin to plugins file: %s", str(exc))


def install_plugin(url, packagename=None, user=None):
    """Install a plugin into the python virtual environment:

    - A staff user account is required
    - We must detect that we are running within a virtual environment
    """

    if user and not user.is_staff:
        raise ValidationError(_("Permission denied: only staff users can install plugins"))

    logger.info("install_plugin: %s, %s", url, packagename)

    # Check if we are running in a virtual environment
    # For now, just log a warning
    in_venv = sys.prefix != sys.base_prefix

    if not in_venv:
        logger.warning("InvenTree is not running in a virtual environment")

    # build up the command
    install_name = ['-U']

    if url:
        # use custom registration / VCS
        if True in [identifier in url for identifier in ['git+https', 'hg+https', 'svn+svn', ]]:
            # using a VCS provider
            if packagename:
                install_name.append(f'{packagename}@{url}')
            else:
                install_name.append(url)
        else:  # pragma: no cover
            # using a custom package repositories
            # This is only for pypa compliant directory services (all current are tested above)
            # and not covered by tests.
            install_name.append('-i')
            install_name.append(url)
            install_name.append(packagename)

    elif packagename:
        # use pypi
        install_name.append(packagename)

    ret = {}

    # Execute installation via pip
    try:
        result = pip_command('install', *install_name)

        ret['result'] = _("Installed plugin successfully")
        ret['output'] = str(result, 'utf-8')

        if path := check_package_path(packagename):
            # Override result information
            ret['result'] = _(f"Installed plugin into {path}")

    except subprocess.CalledProcessError as error:
        # If an error was thrown, we need to parse the output

        output = error.output.decode('utf-8')
        logger.exception("Plugin installation failed: %s", str(output))

        errors = []

        for msg in output.split("\n"):
            msg = msg.strip()

            if msg:
                errors.append(msg)

        if len(errors) > 1:
            raise ValidationError(errors)
        else:
            raise ValidationError(errors[0])

    # Save plugin to plugins file
    add_plugin_to_file(' '.join(install_name))

    # Reload the plugin registry, to discover the new plugin
    from plugin.registry import registry

    registry.reload_plugins(full_reload=True, force_reload=True)

    return ret


def uninstall_plugin(plugin_name):
    """Uninstall a plugin from the python virtual environment.

    Note: This is intended to be implemented in a future version

    - Run pip uninstall (only if plugin is installed in venv)
    - Revese any migrations for plugins which implement the app mixin
    - Raise error if located in "plugins" or external plugin dir
    """
    ...
