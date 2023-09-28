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

    logger.info(f"running pip command: {' '.join(command)}")

    # Debug information, might be useful for working out edge cases
    logger.debug(f"base prefix: {sys.base_prefix}")
    logger.debug(f"python path: {sys.path}")

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

    logger.info(f"check_package_path: {packagename}")

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
        logger.error(f"Plugin lookup failed: {output}")
        return False

    # If we get here, the package is not installed
    return False


def install_plugins_file():
    """Install plugins from the plugins file"""

    logger.info("Installing plugins from plugins file")

    pf = settings.PLUGIN_FILE

    if not os.path.exists(pf):
        logger.warning(f"Plugin file {pf} does not exist")
        return

    pf = os.path.abspath(pf)

    try:
        pip_command('install', '-U', '-r', pf)
    except subprocess.CalledProcessError as error:
        output = error.output.decode('utf-8')
        logger.error(f"Plugin file installation failed: {output}")
        return False
    except Exception as exc:
        logger.error(f"Plugin file installation failed: {str(exc)}")
        return False

    # At this point, the plugins file has been installed
    return True


def add_plugin_to_file(install_name):
    """Add a plugin to the plugins file"""

    logger.info(f"Adding plugin to plugins file: {install_name}")

    pf = settings.PLUGIN_FILE

    if not os.path.exists(pf):
        logger.warning(f"Plugin file {pf} does not exist")
        return

    pf = os.path.abspath(pf)

    # First, read in existing plugin file
    try:
        with open(pf, 'r') as f:
            lines = f.readlines()
    except Exception as exc:
        logger.error(f"Failed to read plugins file: {str(exc)}")
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
        logger.error(f"Failed to add plugin to plugins file: {str(exc)}")


def install_plugin(url, packagename=None, user=None):
    """Install a plugin into the python virtual environment:

    - A staff user account is required
    - We must detect that we are running within a virtual environment
    """

    if user and not user.is_staff:
        raise ValidationError(_("Permission denied: only staff users can install plugins"))

    logger.info(f"install_plugin: {url}, {packagename}")

    # Check if we are running in a virtual environment
    # For now, just log a warning
    in_venv = sys.prefix != sys.base_prefix

    if not in_venv:
        logger.warning("InvenTree is not running in a virtual environment")

    # build up the command
    install_name = []

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
        logger.error(f"Plugin installation failed: {output}")

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

    # TODO: run migrations for this plugin

    # Check for migrations
    # TODO: offload_task

    return ret
