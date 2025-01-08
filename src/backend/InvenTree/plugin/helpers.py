"""Helpers for plugin app."""

import inspect
import os
import pathlib
import pkgutil
import sys
import sysconfig
import traceback
from importlib.metadata import entry_points
from importlib.util import module_from_spec

from django import template
from django.conf import settings
from django.core.exceptions import AppRegistryNotReady
from django.db.utils import IntegrityError

import structlog

logger = structlog.get_logger('inventree')


# region logging / errors
class IntegrationPluginError(Exception):
    """Error that encapsulates another error and adds the path / reference of the raising plugin."""

    def __init__(self, path, message):
        """Init a plugin error.

        Args:
            path: Path on which the error occurred - used to find out which plugin it was
            message: The original error message
        """
        self.path = path
        self.message = message

    def __str__(self):
        """Returns the error message."""
        return self.message  # pragma: no cover


class MixinImplementationError(ValueError):
    """Error if mixin was implemented wrong in plugin.

    Mostly raised if constant is missing
    """


class MixinNotImplementedError(NotImplementedError):
    """Error if necessary mixin function was not overwritten."""


def log_error(error, reference: str = 'general'):
    """Log an plugin error."""
    from plugin import registry

    # make sure the registry is set up
    if reference not in registry.errors:
        registry.errors[reference] = []

    # add error to stack
    registry.errors[reference].append(error)


def handle_error(error, do_raise: bool = True, do_log: bool = True, log_name: str = ''):
    """Handles an error and casts it as an IntegrationPluginError."""
    package_path = traceback.extract_tb(error.__traceback__)[-1].filename
    install_path = sysconfig.get_paths()['purelib']

    try:
        package_name = pathlib.Path(package_path).relative_to(install_path).parts[0]
    except ValueError:
        # is file - loaded -> form a name for that
        try:
            path_obj = pathlib.Path(package_path).relative_to(settings.BASE_DIR)
            path_parts = [*path_obj.parts]
            path_parts[-1] = path_parts[-1].replace(
                path_obj.suffix, ''
            )  # remove suffix

            # remove path prefixes
            if path_parts[0] == 'plugin':
                path_parts.remove('plugin')
                path_parts.pop(0)
            else:
                path_parts.remove('plugins')  # pragma: no cover

            package_name = '.'.join(path_parts)
        except Exception:
            package_name = package_path

    if do_log:
        log_kwargs = {}
        if log_name:
            log_kwargs['reference'] = log_name
        log_error({package_name: str(error)}, **log_kwargs)

    if do_raise:
        # do a straight raise if we are playing with environment variables at execution time, ignore the broken sample
        if (
            settings.TESTING_ENV
            and package_name != 'integration.broken_sample'
            and isinstance(error, IntegrityError)
        ):
            raise error  # pragma: no cover

        raise IntegrationPluginError(package_name, str(error))


def get_entrypoints():
    """Returns list for entrypoints for InvenTree plugins."""
    # on python before 3.12, we need to use importlib_metadata
    if sys.version_info < (3, 12):
        return entry_points().get('inventree_plugins', [])
    return entry_points(group='inventree_plugins')


# endregion


# region git-helpers
def get_git_log(path):
    """Get dict with info of the last commit to file named in path."""
    import datetime

    from dulwich.errors import NotGitRepository
    from dulwich.repo import Repo

    from InvenTree.ready import isInTestMode

    output = None
    path = os.path.abspath(path)

    if os.path.exists(path) and os.path.isfile(path):
        path = os.path.dirname(path)

    # only do this if we are not in test mode
    if not isInTestMode():  # pragma: no cover
        try:
            repo = Repo(path)
            head = repo.head()
            commit = repo[head]

            output = [
                head.decode(),
                commit.author.decode().split('<')[0][:-1],
                commit.author.decode().split('<')[1][:-1],
                datetime.datetime.fromtimestamp(commit.author_time).isoformat(),
                commit.message.decode().split('\n')[0],
            ]
        except KeyError:
            logger.debug('No HEAD tag found in git repo at path %s', path)
        except NotGitRepository:
            pass

    if not output:
        output = 5 * ['']  # pragma: no cover

    return {
        'hash': output[0],
        'author': output[1],
        'mail': output[2],
        'date': output[3],
        'message': output[4],
    }


# endregion


# region plugin finders
def get_modules(pkg, path=None):
    """Get all modules in a package."""
    context = {}

    if path is None:
        path = pkg.__path__
    elif type(path) is not list:
        path = [path]

    packages = pkgutil.walk_packages(path)

    while True:
        try:
            finder, name, _ = next(packages)
        except StopIteration:
            break
        except Exception as error:
            log_error({pkg.__name__: str(error)}, 'discovery')
            continue

        try:
            if sys.version_info < (3, 12):
                module = finder.find_module(name).load_module(name)
            else:
                spec = finder.find_spec(name)
                module = module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
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


def get_classes(module) -> list:
    """Get all classes in a given module."""
    try:
        return inspect.getmembers(module, inspect.isclass)
    except Exception:
        log_error({module.__name__: 'Could not get classes'}, 'discovery')
        return []


def get_plugins(pkg, baseclass, path=None):
    """Return a list of all modules under a given package.

    - Modules must be a subclass of the provided 'baseclass'
    - Modules must have a non-empty NAME parameter
    """
    plugins = []

    modules = get_modules(pkg, path=path)

    # Iterate through each module in the package
    for mod in modules:
        # Iterate through each class in the module
        for item in get_classes(mod):
            plugin = item[1]
            if issubclass(plugin, baseclass) and plugin.NAME:
                plugins.append(plugin)

    return plugins


# endregion


# region templates
def render_template(plugin, template_file, context=None):
    """Locate and render a template file, available in the global template context."""
    try:
        tmp = template.loader.get_template(template_file)
    except template.TemplateDoesNotExist:
        logger.exception(
            "Plugin %s could not locate template '%s'", plugin.slug, template_file
        )

        return f"""
        <div class='alert alert-block alert-danger'>
        Template file <em>{template_file}</em> does not exist.
        </div>
        """

    # Render with the provided context
    html = tmp.render(context)

    return html


def render_text(text, context=None):
    """Locate a raw string with provided context."""
    ctx = template.Context(context)

    return template.Template(text).render(ctx)


# endregion
