"""Helpers for plugin app"""
import os
import subprocess
import pathlib
import sysconfig
import traceback

from django.conf import settings


# region logging / errors
def log_plugin_error(error, reference: str = 'general'):
    from plugin import plugin_reg

    # make sure the registry is set up
    if reference not in plugin_reg.errors:
        plugin_reg.errors[reference] = []

    # add error to stack
    plugin_reg.errors[reference].append(error)


class IntegrationPluginError(Exception):
    def __init__(self, path, message):
        self.path = path
        self.message = message
    
    def __str__(self):
        return self.message


def get_plugin_error(error, do_raise: bool = False, do_log: bool = False, log_name: str = ''):
    package_path = traceback.extract_tb(error.__traceback__)[-1].filename
    install_path = sysconfig.get_paths()["purelib"]
    try:
        package_name = pathlib.Path(package_path).relative_to(install_path).parts[0]
    except ValueError:
        package_name = pathlib.Path(package_path).relative_to(settings.BASE_DIR)

    if do_log:
        log_kwargs = {}
        if log_name:
            log_kwargs['reference'] = log_name
        log_plugin_error({package_name: str(error)}, **log_kwargs)

    if do_raise:
        raise IntegrationPluginError(package_name, str(error))

    return package_name, str(error)
# endregion


# region git-helpers
def get_git_log(path):
    """get dict with info of the last commit to file named in path"""
    path = path.replace(os.path.dirname(settings.BASE_DIR), '')[1:]
    command = ['git', 'log', '-n', '1', "--pretty=format:'%H%n%aN%n%aE%n%aI%n%f%n%G?%n%GK'", '--follow', '--', path]
    try:
        output = str(subprocess.check_output(command, cwd=os.path.dirname(settings.BASE_DIR)), 'utf-8')[1:-1]
        if output:
            output = output.split('\n')
        else:
            output = 7 * ['']
    except subprocess.CalledProcessError:
        output = 7 * ['']
    return {'hash': output[0], 'author': output[1], 'mail': output[2], 'date': output[3], 'message': output[4], 'verified': output[5], 'key': output[6]}


class GitStatus:
    """class for resolving git gpg singing state"""
    class Definition:
        """definition of a git gpg sing state"""
        key: str = 'N'
        status: int = 2
        msg: str = ''

        def __init__(self, key: str = 'N', status: int = 2, msg: str = '') -> None:
            self.key = key
            self.status = status
            self.msg = msg

    N = Definition(key='N', status=2, msg='no signature',)
    G = Definition(key='G', status=0, msg='valid signature',)
    B = Definition(key='B', status=2, msg='bad signature',)
    U = Definition(key='U', status=1, msg='good signature, unknown validity',)
    X = Definition(key='X', status=1, msg='good signature, expired',)
    Y = Definition(key='Y', status=1, msg='good signature, expired key',)
    R = Definition(key='R', status=2, msg='good signature, revoked key',)
    E = Definition(key='E', status=1, msg='cannot be checked',)
# endregion
