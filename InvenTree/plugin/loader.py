"""
load templates for loaded plugins
"""
from django.conf import settings

from django.template.loaders.filesystem import Loader as FilesystemLoader
from pathlib import Path

from plugin import plugin_reg


class PluginTemplateLoader(FilesystemLoader):

    def get_dirs(self):
        dirname = 'templates'
        template_dirs = []
        for plugin in plugin_reg.plugins.values():
            new_path = Path(plugin.path) / dirname
            if Path(new_path).is_dir():
                template_dirs.append(new_path)
        return tuple(template_dirs)
