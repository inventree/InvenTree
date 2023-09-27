"""Install a plugin into the python virtual environment"""

import subprocess
import sys

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def install_plugin(url, packagename=None, user=None):
    """Install a plugin into the python virtual environment:

    - A staff user account is required
    - We must detect that we are running within a virtual environment
    """

    print("install_plugin:", url, packagename)

    if user and not user.is_staff:
        raise ValidationError(_("Permission denied: only staff users can install plugins"))

    # Check if we are running in a virtual environment
    in_venv = sys.prefix != sys.base_prefix

    if not in_venv:
        raise ValidationError(_("Cannot install plugin: not running in a virtual environment"))

    # Determine python executable
    python = sys.executable

    # Check that we are running in a virtual environment
    print("executable:", python)
    print("sys.prefix:", sys.prefix)
    print("sys.base_prefix:", sys.base_prefix)

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

    command = [python, '-m', 'pip', 'install']
    command.extend(install_name)

    ret = {
        'command': ' '.join(command),
    }

    success = False

    print("cmd:", command)
    print("cwd:", settings.BASE_DIR.parent)

    # Execute installation via pip
    try:
        result = subprocess.check_output(
            command,
            cwd=settings.BASE_DIR.parent,
            stderr=subprocess.STDOUT,
        )

        print("Result:", result)

        ret['result'] = str(result, 'utf-8')
        ret['success'] = success = True
    except subprocess.CalledProcessError as error:
        # If an error was thrown, we need to parse the output

        output = error.output.decode('utf-8')

        errors = []

        for msg in output.split("\n"):
            msg = msg.strip()

            if msg:
                errors.append(msg)

        if len(errors) > 1:
            raise ValidationError(errors)
        else:
            raise ValidationError(errors[0])

    if success:
        # TODO: save plugin to plugins file
        ...

    print("success:", success)

    # Check for migrations
    # TODO: offload_task

    return ret
