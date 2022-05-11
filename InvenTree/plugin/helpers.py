"""
Helpers for plugin app
"""
import os
import subprocess
import pathlib
import sysconfig
import traceback
import inspect
import pkgutil
import logging

from django import template
from django.conf import settings
from django.core.exceptions import AppRegistryNotReady
from django.db.utils import IntegrityError


logger = logging.getLogger('inventree')


# region logging / errors
class IntegrationPluginError(Exception):
    """
    Error that encapsulates another error and adds the path / reference of the raising plugin
    """
    def __init__(self, path, message):
        self.path = path
        self.message = message

    def __str__(self):
        return self.message  # pragma: no cover


class MixinImplementationError(ValueError):
    """
    Error if mixin was implemented wrong in plugin
    Mostly raised if constant is missing
    """
    pass


class MixinNotImplementedError(NotImplementedError):
    """
    Error if necessary mixin function was not overwritten
    """
    pass


def log_error(error, reference: str = 'general'):
    """
    Log an plugin error
    """
    from plugin import registry

    # make sure the registry is set up
    if reference not in registry.errors:
        registry.errors[reference] = []

    # add error to stack
    registry.errors[reference].append(error)


def handle_error(error, do_raise: bool = True, do_log: bool = True, log_name: str = ''):
    """
    Handles an error and casts it as an IntegrationPluginError
    """
    package_path = traceback.extract_tb(error.__traceback__)[-1].filename
    install_path = sysconfig.get_paths()["purelib"]
    try:
        package_name = pathlib.Path(package_path).relative_to(install_path).parts[0]
    except ValueError:
        # is file - loaded -> form a name for that
        path_obj = pathlib.Path(package_path).relative_to(settings.BASE_DIR)
        path_parts = [*path_obj.parts]
        path_parts[-1] = path_parts[-1].replace(path_obj.suffix, '')  # remove suffix

        # remove path prefixes
        if path_parts[0] == 'plugin':
            path_parts.remove('plugin')
            path_parts.pop(0)
        else:
            path_parts.remove('plugins')  # pragma: no cover

        package_name = '.'.join(path_parts)

    if do_log:
        log_kwargs = {}
        if log_name:
            log_kwargs['reference'] = log_name
        log_error({package_name: str(error)}, **log_kwargs)

    if do_raise:
        # do a straight raise if we are playing with enviroment variables at execution time, ignore the broken sample
        if settings.TESTING_ENV and package_name != 'integration.broken_sample' and isinstance(error, IntegrityError):
            raise error  # pragma: no cover
        raise IntegrationPluginError(package_name, str(error))
# endregion


# region git-helpers
def get_git_log(path):
    """
    Get dict with info of the last commit to file named in path
    """
    from plugin import registry

    output = None
    if registry.git_is_modern:
        path = path.replace(os.path.dirname(settings.BASE_DIR), '')[1:]
        command = ['git', 'log', '-n', '1', "--pretty=format:'%H%n%aN%n%aE%n%aI%n%f%n%G?%n%GK'", '--follow', '--', path]
        try:
            output = str(subprocess.check_output(command, cwd=os.path.dirname(settings.BASE_DIR)), 'utf-8')[1:-1]
            if output:
                output = output.split('\n')
        except subprocess.CalledProcessError:  # pragma: no cover
            pass

    if not output:
        output = 7 * ['']  # pragma: no cover

    return {'hash': output[0], 'author': output[1], 'mail': output[2], 'date': output[3], 'message': output[4], 'verified': output[5], 'key': output[6]}


def check_git_version():
    """returns if the current git version supports modern features"""

    # get version string
    try:
        output = str(subprocess.check_output(['git', '--version'], cwd=os.path.dirname(settings.BASE_DIR)), 'utf-8')
    except subprocess.CalledProcessError:  # pragma: no cover
        return False

    # process version string
    try:
        version = output[12:-1].split(".")
        if len(version) > 1 and version[0] == '2':
            if len(version) > 2 and int(version[1]) >= 22:
                return True
    except ValueError:  # pragma: no cover
        pass

    return False  # pragma: no cover


class GitStatus:
    """
    Class for resolving git gpg singing state
    """
    class Definition:
        """
        Definition of a git gpg sing state
        """
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


# region plugin finders
def get_modules(pkg):
    """get all modules in a package"""

    context = {}
    for loader, name, ispkg in pkgutil.walk_packages(pkg.__path__):
        try:
            module = loader.find_module(name).load_module(name)
            pkg_names = getattr(module, '__all__', None)
            for k, v in vars(module).items():
                if not k.startswith('_') and (pkg_names is None or k in pkg_names):
                    context[k] = v
            context[name] = module
        except AppRegistryNotReady:  # pragma: no cover
            pass
        except Exception as error:
            # this 'protects' against malformed plugin modules by more or less silently failing

            # log to stack
            log_error({name: str(error)}, 'discovery')

    return [v for k, v in context.items()]


def get_classes(module):
    """get all classes in a given module"""
    return inspect.getmembers(module, inspect.isclass)


def get_plugins(pkg, baseclass):
    """
    Return a list of all modules under a given package.

    - Modules must be a subclass of the provided 'baseclass'
    - Modules must have a non-empty PLUGIN_NAME parameter
    """

    plugins = []

    modules = get_modules(pkg)

    # Iterate through each module in the package
    for mod in modules:
        # Iterate through each class in the module
        for item in get_classes(mod):
            plugin = item[1]
            if issubclass(plugin, baseclass) and plugin.PLUGIN_NAME:
                plugins.append(plugin)

    return plugins
# endregion


# region templates
def render_template(plugin, template_file, context=None):
    """
    Locate and render a template file, available in the global template context.
    """

    try:
        tmp = template.loader.get_template(template_file)
    except template.TemplateDoesNotExist:
        logger.error(f"Plugin {plugin.slug} could not locate template '{template_file}'")

        return f"""
        <div class='alert alert-block alert-danger'>
        Template file <em>{template_file}</em> does not exist.
        </div>
        """

    # Render with the provided context
    html = tmp.render(context)

    return html
# endregion
