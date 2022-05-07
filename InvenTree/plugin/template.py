"""
load templates for loaded plugins
"""

import logging
from pathlib import Path

from django import template
from django.template.loaders.filesystem import Loader as FilesystemLoader

from plugin import registry


logger = logging.getLogger('inventree')


class PluginTemplateLoader(FilesystemLoader):
    """
    A custom template loader which allows loading of templates from installed plugins.

    Each plugin can register templates simply by providing a 'templates' directory in its root path.

    The convention is that each 'templates' directory contains a subdirectory with the same name as the plugin,
    e.g. templates/myplugin/my_template.html

    In this case, the template can then be loaded (from any plugin!) by loading "myplugin/my_template.html".

    The separate plugin-named directories help keep the templates separated and uniquely identifiable.
    """

    def get_dirs(self):
        dirname = 'templates'
        template_dirs = []

        for plugin in registry.plugins.values():
            new_path = Path(plugin.path) / dirname
            if Path(new_path).is_dir():
                template_dirs.append(new_path)

        return tuple(template_dirs)


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
