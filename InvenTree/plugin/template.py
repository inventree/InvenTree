"""Load templates for loaded plugins."""

from django.template.loaders.filesystem import Loader as FilesystemLoader

from plugin import registry


class PluginTemplateLoader(FilesystemLoader):
    """A custom template loader which allows loading of templates from installed plugins.

    Each plugin can register templates simply by providing a 'templates' directory in its root path.

    The convention is that each 'templates' directory contains a subdirectory with the same name as the plugin,
    e.g. templates/myplugin/my_template.html

    In this case, the template can then be loaded (from any plugin!) by loading "myplugin/my_template.html".

    The separate plugin-named directories help keep the templates separated and uniquely identifiable.
    """

    def get_dirs(self):
        """Returns all template dir paths in plugins."""
        dirname = 'templates'
        template_dirs = []

        for plugin in registry.plugins.values():
            new_path = plugin.path().joinpath(dirname)
            if new_path.is_dir():
                template_dirs.append(new_path)

        return tuple(template_dirs)
